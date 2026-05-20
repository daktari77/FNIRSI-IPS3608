from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import RoutineDefinition, RoutineStep


# ---------------------------------------------------------------------------
# Delegate per la colonna Output (dropdown ON / OFF)
# ---------------------------------------------------------------------------

class _OutputDelegate(QStyledItemDelegate):
    _OPTIONS = ("ON", "OFF")

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index) -> QComboBox:
        combo = QComboBox(parent)
        combo.addItems(self._OPTIONS)
        return combo

    def setEditorData(self, editor: QComboBox, index) -> None:
        val = index.data() or "ON"
        editor.setCurrentText(val if val in self._OPTIONS else "ON")

    def setModelData(self, editor: QComboBox, model, index) -> None:
        model.setData(index, editor.currentText())

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index) -> None:
        editor.setGeometry(option.rect)


# ---------------------------------------------------------------------------
# RoutineEditorDialog
# ---------------------------------------------------------------------------

_COL_NAME     = 0
_COL_V        = 1
_COL_I        = 2
_COL_DUR      = 3
_COL_OUTPUT   = 4
_COL_OTP      = 5
_COL_SETTLE   = 6
_HEADERS      = ["Name", "V (V)", "I (A)", "Duration (s)", "Output", "OTP °C", "Settle ms"]


class RoutineEditorDialog(QDialog):
    def __init__(self, parent: QWidget, initial: Optional[RoutineDefinition] = None):
        super().__init__(parent)
        self.setWindowTitle("Routine Editor")
        self.resize(920, 500)
        self.result_routine: Optional[RoutineDefinition] = None

        # --- header form ---
        self.name_btn = QPushButton(initial.name if initial else "Set routine name")
        self.loops_spin = QSpinBox()
        self.loops_spin.setRange(0, 9999)
        self.loops_spin.setValue(1 if initial is None else initial.loops)
        self.loops_spin.setSpecialValueText("∞  (infinite)")
        self.loops_spin.setToolTip("0 = repeat indefinitely")

        self.stop_output_chk = QCheckBox("Stop output when routine ends")
        self.stop_output_chk.setChecked(True if initial is None else initial.stop_output_on_finish)

        head = QFormLayout()
        head.addRow("Name:", self.name_btn)
        head.addRow("Loops:", self.loops_spin)
        head.addRow("Options:", self.stop_output_chk)

        # --- preview ---
        self.preview_lbl = QLabel("")
        self.preview_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")

        # --- table ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(_HEADERS)
        self.table.setItemDelegateForColumn(_COL_OUTPUT, _OutputDelegate(self))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(False)
        for col, w in enumerate([160, 70, 70, 90, 60, 70, 80]):
            self.table.setColumnWidth(col, w)

        # --- row controls ---
        add_btn = QPushButton("Add Step")
        dup_btn = QPushButton("Duplicate")
        del_btn = QPushButton("Remove Step")
        up_btn  = QPushButton("▲")
        down_btn = QPushButton("▼")
        row_bar = QHBoxLayout()
        row_bar.addWidget(add_btn)
        row_bar.addWidget(dup_btn)
        row_bar.addWidget(del_btn)
        row_bar.addSpacing(16)
        row_bar.addWidget(up_btn)
        row_bar.addWidget(down_btn)
        row_bar.addStretch(1)

        # --- save / cancel ---
        save_btn   = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_btn)
        actions.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(head)
        layout.addWidget(QLabel("Steps — each step applies constant V/I for the given duration:"))
        layout.addWidget(self.table)
        layout.addWidget(self.preview_lbl)
        layout.addLayout(row_bar)
        layout.addLayout(actions)

        # --- signals ---
        self.name_btn.clicked.connect(self._pick_name)
        add_btn.clicked.connect(self._add_default_row)
        dup_btn.clicked.connect(self._duplicate_row)
        del_btn.clicked.connect(self._remove_selected_row)
        up_btn.clicked.connect(lambda: self._move_row(-1))
        down_btn.clicked.connect(lambda: self._move_row(1))
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        self.table.cellChanged.connect(self._update_preview)
        self.loops_spin.valueChanged.connect(self._update_preview)

        # --- populate ---
        if initial and initial.steps:
            for step in initial.steps:
                self._add_row(step)
        else:
            self._add_default_row()

        self._update_preview()

    # ------------------------------------------------------------------ helpers

    def _make_item(self, text: str, editable: bool = True) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _add_row(self, step: RoutineStep) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.blockSignals(True)
        self.table.setItem(row, _COL_NAME,   self._make_item(step.name))
        self.table.setItem(row, _COL_V,      self._make_item(f"{step.voltage_v:.3f}"))
        self.table.setItem(row, _COL_I,      self._make_item(f"{step.current_a:.3f}"))
        self.table.setItem(row, _COL_DUR,    self._make_item(f"{step.duration_s:.1f}"))
        self.table.setItem(row, _COL_OUTPUT, self._make_item("ON" if step.output_on else "OFF"))
        self.table.setItem(row, _COL_OTP,    self._make_item(f"{step.otp_limit_c:.1f}"))
        self.table.setItem(row, _COL_SETTLE, self._make_item(f"{step.settle_ms:.0f}"))
        self.table.blockSignals(False)

    def _add_default_row(self) -> None:
        self._add_row(RoutineStep(voltage_v=12.0, current_a=1.0, duration_s=10.0))
        self._update_preview()

    def _duplicate_row(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        step = self._row_to_step(row)
        if step:
            self._add_row(step)
            self._update_preview()

    def _remove_selected_row(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            row = self.table.rowCount() - 1
        if row >= 0:
            self.table.removeRow(row)
            self._update_preview()

    def _move_row(self, direction: int) -> None:
        row = self.table.currentRow()
        target = row + direction
        if row < 0 or not (0 <= target < self.table.rowCount()):
            return
        for col in range(self.table.columnCount()):
            a = self.table.item(row, col)
            b = self.table.item(target, col)
            ta = a.text() if a else ""
            tb = b.text() if b else ""
            if a:
                a.setText(tb)
            if b:
                b.setText(ta)
        self.table.setCurrentCell(target, self.table.currentColumn())

    # ------------------------------------------------------------------ preview

    def _update_preview(self) -> None:
        self.table.blockSignals(True)
        total_s = 0.0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, _COL_DUR)
            try:
                total_s += float(item.text()) if item else 0.0
            except ValueError:
                pass
        self.table.blockSignals(False)

        loops = self.loops_spin.value()
        steps = self.table.rowCount()
        if loops == 0:
            self.preview_lbl.setText(
                f"{steps} step{'s' if steps != 1 else ''}  ·  Step total: {total_s:.1f}s  ·  Total: ∞ (infinite loops)"
            )
        else:
            self.preview_lbl.setText(
                f"{steps} step{'s' if steps != 1 else ''}  ·  "
                f"Step total: {total_s:.1f}s  ·  "
                f"Total: {total_s * loops:.1f}s  ({loops} loop{'s' if loops > 1 else ''})"
            )

    # ------------------------------------------------------------------ name

    def _pick_name(self) -> None:
        current = self.name_btn.text() if self.name_btn.text() != "Set routine name" else ""
        text, ok = QInputDialog.getText(self, "Routine Name", "Name:", text=current)
        if ok and text.strip():
            self.name_btn.setText(text.strip())

    # ------------------------------------------------------------------ parse

    def _row_to_step(self, row: int) -> Optional[RoutineStep]:
        try:
            return RoutineStep(
                name=self.table.item(row, _COL_NAME).text().strip()   if self.table.item(row, _COL_NAME)   else "",
                voltage_v=float(self.table.item(row, _COL_V).text())  if self.table.item(row, _COL_V)      else 0.0,
                current_a=float(self.table.item(row, _COL_I).text())  if self.table.item(row, _COL_I)      else 0.0,
                duration_s=float(self.table.item(row, _COL_DUR).text()) if self.table.item(row, _COL_DUR)  else 0.0,
                output_on=(self.table.item(row, _COL_OUTPUT).text().upper() == "ON") if self.table.item(row, _COL_OUTPUT) else True,
                otp_limit_c=float(self.table.item(row, _COL_OTP).text())    if self.table.item(row, _COL_OTP)    else 0.0,
                settle_ms=float(self.table.item(row, _COL_SETTLE).text())   if self.table.item(row, _COL_SETTLE) else 200.0,
            )
        except (ValueError, AttributeError):
            return None

    # ------------------------------------------------------------------ save

    def _save(self) -> None:
        name = self.name_btn.text().strip()
        if not name or name == "Set routine name":
            QMessageBox.warning(self, "Invalid", "Please set a routine name.")
            return
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Invalid", "Add at least one step.")
            return

        steps: list[RoutineStep] = []
        try:
            for row in range(self.table.rowCount()):
                step = self._row_to_step(row)
                if step is None:
                    raise ValueError(f"Row {row + 1}: unable to parse values.")
                if not (0.0 <= step.voltage_v <= 36.0):
                    raise ValueError(f"Row {row + 1}: voltage out of range 0..36 V")
                if not (0.0 <= step.current_a <= 8.2):
                    raise ValueError(f"Row {row + 1}: current out of range 0..8.2 A")
                if step.duration_s <= 0.0:
                    raise ValueError(f"Row {row + 1}: duration must be > 0 s")
                if not (0.0 <= step.otp_limit_c <= 99.0):
                    raise ValueError(f"Row {row + 1}: OTP limit out of range 0..99 °C (0 = disabled)")
                if step.settle_ms < 0.0:
                    raise ValueError(f"Row {row + 1}: settle time must be ≥ 0 ms")
                steps.append(step)
        except (ValueError, AttributeError) as exc:
            QMessageBox.critical(self, "Invalid data", str(exc))
            return

        self.result_routine = RoutineDefinition(
            name=name,
            steps=steps,
            loops=self.loops_spin.value(),
            stop_output_on_finish=self.stop_output_chk.isChecked(),
        )
        self.accept()


# ---------------------------------------------------------------------------
# RoutineManagerDialog
# ---------------------------------------------------------------------------

class RoutineManagerDialog(QDialog):
    def __init__(self, parent: QWidget, routines: list[RoutineDefinition]):
        super().__init__(parent)
        self.setWindowTitle("Routine Manager")
        self.resize(860, 520)

        self.routines = routines
        self.selected_run_name: Optional[str] = None

        self.list_widget = QListWidget()
        self.preview = QLabel("Select a routine")
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet("color: #4A5A6A; font-size: 11px;")

        self.new_btn    = QPushButton("New")
        self.edit_btn   = QPushButton("Edit")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.run_btn    = QPushButton("▶  Run")
        self.close_btn  = QPushButton("Close")

        self.run_btn.setStyleSheet(
            "font-weight: 700; background-color: #16A34A; color: #FFFFFF;"
            "border: none; border-radius: 6px; padding: 6px 14px;"
        )

        left_actions = QHBoxLayout()
        left_actions.addWidget(self.new_btn)
        left_actions.addWidget(self.edit_btn)
        left_actions.addWidget(self.rename_btn)
        left_actions.addWidget(self.delete_btn)

        right_actions = QHBoxLayout()
        right_actions.addStretch(1)
        right_actions.addWidget(self.run_btn)
        right_actions.addWidget(self.close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Stored routines:"))
        layout.addWidget(self.list_widget)
        layout.addLayout(left_actions)
        layout.addWidget(self.preview)
        layout.addLayout(right_actions)

        self.new_btn.clicked.connect(self._new)
        self.edit_btn.clicked.connect(self._edit)
        self.rename_btn.clicked.connect(self._rename)
        self.delete_btn.clicked.connect(self._delete)
        self.run_btn.clicked.connect(self._run_selected)
        self.close_btn.clicked.connect(self.reject)
        self.list_widget.currentTextChanged.connect(self._refresh_preview)

        self._refresh_list()

    # ------------------------------------------------------------------ helpers

    def _refresh_list(self) -> None:
        self.list_widget.clear()
        for r in sorted(self.routines, key=lambda x: x.name.lower()):
            self.list_widget.addItem(r.name)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        self._refresh_preview(
            self.list_widget.currentItem().text() if self.list_widget.currentItem() else ""
        )

    def _selected_routine(self) -> Optional[RoutineDefinition]:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        name = item.text()
        return next((r for r in self.routines if r.name == name), None)

    # ------------------------------------------------------------------ CRUD

    def _new(self) -> None:
        dlg = RoutineEditorDialog(self)
        if dlg.exec() != QDialog.Accepted or dlg.result_routine is None:
            return
        if any(r.name == dlg.result_routine.name for r in self.routines):
            QMessageBox.warning(self, "Duplicate name", "A routine with this name already exists.")
            return
        self.routines.append(dlg.result_routine)
        self._refresh_list()

    def _edit(self) -> None:
        selected = self._selected_routine()
        if selected is None:
            return
        dlg = RoutineEditorDialog(self, initial=selected)
        if dlg.exec() != QDialog.Accepted or dlg.result_routine is None:
            return
        replacement = dlg.result_routine
        if replacement.name != selected.name and any(r.name == replacement.name for r in self.routines):
            QMessageBox.warning(self, "Duplicate name", "A routine with this name already exists.")
            return
        self.routines[self.routines.index(selected)] = replacement
        self._refresh_list()

    def _rename(self) -> None:
        selected = self._selected_routine()
        if selected is None:
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=selected.name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        if any(r.name == new_name and r is not selected for r in self.routines):
            QMessageBox.warning(self, "Duplicate name", "A routine with this name already exists.")
            return
        selected.name = new_name
        self._refresh_list()

    def _delete(self) -> None:
        selected = self._selected_routine()
        if selected is None:
            return
        if QMessageBox.question(self, "Delete", f"Delete routine '{selected.name}'?") != QMessageBox.Yes:
            return
        self.routines.remove(selected)
        self._refresh_list()

    def _run_selected(self) -> None:
        selected = self._selected_routine()
        if selected is None:
            QMessageBox.information(self, "Run routine", "Select a routine first.")
            return
        self.selected_run_name = selected.name
        self.accept()

    # ------------------------------------------------------------------ preview

    def _refresh_preview(self, name: str) -> None:
        selected = next((r for r in self.routines if r.name == name), None)
        if selected is None:
            self.preview.setText("Select a routine")
            return

        loops_txt = "∞" if selected.loops == 0 else str(selected.loops)
        step_total = selected.total_step_duration_s
        if selected.loops == 0:
            total_txt = f"{step_total:.1f}s × ∞"
        else:
            total_txt = f"{selected.total_duration_s:.1f}s ({selected.loops} loop{'s' if selected.loops > 1 else ''})"

        has_off_steps = any(not s.output_on for s in selected.steps)
        has_otp = any(s.otp_limit_c > 0.0 for s in selected.steps)
        flags = []
        if has_off_steps:
            flags.append("output OFF steps")
        if has_otp:
            flags.append("per-step OTP")
        if selected.stop_output_on_finish:
            flags.append("stop output at end")
        flags_txt = "  ·  " + "  ·  ".join(flags) if flags else ""

        steps_summary = ""
        for i, s in enumerate(selected.steps[:5]):
            label = f"S{i+1}" + (f" {s.name}" if s.name else "")
            out = "ON" if s.output_on else "OFF"
            otp = f" OTP{s.otp_limit_c:.0f}°C" if s.otp_limit_c > 0 else ""
            steps_summary += f"  {label}: {s.voltage_v:.2f}V / {s.current_a:.3f}A / {s.duration_s:.1f}s / {out}{otp}\n"
        if len(selected.steps) > 5:
            steps_summary += f"  … +{len(selected.steps) - 5} more steps\n"

        self.preview.setText(
            f"<b>{selected.name}</b>  ·  {len(selected.steps)} steps  ·  "
            f"Loops: {loops_txt}  ·  Total: {total_txt}{flags_txt}\n\n"
            + steps_summary
        )
