from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class UiState:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED_OUTPUT_OFF = "CONNECTED_OUTPUT_OFF"
    CONNECTED_OUTPUT_ON = "CONNECTED_OUTPUT_ON"
    COMMUNICATION_ERROR = "COMMUNICATION_ERROR"


class RoutineState:
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


@dataclass
class DeviceConfig:
    port: str
    baudrate: int
    bytesize: int
    parity: str
    stopbits: float
    timeout: float
    command_terminator: str
    response_terminator: str


DEFAULT_DEVICE_CONFIG = DeviceConfig(
    port="",
    baudrate=9600,
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=0.2,
    command_terminator="",
    response_terminator="",
)


@dataclass
class Measurement:
    timestamp: datetime
    voltage_v: float
    current_a: float
    temperature_c: float

    @property
    def power_w(self) -> float:
        return self.voltage_v * self.current_a


# LogSample is a semantic alias for Measurement.
# Both represent a timestamped V/I/T reading; keeping a distinct name in the
# public API (log_samples: list[LogSample]) makes the intent clear without
# duplicating the dataclass definition.
LogSample = Measurement


@dataclass
class AppState:
    mode_simulated: bool = False
    ui_state: str = UiState.DISCONNECTED
    connected: bool = False
    output_on: bool = False
    logging_on: bool = False
    last_command: str = "--"
    last_error: str = "--"
    last_data_ts: Optional[datetime] = None
    selected_port: str = DEFAULT_DEVICE_CONFIG.port
    log_started_at: Optional[datetime] = None


@dataclass
class RoutineStep:
    voltage_v: float
    current_a: float
    duration_s: float
    output_on: bool = True
    otp_limit_c: float = 0.0    # per-step OTP; 0 = disabled
    settle_ms: float = 200.0    # stabilisation time at step start (metadata)
    name: str = ""


@dataclass
class RoutineDefinition:
    name: str
    steps: list[RoutineStep] = field(default_factory=list)
    loops: int = 1              # number of full repetitions; 0 = infinite
    stop_output_on_finish: bool = True
    execution_limit_s: float = 0.0  # deprecated — kept for JSON compatibility

    @property
    def total_step_duration_s(self) -> float:
        return sum(max(0.0, s.duration_s) for s in self.steps)

    @property
    def total_duration_s(self) -> float:
        base = self.total_step_duration_s
        return base * self.loops if self.loops > 0 else float("inf")


@dataclass
class RoutineRuntimeInfo:
    state: str
    loop: int           # current loop index (0-based)
    total_loops: int    # 0 = infinite
    step: int           # current step index (0-based)
    step_name: str
    total_steps: int
    elapsed_step_s: float
    elapsed_total_s: float
    remaining_step_s: float


@dataclass
class MemoryPreset:
    slot_id: str
    label: str = ""
    voltage_v: float = 0.0
    current_a: float = 0.0
    enabled: bool = False

    @property
    def display_name(self) -> str:
        if self.label.strip():
            return f"{self.slot_id} - {self.label.strip()}"
        return self.slot_id
