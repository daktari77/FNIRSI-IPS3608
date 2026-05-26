from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Optional

from .models import DeviceConfig, Measurement
from .serial_commands import (
    CMD_READ,
    REG_LIVE,
    REG_TEMP,
    cmd_connect,
    cmd_output,
    cmd_read_live,
    cmd_read_temp,
    cmd_set_current,
    cmd_set_voltage,
    extract_frames,
    parse_live_payload,
    parse_temp_payload,
)

try:
    import serial
except ImportError as exc:
    raise SystemExit("Missing dependency: pyserial. Install with: pip install pyserial") from exc


class IPS3608Client:
    def __init__(self, config: DeviceConfig):
        self.config = config
        self._ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._last_temp_c: Optional[float] = None

    def connect(self) -> bool:
        try:
            self._ser = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits,
                timeout=self.config.timeout,
                write_timeout=1.0,
                rtscts=False,
                dsrdtr=False,
            )
            self._ser.dtr = True
            self._ser.rts = True
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
            self._send_packet_obj(cmd_connect(True))
            time.sleep(0.1)
            return True
        except Exception as exc:
            self.disconnect()
            raise RuntimeError(f"Connection failed: {exc}") from exc

    def disconnect(self) -> None:
        if self._ser is None:
            return
        try:
            if self._ser.is_open:
                try:
                    self._send_packet_obj(cmd_connect(False))
                    time.sleep(0.05)
                except Exception:
                    pass
                self._ser.close()
        finally:
            self._ser = None

    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def read_measurements(self) -> Measurement:
        self._ensure_connected()

        live = self._query_first_matching_frame(cmd_read_live().to_bytes(), CMD_READ, REG_LIVE, 0.6)
        if live is None:
            raise RuntimeError("Timeout/empty response on live register")
        if live[3] != 0x0C:
            raise RuntimeError("Invalid live response length")

        temp = self._query_first_matching_frame(cmd_read_temp().to_bytes(), CMD_READ, REG_TEMP, 0.6)
        if temp is not None and temp[3] == 0x04:
            temperature_c = parse_temp_payload(temp[4:8])
            self._last_temp_c = temperature_c
        elif self._last_temp_c is not None:
            # Non-fatal: device didn't respond in time, reuse last known temperature.
            temperature_c = self._last_temp_c
        else:
            raise RuntimeError("Timeout/empty response on temperature register (no prior reading available)")

        voltage_v, current_a, _dev_power_w = parse_live_payload(live[4:16])

        return Measurement(
            timestamp=datetime.now(),
            voltage_v=voltage_v,
            current_a=current_a,
            temperature_c=temperature_c,
        )

    def start_output(self) -> None:
        self._send_packet_obj(cmd_output(True))

    def stop_output(self) -> None:
        self._send_packet_obj(cmd_output(False))

    def set_voltage(self, voltage: float) -> None:
        if not 0.0 <= voltage <= 36.0:
            raise ValueError("Voltage out of range (0..36V)")
        self._send_packet_obj(cmd_set_voltage(voltage))

    def set_current(self, current: float) -> None:
        if not 0.0 <= current <= 8.2:
            raise ValueError("Current out of range (0..8.2A)")
        self._send_packet_obj(cmd_set_current(current))

    def _ensure_connected(self) -> None:
        if not self.is_connected():
            raise RuntimeError("Device not connected")

    def _send_packet_obj(self, packet_obj) -> None:
        self._ensure_connected()
        assert self._ser is not None
        payload = packet_obj.to_bytes()
        with self._lock:
            try:
                self._ser.write(payload)
                self._ser.flush()
            except Exception as exc:
                raise RuntimeError(f"Write error: {exc}") from exc

    def _query_first_matching_frame(
        self,
        packet: bytes,
        expected_cmd: int,
        expected_reg: int,
        timeout_s: float,
    ) -> Optional[bytes]:
        """Send *packet* and return the first response frame matching
        (expected_cmd, expected_reg), or None on timeout.

        The lock is held for the entire write→read cycle so that no other
        caller (e.g. set_voltage from the main thread) can inject a command
        between the request and the corresponding device response.  The
        maximum hold time equals *timeout_s* (≤ 0.6 s by current callers),
        which is acceptable because disconnect_device() waits for the
        measurement thread before touching the client.
        """
        self._ensure_connected()
        assert self._ser is not None

        deadline = time.monotonic() + timeout_s
        buf = bytearray()

        with self._lock:
            self._ser.write(packet)
            self._ser.flush()

            while time.monotonic() < deadline:
                if not self._ser.is_open:
                    break
                # read() blocks up to config.timeout (0.2 s); no busy-sleep needed.
                chunk = self._ser.read(64)
                if not chunk:
                    continue
                buf.extend(chunk)
                for frame in extract_frames(buf):
                    if frame[1] == expected_cmd and frame[2] == expected_reg:
                        return frame

        return None


class SimulatedIPS3608Client:
    def __init__(self, config: DeviceConfig):
        self.config = config
        self._connected = False
        self._output_on = False
        self._vset = 12.0
        self._iset = 1.5
        self._temp_base = 35.0

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False
        self._output_on = False

    def is_connected(self) -> bool:
        return self._connected

    def read_measurements(self) -> Measurement:
        if not self._connected:
            raise RuntimeError("Device not connected")

        if self._output_on:
            voltage_v = self._vset + random.uniform(-0.10, 0.10)
            current_a = min(self._iset, max(0.0, self._iset * random.uniform(0.35, 1.0)))
            temp_shift = 1.5 + current_a * 1.8
        else:
            voltage_v = random.uniform(0.0, 0.05)
            current_a = 0.0
            temp_shift = -1.0

        self._temp_base += random.uniform(-0.12, 0.12) + temp_shift * 0.02
        self._temp_base = max(30.0, min(50.0, self._temp_base))

        return Measurement(
            timestamp=datetime.now(),
            voltage_v=voltage_v,
            current_a=current_a,
            temperature_c=self._temp_base + random.uniform(-0.3, 0.3),
        )

    def start_output(self) -> None:
        if not self._connected:
            raise RuntimeError("Device not connected")
        self._output_on = True

    def stop_output(self) -> None:
        if not self._connected:
            raise RuntimeError("Device not connected")
        self._output_on = False

    def set_voltage(self, voltage: float) -> None:
        if not self._connected:
            raise RuntimeError("Device not connected")
        if not 0.0 <= voltage <= 36.0:
            raise ValueError("Voltage out of range (0..36V)")
        self._vset = voltage

    def set_current(self, current: float) -> None:
        if not self._connected:
            raise RuntimeError("Device not connected")
        if not 0.0 <= current <= 8.2:
            raise ValueError("Current out of range (0..8.2A)")
        self._iset = current
