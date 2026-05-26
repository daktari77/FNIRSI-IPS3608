from __future__ import annotations

import time
from collections import deque
from datetime import datetime
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
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

_DIGIT_FONT = "DSEG7 Classic"


class Sparkline(QWidget):
    """Lightweight single-line trend chart drawn with QPainter."""

    def __init__(self, color: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._data: deque[float] = deque(maxlen=60)
        self._color = QColor(color)
        self.setFixedHeight(28)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def append(self, value: float) -> None:
        self._data.append(value)
        self.update()

    def clear(self) -> None:
        self._data.clear()
        self.update()

    def paintEvent(self, event) -> None:
        if len(self._data) < 2:
            return
        data = list(self._data)
        lo, hi = min(data), max(data)
        span = hi - lo or 1.0
        w, h = self.width(), self.height()
        path = QPainterPath()
        n = len(data)
        for i, v in enumerate(data):
            x = i / (n - 1) * w
            y = h - (v - lo) / span * (h - 4) - 2
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self._color, 1.5))
        painter.drawPath(path)


class MetricCard(QFrame):
    """Realtime metric display with large digit value, delta vs setpoint, and sparkline."""

    def __init__(self, title: str, unit: str, color: str, decimals: int = 2, show_fan: bool = False):
        super().__init__()
        self.setObjectName("MetricCard")
        self._unit = unit
        self._color = color
        self._decimals = decimals
        self._fmt = f"{{:.{decimals}f}}"
        self._show_fan = show_fan

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px; font-weight: 600; letter-spacing: 1px;")

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(self.title_lbl, stretch=1)
        if show_fan:
            self.fan_lbl = QLabel("◌ FAN")
            self.fan_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")
            self.fan_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            title_row.addWidget(self.fan_lbl)

        self.value_lbl = QLabel(self._fmt.format(0.0))
        self.value_lbl.setFont(QFont(_DIGIT_FONT, 42))
        self.value_lbl.setStyleSheet(f"color: {color};")

        self.unit_lbl = QLabel(unit)
        self.unit_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 600;")
        self.unit_lbl.setAlignment(Qt.AlignBottom)

        self.setpoint_lbl = QLabel("")
        self.setpoint_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")

        self.delta_lbl = QLabel("")
        self.delta_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")
        self.delta_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.sparkline = Sparkline(color, self)

        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        value_row.addWidget(self.value_lbl, stretch=1)
        value_row.addWidget(self.unit_lbl)

        info_row = QHBoxLayout()
        info_row.addWidget(self.setpoint_lbl, stretch=1)
        info_row.addWidget(self.delta_lbl)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.addLayout(title_row)
        layout.addLayout(value_row)
        layout.addLayout(info_row)
        layout.addWidget(self.sparkline)

    def set_value(
        self,
        value: float,
        setpoint: Optional[float] = None,
        sub_text: str = "",
        fan_on: Optional[bool] = None,
    ) -> None:
        self.value_lbl.setText(self._fmt.format(value))
        self.sparkline.append(value)

        if setpoint is not None:
            self.setpoint_lbl.setText(f"Set {self._fmt.format(setpoint)} {self._unit}")
            delta = value - setpoint
            sign = "+" if delta >= 0 else ""
            self.delta_lbl.setText(f"Δ {sign}{self._fmt.format(delta)}")
            threshold = max(abs(setpoint) * 0.05, 10 ** -self._decimals)
            ok = abs(delta) <= threshold
            delta_color = "#16A34A" if ok else "#DC2626"
            self.delta_lbl.setStyleSheet(f"color: {delta_color}; font-size: 11px;")
        elif sub_text:
            self.setpoint_lbl.setText(sub_text)
            self.delta_lbl.setText("")

        if self._show_fan and fan_on is not None and hasattr(self, "fan_lbl"):
            if fan_on:
                self.fan_lbl.setText("⊙ FAN")
                self.fan_lbl.setStyleSheet("color: #0B84F3; font-size: 11px; font-weight: 700;")
            else:
                self.fan_lbl.setText("◌ FAN")
                self.fan_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")


_TEMP_EMA_ALPHA = 0.25   # smoothing factor: lower = smoother, higher = more reactive
_TEMP_DISPLAY_INTERVAL_S = 1.0   # temperature display refresh rate


class RealtimeCardsPanel(QGroupBox):
    def __init__(self):
        super().__init__("Realtime Readings")
        self.max_temp = 0.0
        self._temp_ema: float = 0.0
        self._temp_ema_init: bool = False
        self._last_temp_display_mono: float = 0.0

        self.volt_card = MetricCard("VOLTAGE", "V", "#0B84F3", decimals=2)
        self.curr_card = MetricCard("CURRENT", "A", "#00A86B", decimals=3)
        self.temp_card = MetricCard("TEMPERATURE", "°C", "#EF4444", decimals=1, show_fan=True)
        self.pow_card = MetricCard("POWER", "W", "#F59E0B", decimals=3)

        grid = QGridLayout(self)
        grid.setSpacing(8)
        grid.addWidget(self.volt_card, 0, 0)
        grid.addWidget(self.curr_card, 0, 1)
        grid.addWidget(self.temp_card, 1, 0)
        grid.addWidget(self.pow_card, 1, 1)

    def update_measurement(self, m: Measurement, vset: float, iset: float, fan_on: bool = False) -> None:
        # V, I, P update every measurement cycle
        self.volt_card.set_value(m.voltage_v, setpoint=vset)
        self.curr_card.set_value(m.current_a, setpoint=iset)
        self.pow_card.set_value(m.power_w, sub_text=f"{m.voltage_v:.2f} V × {m.current_a:.3f} A")

        # Temperature: EMA smoothing + 1 Hz display rate to avoid digit bounce
        if not self._temp_ema_init:
            self._temp_ema = m.temperature_c
            self._temp_ema_init = True
        else:
            self._temp_ema = _TEMP_EMA_ALPHA * m.temperature_c + (1.0 - _TEMP_EMA_ALPHA) * self._temp_ema

        self.max_temp = max(self.max_temp, self._temp_ema)
        now = time.monotonic()
        if now - self._last_temp_display_mono >= _TEMP_DISPLAY_INTERVAL_S:
            self._last_temp_display_mono = now
            self.temp_card.set_value(
                self._temp_ema,
                sub_text=f"Max {self.max_temp:.1f} °C",
                fan_on=fan_on,
            )


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
        self.status_dot.setStyleSheet("color: #DC2626; font-size: 18px;")

        self.refresh_btn.clicked.connect(self.refresh_ports_requested.emit)
        self.conn_btn.clicked.connect(self._on_conn_btn)

        self._connected = False

    def _on_conn_btn(self) -> None:
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
        self.output_status.setStyleSheet("font-size: 13px; font-weight: 700;")

        self.toggle_btn = QPushButton("▶  START OUTPUT")
        self.toggle_btn.setMinimumHeight(56)
        self.toggle_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))

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
        if "START" in self.toggle_btn.text():
            self.start_output_requested.emit()
        else:
            self.stop_output_requested.emit()

    def set_output_state(self, on: bool) -> None:
        if on:
            self.output_status.setText("Output ON")
            self.output_status.setStyleSheet("color: #16A34A; font-size: 13px; font-weight: 700;")
            self.toggle_btn.setText("■  STOP OUTPUT")
            self.toggle_btn.setStyleSheet(
                "font-weight: 700; font-size: 13px;"
                "background-color: #DC2626; color: #FFFFFF;"
                "border: none; border-radius: 8px;"
            )
        else:
            self.output_status.setText("Output OFF")
            self.output_status.setStyleSheet("color: #DC2626; font-size: 13px; font-weight: 700;")
            self.toggle_btn.setText("▶  START OUTPUT")
            self.toggle_btn.setStyleSheet(
                "font-weight: 700; font-size: 13px;"
                "background-color: #16A34A; color: #FFFFFF;"
                "border: none; border-radius: 8px;"
            )


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
        self.plot_main.setBackground("#FFFFFF")
        self.plot_main.showGrid(x=True, y=True, alpha=0.2)
        self.plot_main.setLabel("bottom", "Time", units="s")
        self.plot_main.setLabel("left", "Value")
        self.plot_main.addLegend()
        self.plot_main.setYRange(0.0, 40.0, padding=0.0)

        self.curve_v = self.plot_main.plot([], [], pen=pg.mkPen(QColor("#0B84F3"), width=2), name="Voltage (V)")
        self.curve_i = self.plot_main.plot([], [], pen=pg.mkPen(QColor("#00A86B"), width=2), name="Current (A)")

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

        times = np.array(self.data_times)
        now_ts = times[-1]
        min_ts = now_ts - self.window_seconds

        # np.searchsorted is O(log n) on the monotonically-increasing timestamp
        # array, vs the previous O(n) Python loop over up to 20 000 points.
        start = int(np.searchsorted(times, min_ts))
        xs = times[start:] - now_ts
        ys_v = np.maximum(0.0, np.array(self.data_v)[start:])
        ys_i = np.maximum(0.0, np.array(self.data_i)[start:])

        self.curve_v.setData(xs, ys_v)
        self.curve_i.setData(xs, ys_i)
        self.plot_main.setXRange(-self.window_seconds, 0.0, padding=0.01)
        if self.autoscale_enabled and len(xs) > 0:
            y_max = float(max(ys_v.max(), ys_i.max()))
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
        self.running_banner.setStyleSheet(
            "color: #14532d; background: #dcfce7; padding: 4px 8px;"
            "border-radius: 6px; border: 1px solid #86efac;"
        )
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
            self.status_dot.setStyleSheet("color: #16A34A; font-size: 18px;")
            self.running_banner.setVisible(True)
        else:
            self.status_label.setText("OFF")
            self.status_dot.setStyleSheet("color: #DC2626; font-size: 18px;")
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
