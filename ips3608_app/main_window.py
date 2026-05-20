from __future__ import annotations

import csv
import copy
import sys
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .clients import IPS3608Client, SimulatedIPS3608Client
from .memory_presets import MemoryPresetDialog, MemoryRepository
from .models import AppState, DeviceConfig, LogSample, Measurement, RoutineDefinition, UiState, DEFAULT_DEVICE_CONFIG
from .routine_dialogs import RoutineManagerDialog
from .routines import ActiveRoutineRunner, RoutineRepository
from .ui_panels import (
    ConnectionPanel,
    DataloggerPanel,
    GraphPanel,
    LogTableDialog,
    OutputControlPanel,
    RealtimeCardsPanel,
    StatusLogPanel,
)

try:
    from serial.tools import list_ports
except ImportError as exc:
    raise SystemExit("Missing dependency: pyserial. Install with: pip install pyserial") from exc


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FNIRSI IPS3608 Remote Control")
        self.resize(1360, 900)

        self.app_state = AppState()
        self.device_config = DEFAULT_DEVICE_CONFIG
        self.device_client: Optional[object] = None
        self.log_samples: list[LogSample] = []
        self.last_measurement: Optional[Measurement] = None
        self.log_table_dialog: Optional[LogTableDialog] = None
        self.routine_repository = RoutineRepository(Path.cwd() / "ips3608_routines.json")
        self.routines: list[RoutineDefinition] = self.routine_repository.load_all()
        self.active_routine: Optional[ActiveRoutineRunner] = None
        self.active_routine_name: str = "--"
        self.last_routine_setpoint_mono = 0.0
        self.memory_repository = MemoryRepository(Path.cwd() / "ips3608_memories.json")
        self.memory_presets = self.memory_repository.load_all()

        self.connection_panel = ConnectionPanel()
        self.output_panel = OutputControlPanel()
        self.cards_panel = RealtimeCardsPanel()
        self.graph_panel = GraphPanel()
        self.datalogger_panel = DataloggerPanel()
        self.status_panel = StatusLogPanel()

        self.measure_timer = QTimer(self)
        self.measure_timer.timeout.connect(self._read_measurement_cycle)
        self.measure_timer.setInterval(500)

        self.log_status_timer = QTimer(self)
        self.log_status_timer.timeout.connect(self._update_log_runtime_info)
        self.log_status_timer.setInterval(1000)

        self.routine_timer = QTimer(self)
        self.routine_timer.timeout.connect(self._routine_tick)
        self.routine_timer.setInterval(200)

        self.next_log_due_monotonic = 0.0

        self._build_menu()
        self._build_ui()
        self._wire_signals()
        self._apply_style()
        self.refresh_ports()
        self._set_ui_state(UiState.DISCONNECTED)
        self._status("Application ready. Default mode: real.")

    def _build_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        self.act_export_file = QAction("Export log CSV", self)
        self.act_exit = QAction("Exit", self)
        file_menu.addAction(self.act_export_file)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        datalogger_menu = menu.addMenu("Datalogger")
        self.act_log_start = QAction("Start logging", self)
        self.act_log_stop = QAction("Stop logging", self)
        self.act_log_table = QAction("View log table", self)
        self.act_log_clear = QAction("Clear current log", self)
        self.act_log_export = QAction("Export log CSV", self)
        datalogger_menu.addActions([
            self.act_log_start,
            self.act_log_stop,
            self.act_log_table,
            self.act_log_clear,
            self.act_log_export,
        ])

        graph_menu = menu.addMenu("Graphs")
        self.act_graph_pause = QAction("Pause graphs", self)
        self.act_graph_reset = QAction("Reset graphs", self)
        self.act_graph_autoscale = QAction("Autoscale", self)
        graph_menu.addActions([self.act_graph_pause, self.act_graph_reset, self.act_graph_autoscale])

        routine_menu = menu.addMenu("Routine")
        self.act_routine_manage = QAction("Manage routines", self)
        self.act_routine_stop = QAction("Stop active routine", self)
        routine_menu.addActions([self.act_routine_manage, self.act_routine_stop])

        memory_menu = menu.addMenu("Memory")
        self.act_memory_manage = QAction("Manage memories M1..M6", self)
        memory_menu.addAction(self.act_memory_manage)

        instrument_menu = menu.addMenu("Instrument")
        self.act_connect = QAction("Connect", self)
        self.act_disconnect = QAction("Disconnect", self)
        self.act_output_start = QAction("Start Output", self)
        self.act_output_stop = QAction("Stop Output", self)
        instrument_menu.addActions([
            self.act_connect,
            self.act_disconnect,
            self.act_output_start,
            self.act_output_stop,
        ])

        mode_menu = menu.addMenu("Mode")
        self.act_mode_real = QAction("Real mode", self, checkable=True)
        self.act_mode_sim = QAction("Simulated mode", self, checkable=True)
        mode_group = QActionGroup(self)
        mode_group.setExclusive(True)
        mode_group.addAction(self.act_mode_real)
        mode_group.addAction(self.act_mode_sim)
        self.act_mode_real.setChecked(True)
        mode_menu.addAction(self.act_mode_real)
        mode_menu.addAction(self.act_mode_sim)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.addWidget(self.connection_panel)
        root.addWidget(self.output_panel)
        root.addWidget(self.datalogger_panel)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.cards_panel)
        split.addWidget(self.graph_panel)
        split.setSizes([420, 900])

        root.addWidget(split, stretch=1)
        root.addWidget(self.status_panel)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _wire_signals(self) -> None:
        self.connection_panel.refresh_ports_requested.connect(self.refresh_ports)
        self.connection_panel.connect_requested.connect(self.connect_device)
        self.connection_panel.disconnect_requested.connect(self.disconnect_device)

        self.output_panel.start_output_requested.connect(self.start_output)
        self.output_panel.stop_output_requested.connect(self.stop_output)
        self.output_panel.voltage_changed.connect(self.on_voltage_changed)
        self.output_panel.current_changed.connect(self.on_current_changed)

        self.datalogger_panel.start_log_requested.connect(self.start_logging)
        self.datalogger_panel.stop_log_requested.connect(self.stop_logging)
        self.datalogger_panel.show_table_requested.connect(self.show_log_table)
        self.datalogger_panel.export_csv_requested.connect(self.export_log_csv)

        self.act_export_file.triggered.connect(self.export_log_csv)
        self.act_exit.triggered.connect(self.close)

        self.act_log_start.triggered.connect(self.start_logging)
        self.act_log_stop.triggered.connect(self.stop_logging)
        self.act_log_table.triggered.connect(self.show_log_table)
        self.act_log_clear.triggered.connect(self.clear_log)
        self.act_log_export.triggered.connect(self.export_log_csv)

        self.act_graph_pause.triggered.connect(self.graph_panel._toggle_pause)
        self.act_graph_reset.triggered.connect(self.graph_panel.clear)
        self.act_graph_autoscale.triggered.connect(self.graph_panel._autoscale)

        self.act_connect.triggered.connect(lambda: self.connect_device(self.connection_panel.port_combo.currentText().strip()))
        self.act_disconnect.triggered.connect(self.disconnect_device)
        self.act_output_start.triggered.connect(self.start_output)
        self.act_output_stop.triggered.connect(self.stop_output)

        self.act_mode_real.triggered.connect(lambda: self.set_mode(simulated=False))
        self.act_mode_sim.triggered.connect(lambda: self.set_mode(simulated=True))
        self.act_routine_manage.triggered.connect(self.manage_routines)
        self.act_routine_stop.triggered.connect(self.stop_active_routine)
        self.act_memory_manage.triggered.connect(self.manage_memories)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0b1220; color: #e2e8f0; }
            QGroupBox {
                border: 1px solid #334155; border-radius: 8px; margin-top: 10px;
                font-weight: 700; color: #f8fafc; background: #0f172a;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
            QLabel { color: #e2e8f0; }
            QPushButton {
                background-color: #1e293b; color: #e2e8f0; border: 1px solid #475569;
                border-radius: 6px; padding: 6px 10px; font-weight: 600;
            }
            QPushButton:hover { background-color: #334155; }
            QComboBox, QDoubleSpinBox {
                background-color: #111827; border: 1px solid #475569; border-radius: 5px;
                padding: 4px; color: #e2e8f0;
            }
            QTableWidget {
                background-color: #111827; color: #e5e7eb; gridline-color: #334155;
                border: 1px solid #334155;
            }
            QHeaderView::section {
                background-color: #1f2937; color: #f8fafc; border: 1px solid #334155;
                padding: 4px;
            }
            QTextEdit { background-color: #111827; border: 1px solid #334155; color: #e5e7eb; }
            QFrame#MetricCard { background-color: #111827; border: 1px solid #334155; border-radius: 10px; }
            """
        )
        pg.setConfigOption("background", "#0b1220")
        pg.setConfigOption("foreground", "#cbd5e1")

    def _status(self, text: str) -> None:
        self.statusBar().showMessage(text, 6000)
        self.status_panel.add_log_line(text)

    def refresh_ports(self) -> None:
        ports = [p.device for p in list_ports.comports()]
        # Keep SIMULATED available in all modes for explicit testing.
        self.connection_panel.set_ports(ports, include_simulated=True)
        self._select_default_port_for_mode()

    def set_mode(self, simulated: bool) -> None:
        if self.app_state.connected:
            QMessageBox.information(self, "Mode change", "Disconnect first to change mode.")
            self.act_mode_sim.setChecked(self.app_state.mode_simulated)
            self.act_mode_real.setChecked(not self.app_state.mode_simulated)
            return
        self.app_state.mode_simulated = simulated
        self.refresh_ports()
        self._status(f"Mode set to {'simulated' if simulated else 'real'}.")

    def _select_default_port_for_mode(self) -> None:
        combo = self.connection_panel.port_combo
        if combo.count() == 0:
            return

        current = combo.currentText().strip()
        if self.app_state.mode_simulated:
            idx = combo.findText("SIMULATED")
            if idx >= 0:
                combo.setCurrentIndex(idx)
            return

        # In real mode prefer a hardware serial port if available.
        if current and current != "SIMULATED":
            return

        for i in range(combo.count()):
            if combo.itemText(i) != "SIMULATED":
                combo.setCurrentIndex(i)
                return

    def connect_device(self, selected_port: str) -> None:
        if self.app_state.connected:
            self._status("Already connected.")
            return

        self._set_ui_state(UiState.CONNECTING)
        self.app_state.selected_port = selected_port or self.device_config.port

        try:
            cfg = DeviceConfig(**vars(self.device_config))
            cfg.port = self.app_state.selected_port

            if not cfg.port:
                raise RuntimeError("No serial port selected")

            use_simulated = cfg.port.upper() == "SIMULATED"
            if use_simulated and not self.app_state.mode_simulated:
                self._status("SIMULATED port selected while in real mode. Switching to simulated client.")

            if use_simulated:
                self.device_client = SimulatedIPS3608Client(cfg)
            else:
                self.device_client = IPS3608Client(cfg)

            assert self.device_client is not None
            self.device_client.connect()
            self.app_state.connected = True
            self.app_state.output_on = False
            self.app_state.last_error = "--"
            self.app_state.last_command = "CONNECT"

            try:
                self.device_client.set_voltage(self.output_panel.vset_spin.value())
                self.device_client.set_current(self.output_panel.iset_spin.value())
            except Exception:
                pass

            self.measure_timer.start()
            self._set_ui_state(UiState.CONNECTED_OUTPUT_OFF)
            conn_kind = "simulated" if use_simulated else "real"
            self._status(f"Connected ({conn_kind}) on {cfg.port}.")
        except Exception as exc:
            self.app_state.last_error = str(exc)
            self._set_ui_state(UiState.COMMUNICATION_ERROR)
            self._status(f"Connection error: {exc}")

    def disconnect_device(self) -> None:
        self.measure_timer.stop()
        if self.app_state.logging_on:
            self.stop_logging(silent=True)

        if self.device_client is not None:
            try:
                self.device_client.disconnect()
            except Exception as exc:
                self.app_state.last_error = str(exc)

        self.device_client = None
        self.app_state.connected = False
        self.app_state.output_on = False
        self.app_state.last_command = "DISCONNECT"
        self.stop_active_routine(silent=True)
        self._set_ui_state(UiState.DISCONNECTED)
        self._status("Disconnected.")

    def start_output(self) -> None:
        if not self.app_state.connected or self.device_client is None:
            QMessageBox.warning(self, "Not connected", "Connect to the device before starting output.")
            return
        try:
            self.device_client.start_output()
            self.app_state.output_on = True
            self.app_state.last_command = "START_OUTPUT"
            self._set_ui_state(UiState.CONNECTED_OUTPUT_ON)
            self._status("Output started.")
        except Exception as exc:
            self._handle_communication_error(f"Start output failed: {exc}")

    def stop_output(self) -> None:
        if not self.app_state.connected or self.device_client is None:
            QMessageBox.warning(self, "Not connected", "Connect to the device before stopping output.")
            return
        try:
            self.device_client.stop_output()
            self.app_state.output_on = False
            self.app_state.last_command = "STOP_OUTPUT"
            self._set_ui_state(UiState.CONNECTED_OUTPUT_OFF)
            if self.last_measurement is not None:
                zero_current = replace(self.last_measurement, current_a=0.0)
                self.last_measurement = zero_current
                self.app_state.last_data_ts = zero_current.timestamp
                self.cards_panel.update_measurement(
                    zero_current,
                    self.output_panel.vset_spin.value(),
                    self.output_panel.iset_spin.value(),
                )
                self.graph_panel.add_measurement(zero_current)
            self._status("Output stopped.")
        except Exception as exc:
            self._handle_communication_error(f"Stop output failed: {exc}")

    def on_voltage_changed(self, value: float) -> None:
        if not self.app_state.connected or self.device_client is None:
            return
        try:
            self.device_client.set_voltage(value)
            self.app_state.last_command = f"SET_VOLT {value:.2f}"
        except Exception as exc:
            self._status(f"Voltage set failed: {exc}")

    def on_current_changed(self, value: float) -> None:
        if not self.app_state.connected or self.device_client is None:
            return
        try:
            self.device_client.set_current(value)
            self.app_state.last_command = f"SET_CURR {value:.3f}"
        except Exception as exc:
            self._status(f"Current set failed: {exc}")

    def _read_measurement_cycle(self) -> None:
        if not self.app_state.connected or self.device_client is None:
            return
        try:
            m = self.device_client.read_measurements()
            if not self.app_state.output_on:
                m.current_a = 0.0
            self.last_measurement = m
            self.app_state.last_data_ts = m.timestamp
            self.app_state.last_error = "--"

            self.cards_panel.update_measurement(m, self.output_panel.vset_spin.value(), self.output_panel.iset_spin.value())
            self.graph_panel.add_measurement(m)
            self._maybe_append_log_sample(m)
            self._refresh_status_summary()

            if self.log_table_dialog is not None and self.log_table_dialog.isVisible() and self.app_state.logging_on:
                self.log_table_dialog.set_samples(self.log_samples)
        except Exception as exc:
            self._handle_communication_error(f"Read cycle error: {exc}")

    def manage_routines(self) -> None:
        dlg = RoutineManagerDialog(self, copy.deepcopy(self.routines))
        if dlg.exec() != QDialog.Accepted:
            return

        self.routines = dlg.routines
        self.routine_repository.save_all(self.routines)
        self._status(f"Routine library saved ({len(self.routines)} routines).")

        if dlg.selected_run_name:
            self.start_routine_by_name(dlg.selected_run_name)

    def manage_memories(self) -> None:
        dlg = MemoryPresetDialog(self, copy.deepcopy(self.memory_presets))
        if dlg.exec() != QDialog.Accepted:
            return

        self.memory_presets = dlg.presets
        self.memory_repository.save_all(self.memory_presets)
        self._status("Memory presets saved (M1..M6).")

    def start_routine_by_name(self, name: str) -> None:
        if not self.app_state.connected or self.device_client is None:
            QMessageBox.warning(self, "Not connected", "Connect to the device before running a routine.")
            return

        routine = next((r for r in self.routines if r.name == name), None)
        if routine is None:
            QMessageBox.warning(self, "Routine", f"Routine '{name}' not found.")
            return
        if not routine.steps:
            QMessageBox.warning(self, "Routine", "Selected routine has no steps.")
            return

        self.active_routine = ActiveRoutineRunner(routine)
        self.active_routine_name = routine.name
        self.last_routine_setpoint_mono = 0.0
        self.routine_timer.start()
        self._status(f"Routine started: {routine.name}")

    def stop_active_routine(self, silent: bool = False) -> None:
        if self.active_routine is None:
            return

        routine = self.active_routine.routine
        self.routine_timer.stop()
        self.active_routine = None
        self.active_routine_name = "--"

        if routine.stop_output_on_finish and self.app_state.connected:
            try:
                self.stop_output()
            except Exception:
                pass

        if not silent:
            self._status("Routine stopped.")

    def _routine_tick(self) -> None:
        if self.active_routine is None or self.device_client is None:
            return
        if not self.app_state.connected:
            self.stop_active_routine(silent=True)
            return

        setpoints = self.active_routine.current_setpoints()
        if setpoints is None:
            ended_name = self.active_routine_name
            self.stop_active_routine(silent=True)
            self._status(f"Routine completed: {ended_name}")
            return

        now_mono = time.monotonic()
        if now_mono - self.last_routine_setpoint_mono < 0.2:
            return

        vset, iset = setpoints
        try:
            self.device_client.set_voltage(vset)
            self.device_client.set_current(iset)
            self.output_panel.vset_spin.blockSignals(True)
            self.output_panel.iset_spin.blockSignals(True)
            self.output_panel.vset_spin.setValue(vset)
            self.output_panel.iset_spin.setValue(iset)
            self.output_panel.vset_spin.blockSignals(False)
            self.output_panel.iset_spin.blockSignals(False)
            self.last_routine_setpoint_mono = now_mono
            self.app_state.last_command = f"ROUTINE_SET {vset:.2f}V {iset:.3f}A"
            if not self.app_state.output_on:
                self.start_output()
        except Exception as exc:
            self.stop_active_routine(silent=True)
            self._handle_communication_error(f"Routine execution error: {exc}")

    def _maybe_append_log_sample(self, m: Measurement) -> None:
        if not self.app_state.logging_on:
            return
        now_mono = time.monotonic()
        if now_mono < self.next_log_due_monotonic:
            return
        self.append_log_sample(m)
        self.next_log_due_monotonic = now_mono + self.datalogger_panel.interval_seconds()

    def start_logging(self) -> None:
        if not self.app_state.connected:
            QMessageBox.warning(self, "Not connected", "Cannot start logging without a connection.")
            return
        if self.app_state.logging_on:
            return

        if self.log_samples:
            msg = QMessageBox(self)
            msg.setWindowTitle("Existing log samples")
            msg.setText("Existing samples found. Append or clear before starting?")
            append_btn = msg.addButton("Append", QMessageBox.AcceptRole)
            clear_btn = msg.addButton("Clear and Start", QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == cancel_btn:
                return
            if clicked == clear_btn:
                self.clear_log(confirm=False)
            elif clicked != append_btn:
                return

        self.app_state.logging_on = True
        self.app_state.log_started_at = datetime.now()
        self.next_log_due_monotonic = 0.0
        self.datalogger_panel.interval_combo.setEnabled(False)
        self.datalogger_panel.set_logging_state(True)
        self.log_status_timer.start()
        self._set_ui_state(self.app_state.ui_state)
        self._status("Datalogger started.")

    def stop_logging(self, silent: bool = False) -> None:
        if not self.app_state.logging_on:
            return
        self.app_state.logging_on = False
        self.log_status_timer.stop()
        self.datalogger_panel.interval_combo.setEnabled(True)
        self.datalogger_panel.set_logging_state(False)
        self._set_ui_state(self.app_state.ui_state)
        if not silent:
            self._status("Datalogger stopped.")

    def append_log_sample(self, m: Measurement) -> None:
        self.log_samples.append(
            LogSample(
                timestamp=m.timestamp,
                voltage_v=m.voltage_v,
                current_a=m.current_a,
                temperature_c=m.temperature_c,
            )
        )
        self._update_log_runtime_info()

    def _update_log_runtime_info(self) -> None:
        last = self.log_samples[-1].timestamp if self.log_samples else None
        duration = 0
        if self.app_state.logging_on and self.app_state.log_started_at is not None:
            duration = int((datetime.now() - self.app_state.log_started_at).total_seconds())
        self.datalogger_panel.update_stats(len(self.log_samples), duration, last)
        self._refresh_status_summary()

    def clear_log(self, confirm: bool = True) -> None:
        if confirm and self.log_samples:
            if QMessageBox.question(self, "Clear log", "Clear all currently recorded log samples?") != QMessageBox.Yes:
                return
        self.log_samples.clear()
        self.datalogger_panel.update_stats(0, 0, None)
        if self.log_table_dialog is not None and self.log_table_dialog.isVisible():
            self.log_table_dialog.set_samples(self.log_samples)
        self._status("Log samples cleared.")

    def show_log_table(self) -> None:
        if self.log_table_dialog is None:
            self.log_table_dialog = LogTableDialog(self)
            self.log_table_dialog.export_requested.connect(self.export_log_csv)
            self.log_table_dialog.clear_requested.connect(self._clear_log_from_dialog)

        self.log_table_dialog.set_samples(self.log_samples)
        self.log_table_dialog.show()
        self.log_table_dialog.raise_()
        self.log_table_dialog.activateWindow()

    def _clear_log_from_dialog(self) -> None:
        if not self.log_samples:
            return
        if QMessageBox.question(self, "Clear log", "Clear all samples from the log table?") != QMessageBox.Yes:
            return
        self.clear_log(confirm=False)

    def export_log_csv(self) -> None:
        if not self.log_samples:
            QMessageBox.information(self, "No data", "No samples available for CSV export.")
            return

        default_name = f"ips3608_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path_str, _ = QFileDialog.getSaveFileName(self, "Export CSV", str(Path.cwd() / default_name), "CSV files (*.csv)")
        if not path_str:
            return

        with open(path_str, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "voltage_v", "current_a", "power_w", "temperature_c"])
            for s in self.log_samples:
                w.writerow([
                    s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{s.voltage_v:.2f}",
                    f"{s.current_a:.3f}",
                    f"{s.power_w:.3f}",
                    f"{s.temperature_c:.1f}",
                ])

        QMessageBox.information(self, "Export complete", f"CSV exported successfully:\n{path_str}")
        self._status(f"CSV exported: {path_str}")

    def _handle_communication_error(self, message: str) -> None:
        self.app_state.last_error = message
        self._status(message)
        self.stop_active_routine(silent=True)
        if self.app_state.logging_on:
            self.stop_logging(silent=True)
        self.measure_timer.stop()
        self._set_ui_state(UiState.COMMUNICATION_ERROR)

    def _set_ui_state(self, state: str) -> None:
        self.app_state.ui_state = state
        connected = self.app_state.connected
        output_on = self.app_state.output_on
        logging_on = self.app_state.logging_on

        if state == UiState.DISCONNECTED:
            self.connection_panel.connect_btn.setEnabled(True)
            self.connection_panel.disconnect_btn.setEnabled(False)
            self.connection_panel.set_connection_state("Disconnected", "#ef4444")
            self.output_panel.toggle_btn.setEnabled(False)
            self.output_panel.set_output_state(False)
            self.datalogger_panel.start_btn.setEnabled(False)
            self.datalogger_panel.stop_btn.setEnabled(False)
        elif state == UiState.CONNECTING:
            self.connection_panel.connect_btn.setEnabled(False)
            self.connection_panel.disconnect_btn.setEnabled(False)
            self.connection_panel.set_connection_state("Connecting...", "#eab308")
            self.output_panel.toggle_btn.setEnabled(False)
            self.datalogger_panel.start_btn.setEnabled(False)
            self.datalogger_panel.stop_btn.setEnabled(False)
        elif state == UiState.CONNECTED_OUTPUT_OFF:
            self.connection_panel.connect_btn.setEnabled(False)
            self.connection_panel.disconnect_btn.setEnabled(True)
            self.connection_panel.set_connection_state("Connected", "#22c55e")
            self.output_panel.toggle_btn.setEnabled(True)
            self.output_panel.set_output_state(False)
            self.datalogger_panel.start_btn.setEnabled(not logging_on)
            self.datalogger_panel.stop_btn.setEnabled(logging_on)
        elif state == UiState.CONNECTED_OUTPUT_ON:
            self.connection_panel.connect_btn.setEnabled(False)
            self.connection_panel.disconnect_btn.setEnabled(True)
            self.connection_panel.set_connection_state("Connected", "#22c55e")
            self.output_panel.toggle_btn.setEnabled(True)
            self.output_panel.set_output_state(True)
            self.datalogger_panel.start_btn.setEnabled(not logging_on)
            self.datalogger_panel.stop_btn.setEnabled(logging_on)
        elif state == UiState.COMMUNICATION_ERROR:
            self.connection_panel.connect_btn.setEnabled(not connected)
            self.connection_panel.disconnect_btn.setEnabled(connected)
            self.connection_panel.set_connection_state("Communication error", "#f97316")
            self.output_panel.toggle_btn.setEnabled(False)
            self.datalogger_panel.start_btn.setEnabled(False)
            self.datalogger_panel.stop_btn.setEnabled(False)

        self.act_connect.setEnabled(not connected)
        self.act_disconnect.setEnabled(connected)
        self.act_output_start.setEnabled(connected and not output_on)
        self.act_output_stop.setEnabled(connected and output_on)
        self.act_log_start.setEnabled(connected and not logging_on)
        self.act_log_stop.setEnabled(logging_on)
        self._refresh_status_summary()

    def _refresh_status_summary(self) -> None:
        if self.app_state.ui_state == UiState.COMMUNICATION_ERROR:
            conn = "Communication error"
        elif self.app_state.connected:
            conn = "Connected"
        else:
            conn = "Disconnected"

        output = "Output ON" if self.app_state.output_on else "Output OFF"
        dlog = "ON" if self.app_state.logging_on else "OFF"
        last_data = self.app_state.last_data_ts.strftime("%H:%M:%S") if self.app_state.last_data_ts else "--"

        self.status_panel.set_summary(
            conn,
            f"{output} | Routine {self.active_routine_name}",
            dlog,
            len(self.log_samples),
            last_data,
            self.app_state.last_command,
            self.app_state.last_error,
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.app_state.logging_on:
            res = QMessageBox.question(
                self,
                "Datalogger active",
                "The datalogger is still active. Stop logging and close the application?",
            )
            if res != QMessageBox.Yes:
                event.ignore()
                return
            self.stop_logging(silent=True)

        self.disconnect_device()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow()
    win.show()
    return app.exec()
