from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Optional

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .models import LogSample, Measurement


class ConnectionPanel(QGroupBox):
    connect_requested = Signal(str)
    disconnect_requested = Signal()
    refresh_ports_requested = Signal()

    def __init__(self):
        super().__init__("Connection")

        self.port_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh")
        self.conn_btn = QPushButton("Connect")
        self.status_dot = QLabel("●")
        self.status_label = QLabel("Disconnected")

        row = QHBoxLayout()
        row.addWidget(QLabel("Port:"))
        row.addWidget(self.port_combo, stretch=1)
        row.addWidget(self.refresh_btn)
        row.addWidget(self.conn_btn)

        st = QHBoxLayout()
        st.addWidget(QLabel("Status:"))
        st.addWidget(self.status_dot)
        st.addWidget(self.status_label)
        st.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(st)
        self.status_dot.setStyleSheet("color: #ef4444; font-size: 18px;")

        self.refresh_btn.clicked.connect(self.refresh_ports_requested.emit)
        self.conn_btn.clicked.connect(self._on_conn_btn)

        self._connected = False

    def _on_conn_btn(self):
        if not self._connected:
            self.connect_requested.emit(self.port_combo.currentText().strip())
        else:
            self.disconnect_requested.emit()

    def set_connection_state(self, text: str, color: str) -> None:
        self.status_label.setText(text)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 18px;")
        if text.lower().startswith("connected"):
            self.conn_btn.setText("Disconnect")
            self._connected = True
            self.conn_btn.setStyleSheet("font-weight: 700; background-color: #dcfce7; color: #166534; border: 1px solid #86efac;")
        elif text.lower().startswith("disconnected"):
            self.conn_btn.setText("Connect")
            self._connected = False
            self.conn_btn.setStyleSheet("font-weight: 700; background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;")
        elif text.lower().startswith("connecting"):
            self.conn_btn.setText("Connect")
            self._connected = False
            self.conn_btn.setStyleSheet("font-weight: 700; background-color: #fef9c3; color: #a16207; border: 1px solid #fde047;")
        elif text.lower().startswith("communication error"):
            self.conn_btn.setText("Connect")
            self._connected = False
            self.conn_btn.setStyleSheet("font-weight: 700; background-color: #fed7aa; color: #b45309; border: 1px solid #fb923c;")
        else:
            self.conn_btn.setText("Connect")
            self._connected = False
            self.conn_btn.setStyleSheet("")

    def set_ports(self, ports: list[str], include_simulated: bool) -> None:
        current = self.port_combo.currentText()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        if include_simulated:
            self.port_combo.addItem("SIMULATED")
        for p in ports:
            if p != "SIMULATED":
                self.port_combo.addItem(p)
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)
        self.port_combo.blockSignals(False)

class OutputControlPanel(QGroupBox):
    temperature_limit_changed = Signal(float)
    start_output_requested = Signal()
    stop_output_requested = Signal()
    voltage_changed = Signal(float)
    current_changed = Signal(float)

    def __init__(self):
        super().__init__("Output Control")
        self.output_status = QLabel("Output OFF")
        self.toggle_btn = QPushButton("START OUTPUT")
        self.toggle_btn.setMinimumHeight(40)

        self.vset_spin = QDoubleSpinBox()
        self.vset_spin.setRange(0.0, 36.0)
        self.vset_spin.setDecimals(2)
        self.vset_spin.setSingleStep(0.10)
        self.vset_spin.setValue(12.00)
        self.vset_spin.setSuffix(" V")

        self.iset_spin = QDoubleSpinBox()
        self.iset_spin.setRange(0.0, 8.2)
        self.iset_spin.setDecimals(3)
        self.iset_spin.setSingleStep(0.001)
        self.iset_spin.setValue(1.500)
        self.iset_spin.setSuffix(" A")

        self.temp_limit_spin = QDoubleSpinBox()
        self.temp_limit_spin.setRange(0.0, 100.0)
        self.temp_limit_spin.setDecimals(1)
        self.temp_limit_spin.setSingleStep(0.5)
        self.temp_limit_spin.setValue(60.0)
        self.temp_limit_spin.setSuffix(" °C")

        top = QHBoxLayout()
        top.addWidget(self.output_status)
        top.addStretch(1)
        top.addWidget(self.toggle_btn)

        setpoint_row = QWidget()
        setpoint_layout = QHBoxLayout(setpoint_row)
        setpoint_layout.setContentsMargins(0, 0, 0, 0)
        setpoint_layout.addWidget(QLabel("Vset:"))
        setpoint_layout.addWidget(self.vset_spin)
        setpoint_layout.addSpacing(16)
        setpoint_layout.addWidget(QLabel("Iset:"))
        setpoint_layout.addWidget(self.iset_spin)
        setpoint_layout.addSpacing(16)
        setpoint_layout.addWidget(QLabel("Tmax:"))
        setpoint_layout.addWidget(self.temp_limit_spin)
        setpoint_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(setpoint_row)

        self.toggle_btn.clicked.connect(self._on_toggle)
        self.vset_spin.valueChanged.connect(self.voltage_changed.emit)
        self.iset_spin.valueChanged.connect(self.current_changed.emit)
        self.temp_limit_spin.valueChanged.connect(self.temperature_limit_changed.emit)
        self.set_output_state(False)

    def _on_toggle(self) -> None:
        if self.toggle_btn.text().startswith("START"):
            self.start_output_requested.emit()
        else:
            self.stop_output_requested.emit()

    def set_output_state(self, on: bool) -> None:
        if on:
            self.output_status.setText("Output ON")
            self.output_status.setStyleSheet("color: #166534; font-weight: 700;")
            self.toggle_btn.setText("STOP OUTPUT")
            self.toggle_btn.setStyleSheet("font-weight: 700; background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;")
        else:
            self.output_status.setText("Output OFF")
            self.output_status.setStyleSheet("color: #b91c1c; font-weight: 700;")
            self.toggle_btn.setText("START OUTPUT")
            self.toggle_btn.setStyleSheet("font-weight: 700; background-color: #dcfce7; color: #166534; border: 1px solid #86efac;")


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, sub: str, color: str):
        super().__init__()
        self.setObjectName("MetricCard")
        self.title_lbl = QLabel(title)
        self.value_lbl = QLabel(value)
        self.sub_lbl = QLabel(sub)

        self.title_lbl.setStyleSheet("color: #6b7280; font-size: 12px; font-weight: 600;")
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 34px; font-weight: 800;")
        self.sub_lbl.setStyleSheet("color: #4b5563; font-size: 12px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.sub_lbl)


class RealtimeCardsPanel(QGroupBox):
    def __init__(self):
        super().__init__("Realtime Readings")
        self.max_temp = 0.0
        self.volt_card = MetricCard("VOLTAGE", "0.00 V", "Set: 0.00 V", "#60a5fa")
        self.curr_card = MetricCard("CURRENT", "0.000 A", "Set: 0.000 A", "#34d399")
        self.temp_card = MetricCard("TEMPERATURE", "0.0 C", "Max: 0.0 C", "#f59e0b")
        self.pow_card = MetricCard("POWER", "0.000 W", "V x I", "#f472b6")

        grid = QGridLayout(self)
        grid.addWidget(self.volt_card, 0, 0)
        grid.addWidget(self.curr_card, 0, 1)
        grid.addWidget(self.temp_card, 1, 0)
        grid.addWidget(self.pow_card, 1, 1)

    def update_measurement(self, m: Measurement, vset: float, iset: float) -> None:
        self.max_temp = max(self.max_temp, m.temperature_c)
        self.volt_card.value_lbl.setText(f"{m.voltage_v:.2f} V")
        self.volt_card.sub_lbl.setText(f"Set: {vset:.2f} V")
        self.curr_card.value_lbl.setText(f"{m.current_a:.3f} A")
        self.curr_card.sub_lbl.setText(f"Set: {iset:.3f} A")
        self.temp_card.value_lbl.setText(f"{m.temperature_c:.1f} C")
        self.temp_card.sub_lbl.setText(f"Max: {self.max_temp:.1f} C")
        self.pow_card.value_lbl.setText(f"{m.power_w:.3f} W")


class GraphPanel(QGroupBox):
    def __init__(self):
        super().__init__("Realtime Graphs")
        self.is_paused = False
        self.autoscale_enabled = False
        self.window_seconds = 60
        self.data_times: deque[float] = deque(maxlen=20000)
        self.data_v: deque[float] = deque(maxlen=20000)
        self.data_i: deque[float] = deque(maxlen=20000)
        self.data_t: deque[float] = deque(maxlen=20000)

        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Reset")
        self.autoscale_btn = QPushButton("Autoscale")

        self.window_combo = QComboBox()
        self.window_combo.addItems(["30 s", "60 s", "5 min", "15 min"])

        self.update_combo = QComboBox()
        self.update_combo.addItems(["250 ms", "500 ms", "1 s", "2 s"])
        self.update_combo.setCurrentText("500 ms")

        self.plot_main = pg.PlotWidget(title="V / I vs Time")
        self.plot_main.showGrid(x=True, y=True, alpha=0.25)
        self.plot_main.setLabel("bottom", "Time", units="s")
        self.plot_main.setLabel("left", "Value")
        self.plot_main.addLegend()
        self.plot_main.setYRange(0.0, 40.0, padding=0.0)

        self.curve_v = self.plot_main.plot([], [], pen=pg.mkPen(QColor("#60a5fa"), width=2), name="Voltage (V)")
        self.curve_i = self.plot_main.plot([], [], pen=pg.mkPen(QColor("#34d399"), width=2), name="Current (A)")

        controls = QHBoxLayout()
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.reset_btn)
        controls.addWidget(self.autoscale_btn)
        controls.addWidget(QLabel("Window:"))
        controls.addWidget(self.window_combo)
        controls.addWidget(QLabel("Graph update:"))
        controls.addWidget(self.update_combo)
        controls.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_main)
        layout.addLayout(controls)

        self.pause_btn.clicked.connect(self._toggle_pause)
        self.reset_btn.clicked.connect(self.clear)
        self.autoscale_btn.clicked.connect(self._autoscale)
        self.window_combo.currentTextChanged.connect(self._window_changed)

        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.render)
        self.render_timer.start(500)
        self.update_combo.currentTextChanged.connect(self._update_freq_changed)

    def _toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        self.pause_btn.setText("Resume" if self.is_paused else "Pause")

    def _autoscale(self) -> None:
        self.autoscale_enabled = not self.autoscale_enabled
        self.autoscale_btn.setText("Autoscale ON" if self.autoscale_enabled else "Autoscale")
        self.render()

    def _window_changed(self, value: str) -> None:
        mapping = {"30 s": 30, "60 s": 60, "5 min": 300, "15 min": 900}
        self.window_seconds = mapping.get(value, 60)

    def _update_freq_changed(self, value: str) -> None:
        mapping = {"250 ms": 250, "500 ms": 500, "1 s": 1000, "2 s": 2000}
        self.render_timer.setInterval(mapping.get(value, 500))

    def add_measurement(self, m: Measurement) -> None:
        ts = m.timestamp.timestamp()
        self.data_times.append(ts)
        self.data_v.append(m.voltage_v)
        self.data_i.append(m.current_a)
        self.data_t.append(m.temperature_c)

    def clear(self) -> None:
        self.data_times.clear()
        self.data_v.clear()
        self.data_i.clear()
        self.data_t.clear()
        self.render()

    def render(self) -> None:
        if self.is_paused or not self.data_times:
            return
        now_ts = self.data_times[-1]
        min_ts = now_ts - self.window_seconds

        xs: list[float] = []
        ys_v: list[float] = []
        ys_i: list[float] = []

        for idx, ts in enumerate(self.data_times):
            if ts >= min_ts:
                xs.append(ts - now_ts)
                ys_v.append(max(0.0, self.data_v[idx]))
                ys_i.append(max(0.0, self.data_i[idx]))

        self.curve_v.setData(xs, ys_v)
        self.curve_i.setData(xs, ys_i)
        self.plot_main.setXRange(-self.window_seconds, 0.0, padding=0.01)
        if self.autoscale_enabled and (ys_v or ys_i):
            y_max = max(ys_v + ys_i)
            y_top = min(40.0, max(1.0, y_max * 1.1))
            self.plot_main.setYRange(0.0, y_top, padding=0.0)
        else:
            self.plot_main.setYRange(0.0, 40.0, padding=0.0)


class DataloggerPanel(QGroupBox):
    start_log_requested = Signal()
    stop_log_requested = Signal()
    show_table_requested = Signal()
    export_csv_requested = Signal()

    def __init__(self):
        super().__init__("Datalogger")
        self.status_dot = QLabel("●")
        self.status_label = QLabel("OFF")
        self.running_banner = QLabel("DATALOGGING IN CORSO")
        self.running_banner.setStyleSheet("color: #14532d; background: #dcfce7; padding: 4px 8px; border-radius: 6px; border: 1px solid #86efac;")
        self.running_banner.setVisible(False)

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1 s", "5 s", "10 s", "30 s", "60 s"])

        self.start_btn = QPushButton("START LOG")
        self.stop_btn = QPushButton("STOP LOG")
        self.table_btn = QPushButton("View Log Table")
        self.export_btn = QPushButton("Export CSV")

        self.samples_lbl = QLabel("Samples: 0")
        self.duration_lbl = QLabel("Duration: 00:00:00")
        self.last_lbl = QLabel("Last sample: --")


        head = QHBoxLayout()
        head.addWidget(QLabel("Datalogger:"))
        head.addWidget(self.status_dot)
        head.addWidget(self.status_label)
        head.addWidget(self.running_banner)
        head.addStretch(1)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Interval:"))
        controls.addWidget(self.interval_combo)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.table_btn)
        controls.addWidget(self.export_btn)
        controls.addStretch(1)

        stats = QHBoxLayout()
        stats.addWidget(self.samples_lbl)
        stats.addWidget(QLabel("|"))
        stats.addWidget(self.duration_lbl)
        stats.addWidget(QLabel("|"))
        stats.addWidget(self.last_lbl)
        stats.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(head)
        layout.addLayout(controls)
        layout.addLayout(stats)

        self.start_btn.clicked.connect(self.start_log_requested.emit)
        self.stop_btn.clicked.connect(self.stop_log_requested.emit)
        self.table_btn.clicked.connect(self.show_table_requested.emit)
        self.export_btn.clicked.connect(self.export_csv_requested.emit)

    def interval_seconds(self) -> int:
        mapping = {"1 s": 1, "5 s": 5, "10 s": 10, "30 s": 30, "60 s": 60}
        return mapping.get(self.interval_combo.currentText(), 1)

    def set_logging_state(self, on: bool) -> None:
        if on:
            self.status_label.setText("IN CORSO")
            self.status_dot.setStyleSheet("color: #16a34a; font-size: 18px;")
            self.running_banner.setVisible(True)
        else:
            self.status_label.setText("OFF")
            self.status_dot.setStyleSheet("color: #dc2626; font-size: 18px;")
            self.running_banner.setVisible(False)

    def update_stats(self, samples: int, duration_sec: int, last_sample: Optional[datetime]) -> None:
        hh = duration_sec // 3600
        mm = (duration_sec % 3600) // 60
        ss = duration_sec % 60
        self.samples_lbl.setText(f"Samples: {samples}")
        self.duration_lbl.setText(f"Duration: {hh:02d}:{mm:02d}:{ss:02d}")
        if last_sample is None:
            self.last_lbl.setText("Last sample: --")
        else:
            self.last_lbl.setText(f"Last sample: {last_sample.strftime('%Y-%m-%d %H:%M:%S')}")

    def set_samples(self, samples: list[LogSample]) -> None:
        self.samples_lbl.setText(f"Samples: {len(samples)}")
        if samples:
            self.last_lbl.setText(f"Last sample: {samples[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.last_lbl.setText("Last sample: --")


class StatusLogPanel(QGroupBox):
    def __init__(self):
        super().__init__("Status")
        self.summary_lbl = QLabel("State: Disconnected | Output OFF | Datalogger OFF | Samples: 0 | Last data: --")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_lbl)
        layout.addWidget(self.log_text)

    def set_summary(
        self,
        conn_text: str,
        output_text: str,
        datalogger_text: str,
        sample_count: int,
        last_data: str,
        last_command: str,
        last_error: str,
    ) -> None:
        self.summary_lbl.setText(
            "State: "
            f"{conn_text} | "
            f"{output_text} | "
            f"Datalogger {datalogger_text} | "
            f"Samples: {sample_count} | "
            f"Last data: {last_data} | "
            f"Last cmd: {last_command}"
        )
        if last_error != "--":
            self.summary_lbl.setText(self.summary_lbl.text() + f" | Error: {last_error}")

    def add_log_line(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {message}")
