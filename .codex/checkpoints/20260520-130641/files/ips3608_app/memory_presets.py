from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
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


    def load_all(self) -> list[MemoryPreset]:
        presets = [MemoryPreset(slot_id=slot) for slot in DEFAULT_SLOT_IDS]
        if not self.file_path.exists():
            return presets

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return presets

        # Migrazione automatica: se è una lista, convertila in oggetto versionato
        if isinstance(raw, list):
            # Backup vecchio formato
            backup_path = self.file_path.parent / f"../backup/v1/{self.file_path.stem}_legacy_{__import__('time').strftime('%Y%m%d')}.json"
            backup_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            raw = {"version": 2, "presets": raw}
            # Aggiorna file
            self.file_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

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
        # Backup prima di ogni salvataggio
        backup_path = self.file_path.parent / f"../backup/v1/{self.file_path.stem}_{__import__('time').strftime('%Y%m%d')}.json"
        if self.file_path.exists():
            backup_path.write_text(self.file_path.read_text(encoding="utf-8"), encoding="utf-8")
        serializable = {
            "version": 2,
            "presets": [asdict(p) for p in presets]
        }
        self.file_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")


class MemoryPresetDialog(QDialog):
    def __init__(self, parent: QWidget, presets: list[MemoryPreset]):
        super().__init__(parent)
        self.setWindowTitle("Memory Presets M1..M6")
        self.resize(860, 480)
        self.presets = presets
        self.selected_slot_id: Optional[str] = None

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
        self.apply_from_current_btn.clicked.connect(self._load_from_parent)
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

    def _load_from_parent(self) -> None:
        parent = self.parent()
        if parent is None:
            return
        vset = getattr(getattr(parent, "output_panel", None), "vset_spin", None)
        iset = getattr(getattr(parent, "output_panel", None), "iset_spin", None)
        if vset is None or iset is None:
            return
        self.voltage_spin.setValue(float(vset.value()))
        self.current_spin.setValue(float(iset.value()))
        self.status_lbl.setText("Loaded current output values")

    def _recall_to_output(self) -> None:
        preset = self._selected_preset()
        if preset is None:
            return
        parent = self.parent()
        if parent is None:
            return

        output_panel = getattr(parent, "output_panel", None)
        if output_panel is not None:
            output_panel.vset_spin.blockSignals(True)
            output_panel.iset_spin.blockSignals(True)
            output_panel.vset_spin.setValue(preset.voltage_v)
            output_panel.iset_spin.setValue(preset.current_a)
            output_panel.vset_spin.blockSignals(False)
            output_panel.iset_spin.blockSignals(False)

        device_client = getattr(parent, "device_client", None)
        app_state = getattr(parent, "app_state", None)
        if device_client is not None and app_state is not None and getattr(app_state, "connected", False):
            try:
                device_client.set_voltage(preset.voltage_v)
                device_client.set_current(preset.current_a)
            except Exception as exc:
                QMessageBox.warning(self, "Recall error", str(exc))
                return

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
        self._refresh_list()
        self._load_selected("")
        self.status_lbl.setText(f"Cleared {preset.slot_id}")
