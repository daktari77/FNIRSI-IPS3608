from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import RoutineDefinition, RoutineStep


class RoutineEditorDialog(QDialog):
    def __init__(self, parent: QWidget, initial: Optional[RoutineDefinition] = None):
        super().__init__(parent)
        self.setWindowTitle("Routine Editor")
        self.resize(860, 460)
        self.result_routine: Optional[RoutineDefinition] = None

        self.name_btn = QPushButton(initial.name if initial else "Set routine name")
        self.stop_output_chk = QCheckBox("Stop output when routine ends")
        self.stop_output_chk.setChecked(True if initial is None else initial.stop_output_on_finish)

        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setRange(0.0, 86400.0)
        self.limit_spin.setDecimals(1)
        self.limit_spin.setSingleStep(1.0)
        self.limit_spin.setSuffix(" s (0 = disabled)")
        self.limit_spin.setValue(0.0 if initial is None else initial.execution_limit_s)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "V start (V)",
            "V end (V)",
            "I start (A)",
            "I end (A)",
            "Duration (s)",
        ])

        add_row_btn = QPushButton("Add Step")
        del_row_btn = QPushButton("Remove Step")
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        head = QFormLayout()
        head.addRow("Name:", self.name_btn)
        head.addRow("Execution limit:", self.limit_spin)
        head.addRow("Options:", self.stop_output_chk)

        row_controls = QHBoxLayout()
        row_controls.addWidget(add_row_btn)
        row_controls.addWidget(del_row_btn)
        row_controls.addStretch(1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(save_btn)
        actions.addWidget(cancel_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(head)
        layout.addWidget(QLabel("Linear ramp steps over time:"))
        layout.addWidget(self.table)
        layout.addLayout(row_controls)
        layout.addLayout(actions)

        self.name_btn.clicked.connect(self._pick_name)
        add_row_btn.clicked.connect(self._add_default_row)
        del_row_btn.clicked.connect(self._remove_selected_row)
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

        if initial is not None:
            for step in initial.steps:
                self._add_row(step)
        else:
            self._add_default_row()

    def _pick_name(self) -> None:
        current = self.name_btn.text() if self.name_btn.text() != "Set routine name" else ""
        text, ok = QInputDialog.getText(self, "Routine Name", "Name:", text=current)
        if ok and text.strip():
            self.name_btn.setText(text.strip())

    def _add_default_row(self) -> None:
        self._add_row(RoutineStep(12.0, 12.0, 1.0, 1.0, 10.0))

    def _add_row(self, step: RoutineStep) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        vals = [
            f"{step.voltage_start_v:.3f}",
            f"{step.voltage_end_v:.3f}",
            f"{step.current_start_a:.3f}",
            f"{step.current_end_a:.3f}",
            f"{step.duration_s:.1f}",
        ]
        for col, val in enumerate(vals):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)

    def _remove_selected_row(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            row = self.table.rowCount() - 1
        if row >= 0:
            self.table.removeRow(row)

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
                v0 = float(self.table.item(row, 0).text())
                v1 = float(self.table.item(row, 1).text())
                i0 = float(self.table.item(row, 2).text())
                i1 = float(self.table.item(row, 3).text())
                dt = float(self.table.item(row, 4).text())

                if not (0.0 <= v0 <= 36.0 and 0.0 <= v1 <= 36.0):
                    raise ValueError(f"Row {row + 1}: voltage out of range 0..36V")
                if not (0.0 <= i0 <= 8.0 and 0.0 <= i1 <= 8.0):
                    raise ValueError(f"Row {row + 1}: current out of range 0..8A")
                if dt <= 0.0:
                    raise ValueError(f"Row {row + 1}: duration must be > 0")

                steps.append(RoutineStep(v0, v1, i0, i1, dt))
        except Exception as exc:
            QMessageBox.critical(self, "Invalid data", str(exc))
            return

        self.result_routine = RoutineDefinition(
            name=name,
            steps=steps,
            stop_output_on_finish=self.stop_output_chk.isChecked(),
            execution_limit_s=float(self.limit_spin.value()),
        )
        self.accept()


class RoutineManagerDialog(QDialog):
    def __init__(self, parent: QWidget, routines: list[RoutineDefinition]):
        super().__init__(parent)
        self.setWindowTitle("Routine Manager")
        self.resize(840, 500)

        self.routines = routines
        self.selected_run_name: Optional[str] = None

        self.list_widget = QListWidget()
        self.preview = QLabel("Select a routine")
        self.preview.setWordWrap(True)

        self.new_btn = QPushButton("New")
        self.edit_btn = QPushButton("Edit")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.run_btn = QPushButton("Run")
        self.close_btn = QPushButton("Close")

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

    def _refresh_list(self) -> None:
        self.list_widget.clear()
        for r in sorted(self.routines, key=lambda x: x.name.lower()):
            self.list_widget.addItem(r.name)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        self._refresh_preview(self.list_widget.currentItem().text() if self.list_widget.currentItem() else "")

    def _selected_routine(self) -> Optional[RoutineDefinition]:
        name = self.list_widget.currentItem().text() if self.list_widget.currentItem() else ""
        for r in self.routines:
            if r.name == name:
                return r
        return None

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
        idx = self.routines.index(selected)
        self.routines[idx] = replacement
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

    def _refresh_preview(self, name: str) -> None:
        selected = None
        for r in self.routines:
            if r.name == name:
                selected = r
                break
        if selected is None:
            self.preview.setText("Select a routine")
            return

        stop_txt = "yes" if selected.stop_output_on_finish else "no"
        limit_txt = f"{selected.execution_limit_s:.1f}s" if selected.execution_limit_s > 0 else "disabled"
        self.preview.setText(
            f"Name: {selected.name} | Steps: {len(selected.steps)} | "
            f"Step total: {selected.total_step_duration_s:.1f}s | "
            f"Execution limit: {limit_txt} | Stop output at end: {stop_txt}"
        )
