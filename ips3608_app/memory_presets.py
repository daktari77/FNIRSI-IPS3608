from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .models import MemoryPreset


DEFAULT_SLOT_IDS = [f"M{i}" for i in range(1, 7)]


class MemoryRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    _MAX_BACKUPS = 10

    def _backup_path(self, suffix: str = "") -> Path:
        backup_dir = self.file_path.parent / "backup" / "v1"
        backup_dir.mkdir(parents=True, exist_ok=True)
        tag = f"_{suffix}" if suffix else ""
        return backup_dir / f"{self.file_path.stem}{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json"

    def _rotate_backups(self) -> None:
        """Delete oldest backup files, retaining at most _MAX_BACKUPS."""
        backup_dir = self.file_path.parent / "backup" / "v1"
        if not backup_dir.exists():
            return
        stem = self.file_path.stem
        files = sorted(
            (f for f in backup_dir.iterdir() if f.name.startswith(stem) and f.suffix == ".json"),
            key=lambda f: f.stat().st_mtime,
        )
        for old in files[: -self._MAX_BACKUPS]:
            try:
                old.unlink()
            except Exception:
                pass

    def _write_json_atomic(self, payload: object) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_path.replace(self.file_path)

    def load_all(self) -> list[MemoryPreset]:
        presets = [MemoryPreset(slot_id=slot) for slot in DEFAULT_SLOT_IDS]
        if not self.file_path.exists():
            return presets

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[MemoryRepository] Failed to load {self.file_path}: {exc}", file=sys.stderr)
            return presets

        # Migrazione automatica: se è una lista, convertila in oggetto versionato
        if isinstance(raw, list):
            self._backup_path("legacy").write_text(json.dumps(raw, indent=2), encoding="utf-8")
            raw = {"version": 2, "presets": raw}
            self._write_json_atomic(raw)
        if not isinstance(raw, dict):
            return presets

        items = raw.get("presets", [])
        by_slot = {p.slot_id: p for p in presets}
        for item in items:
            slot_id = str(item.get("slot_id", "")).strip().upper()
            if slot_id in by_slot:
                preset = by_slot[slot_id]
                preset.label = str(item.get("label", ""))
                preset.voltage_v = float(item.get("voltage_v", 0.0))
                preset.current_a = float(item.get("current_a", 0.0))
                preset.enabled = bool(item.get("enabled", False))
        return presets

    def save_all(self, presets: list[MemoryPreset]) -> None:
        if self.file_path.exists():
            self._backup_path().write_text(self.file_path.read_text(encoding="utf-8"), encoding="utf-8")
        serializable = {
            "version": 2,
            "presets": [asdict(p) for p in presets]
        }
        self._write_json_atomic(serializable)
        self._rotate_backups()


class MemoryPresetDialog(QDialog):
    """Dialog for editing memory presets M1..M6.

    Signals:
        recall_requested(voltage_v, current_a): emitted when the user clicks "Recall To Output".
            Connect this in the caller to apply the values to the device and the UI spinboxes.
    """

    recall_requested = Signal(float, float)

    def __init__(
        self,
        parent: QWidget,
        presets: list[MemoryPreset],
        current_voltage: float = 0.0,
        current_current: float = 0.0,
    ):
        super().__init__(parent)
        self.setWindowTitle("Memory Presets M1..M6")
        self.resize(860, 480)
        self.presets = presets
        self.selected_slot_id: Optional[str] = None
        self._current_voltage = current_voltage
        self._current_current = current_current

        self.list_widget = QListWidget()
        self.slot_lbl = QLabel("Slot: -")
        self.label_edit = QLineEdit()
        self.voltage_spin = QDoubleSpinBox()
        self.current_spin = QDoubleSpinBox()
        self.status_lbl = QLabel("Select a memory slot")

        self.apply_from_current_btn = QPushButton("Load From Current Output")
        self.recall_btn = QPushButton("Recall To Output")
        self.save_btn = QPushButton("Save Slot")
        self.clear_btn = QPushButton("Clear Slot")
        self.close_btn = QPushButton("Close")

        self._build_ui()
        self._wire_signals()
        self._refresh_list()

    def _build_ui(self) -> None:
        self.voltage_spin.setRange(0.0, 36.0)
        self.voltage_spin.setDecimals(2)
        self.voltage_spin.setSingleStep(0.10)
        self.voltage_spin.setSuffix(" V")

        self.current_spin.setRange(0.0, 8.2)
        self.current_spin.setDecimals(3)
        self.current_spin.setSingleStep(0.010)
        self.current_spin.setSuffix(" A")

        left = QVBoxLayout()
        left.addWidget(QLabel("Slots:"))
        left.addWidget(self.list_widget)
        left.addWidget(self.status_lbl)

        form = QFormLayout()
        form.addRow("Slot:", self.slot_lbl)
        form.addRow("Label:", self.label_edit)
        form.addRow("Voltage:", self.voltage_spin)
        form.addRow("Current:", self.current_spin)

        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(self.apply_from_current_btn)
        right.addWidget(self.recall_btn)
        right.addWidget(self.save_btn)
        right.addWidget(self.clear_btn)
        right.addStretch(1)
        right.addWidget(self.close_btn)

        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addLayout(right, 2)

    def _wire_signals(self) -> None:
        self.list_widget.currentTextChanged.connect(self._load_selected)
        self.apply_from_current_btn.clicked.connect(self._load_from_current)
        self.recall_btn.clicked.connect(self._recall_to_output)
        self.save_btn.clicked.connect(self._save_slot)
        self.clear_btn.clicked.connect(self._clear_slot)
        self.close_btn.clicked.connect(self.accept)

    def _refresh_list(self) -> None:
        current = self.list_widget.currentItem().text() if self.list_widget.currentItem() else ""
        self.list_widget.clear()
        for preset in self.presets:
            self.list_widget.addItem(preset.display_name)
        if current:
            found = self.list_widget.findItems(current, Qt.MatchStartsWith)
            if found:
                self.list_widget.setCurrentItem(found[0])
        if self.list_widget.currentRow() < 0 and self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _selected_preset(self) -> Optional[MemoryPreset]:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        slot_id = item.text().split(" - ", 1)[0].strip().upper()
        for preset in self.presets:
            if preset.slot_id == slot_id:
                return preset
        return None

    def _load_selected(self, _: str) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        self.selected_slot_id = preset.slot_id
        self.slot_lbl.setText(preset.slot_id)
        self.label_edit.setText(preset.label)
        self.voltage_spin.setValue(preset.voltage_v)
        self.current_spin.setValue(preset.current_a)
        self.status_lbl.setText(f"Editing {preset.display_name}")

    def _load_from_current(self) -> None:
        self.voltage_spin.setValue(self._current_voltage)
        self.current_spin.setValue(self._current_current)
        self.status_lbl.setText("Loaded current output values")

    def _recall_to_output(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        self.recall_requested.emit(preset.voltage_v, preset.current_a)
        self.status_lbl.setText(f"Recalled {preset.display_name}")

    def _save_slot(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        label = self.label_edit.text().strip()
        if not label:
            label = preset.slot_id
        preset.label = label
        preset.voltage_v = float(self.voltage_spin.value())
        preset.current_a = float(self.current_spin.value())
        preset.enabled = True
        self._refresh_list()
        self.status_lbl.setText(f"Saved {preset.display_name}")

    def _clear_slot(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        if QMessageBox.question(self, "Clear slot", f"Clear preset {preset.slot_id}?") != QMessageBox.Yes:
            return
        preset.label = ""
        preset.voltage_v = 0.0
        preset.current_a = 0.0
        preset.enabled = False
        self._refresh_list()
        self._load_selected("")
        self.status_lbl.setText(f"Cleared {preset.slot_id}")
