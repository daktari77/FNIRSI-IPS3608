#!/usr/bin/env python3
"""IPS3608 Studio: memories + routine window DSL."""

from __future__ import annotations

import re
import struct
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Optional

try:
    import serial
except ImportError as exc:
    raise SystemExit("Missing dependency: pyserial. Install with: pip install pyserial") from exc


CMD_READ = 0xA1
CMD_WRITE_BYTE = 0xB1
CMD_CONNECT = 0xC1

REG_SET_VOLT = 0xC1
REG_SET_CURR = 0xC2
REG_LIVE = 0xC3
REG_TEMP = 0xC4
REG_OTP_LIMIT = 0xD4
REG_OUTPUT = 0xDB


def preset_registers(slot: int) -> tuple[int, int]:
    # Slot 1..6 -> V: C5,C7,C9,CB,CD,CF and I next register.
    if slot < 1 or slot > 6:
        raise ValueError("Memory slot must be in range 1..6")
    reg_v = 0xC3 + 2 * slot
    reg_i = reg_v + 1
    return reg_v, reg_i


@dataclass
class RoutineStep:
    voltage: float
    current: float
    temperature: float
    duration_s: float
    output_on: bool = True


class IPS3608:
    def __init__(self, port: str, baud: int = 9600, timeout: float = 0.2) -> None:
        self._ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout,
            write_timeout=1.0,
            rtscts=False,
            dsrdtr=False,
        )
        self._ser.dtr = True
        self._ser.rts = True

    def close(self) -> None:
        if self._ser.is_open:
            self.send(CMD_CONNECT, 0x00, b"\x00")
            time.sleep(0.05)
            self._ser.close()

    def send(self, cmd_type: int, register: int, data: bytes) -> bytes:
        packet = self._make_cmd(cmd_type, register, data)
        self._ser.write(packet)
        self._ser.flush()
        return packet

    @staticmethod
    def _make_cmd(cmd_type: int, register: int, data: bytes) -> bytes:
        length = len(data)
        checksum = (register + length + sum(data)) & 0xFF
        return bytes([0xF1, cmd_type, register, length]) + data + bytes([checksum])

    def connect(self) -> None:
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        self.send(CMD_CONNECT, 0x00, b"\x01")
        time.sleep(0.1)

    def read_frames(self, timeout_s: float = 0.7) -> list[bytes]:
        deadline = time.monotonic() + timeout_s
        buf = bytearray()
        out: list[bytes] = []

        while time.monotonic() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                buf.extend(chunk)
                while True:
                    if len(buf) < 5:
                        break
                    if buf[0] != 0xF0:
                        del buf[0]
                        continue
                    frame_len = 5 + buf[3]
                    if len(buf) < frame_len:
                        break
                    frame = bytes(buf[:frame_len])
                    del buf[:frame_len]
                    if self._valid_checksum(frame):
                        out.append(frame)
            else:
                time.sleep(0.01)

        return out

    @staticmethod
    def _valid_checksum(frame: bytes) -> bool:
        if len(frame) < 5 or frame[0] != 0xF0:
            return False
        reg = frame[2]
        ln = frame[3]
        payload = frame[4 : 4 + ln]
        cs = frame[4 + ln]
        return ((reg + ln + sum(payload)) & 0xFF) == cs

    def set_voltage(self, volts: float) -> None:
        self.send(CMD_WRITE_BYTE, REG_SET_VOLT, struct.pack("<f", volts))

    def set_current(self, amps: float) -> None:
        self.send(CMD_WRITE_BYTE, REG_SET_CURR, struct.pack("<f", amps))

    def set_temperature_limit(self, temp_c: float) -> None:
        self.send(CMD_WRITE_BYTE, REG_OTP_LIMIT, struct.pack("<f", temp_c))

    def output(self, on: bool) -> None:
        self.send(CMD_WRITE_BYTE, REG_OUTPUT, bytes([1 if on else 0]))

    def write_preset(self, slot: int, volts: float, amps: float) -> None:
        reg_v, reg_i = preset_registers(slot)
        self.send(CMD_WRITE_BYTE, reg_v, struct.pack("<f", volts))
        time.sleep(0.03)
        self.send(CMD_WRITE_BYTE, reg_i, struct.pack("<f", amps))

    def read_float_register(self, register: int) -> Optional[float]:
        self.send(CMD_READ, register, b"\x00")
        for frame in self.read_frames(0.5):
            if len(frame) >= 9 and frame[2] == register and frame[3] == 0x04:
                return struct.unpack("<f", frame[4:8])[0]
        return None

    def read_preset(self, slot: int) -> Optional[tuple[float, float]]:
        reg_v, reg_i = preset_registers(slot)
        v = self.read_float_register(reg_v)
        i = self.read_float_register(reg_i)
        if v is None or i is None:
            return None
        return (v, i)

    def read_live(self) -> Optional[tuple[float, float, float]]:
        self.send(CMD_READ, REG_LIVE, b"\x00")
        for frame in self.read_frames(0.6):
            if len(frame) >= 17 and frame[2] == REG_LIVE and frame[3] == 0x0C:
                payload = frame[4:16]
                return (
                    struct.unpack("<f", payload[0:4])[0],
                    struct.unpack("<f", payload[4:8])[0],
                    struct.unpack("<f", payload[8:12])[0],
                )
        return None

    def read_temp(self) -> Optional[float]:
        self.send(CMD_READ, REG_TEMP, b"\x00")
        for frame in self.read_frames(0.4):
            if len(frame) >= 9 and frame[2] == REG_TEMP and frame[3] == 0x04:
                return struct.unpack("<f", frame[4:8])[0]
        return None


class RoutineWindow(tk.Toplevel):
    """Separate window for routine definition and execution."""

    HELP_TEXT = (
        "One step per line.\n"
        "Syntax 1: V=3 I=1 T=60 DUR=10\n"
        "Syntax 2: 3V 10s (uses current I/T fields from main window)\n"
        "Optional: OUT=OFF for a step with output disabled\n"
    )

    def __init__(self, master: "StudioApp") -> None:
        super().__init__(master)
        self.master_app = master
        self.title("Routine Studio")
        self.geometry("760x520")

        self.steps: list[RoutineStep] = []
        self.running = False
        self.current_index = -1
        self.step_started_at = 0.0
        self.job: Optional[str] = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        top = ttk.LabelFrame(frame, text="DSL", padding=8)
        top.pack(fill="both", expand=True)

        self.txt = tk.Text(top, height=18, font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True)
        self.txt.insert(
            "1.0",
            "# Example\n"
            "V=3 I=1 T=60 DUR=10\n"
            "V=4 I=1 T=60 DUR=5\n"
            "V=2 I=1 T=60 DUR=1\n",
        )

        bottom = ttk.Frame(frame)
        bottom.pack(fill="x", pady=(8, 0))

        ttk.Label(bottom, text=self.HELP_TEXT, justify="left").grid(row=0, column=0, rowspan=2, sticky="w")

        ttk.Button(bottom, text="Validate", command=self.on_validate).grid(row=0, column=1, padx=6)
        ttk.Button(bottom, text="Run", command=self.on_run).grid(row=0, column=2, padx=6)
        ttk.Button(bottom, text="Stop", command=self.on_stop).grid(row=0, column=3, padx=6)

        self.state_var = tk.StringVar(value="Idle")
        ttk.Label(bottom, textvariable=self.state_var).grid(row=1, column=1, columnspan=3, sticky="w", padx=6)

    def _parse(self) -> list[RoutineStep]:
        text = self.txt.get("1.0", "end").splitlines()
        steps: list[RoutineStep] = []

        default_i = float(self.master_app.i_set_var.get())
        default_t = float(self.master_app.t_set_var.get())

        for line_no, raw in enumerate(text, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            m_simple = re.match(r"^(\d+(?:\.\d+)?)V\s+(\d+(?:\.\d+)?)s$", line, re.IGNORECASE)
            if m_simple:
                v = float(m_simple.group(1))
                dur = float(m_simple.group(2))
                steps.append(RoutineStep(v, default_i, default_t, dur, True))
                continue

            pairs = dict((k.upper(), val) for k, val in re.findall(r"([A-Za-z]+)\s*=\s*([^\s]+)", line))
            if not pairs:
                raise ValueError(f"Line {line_no}: invalid syntax")

            try:
                v = float(pairs.get("V", "nan"))
                i = float(pairs.get("I", default_i))
                t = float(pairs.get("T", default_t))
                dur = float(pairs.get("DUR", pairs.get("S", "nan")))
            except ValueError as exc:
                raise ValueError(f"Line {line_no}: invalid number") from exc

            out_raw = pairs.get("OUT", "ON").strip().upper()
            output_on = out_raw not in ("OFF", "0", "FALSE")

            if not (0.0 <= v <= 36.0):
                raise ValueError(f"Line {line_no}: V out of range")
            if not (0.0 <= i <= 8.2):
                raise ValueError(f"Line {line_no}: I out of range")
            if not (0.0 <= t <= 99.0):
                raise ValueError(f"Line {line_no}: T out of range")
            if dur <= 0:
                raise ValueError(f"Line {line_no}: DUR must be > 0")

            steps.append(RoutineStep(v, i, t, dur, output_on))

        if not steps:
            raise ValueError("No steps defined")

        return steps

    def on_validate(self) -> None:
        try:
            self.steps = self._parse()
            total = sum(s.duration_s for s in self.steps)
            self.state_var.set(f"Valid: {len(self.steps)} step(s), total {total:.1f}s")
        except Exception as exc:
            self.state_var.set(f"Invalid: {exc}")
            messagebox.showerror("Routine validation", str(exc), parent=self)

    def on_run(self) -> None:
        if self.running:
            return
        if not self.master_app.ensure_connected():
            return
        try:
            self.steps = self._parse()
        except Exception as exc:
            messagebox.showerror("Routine parse", str(exc), parent=self)
            return

        self.running = True
        self.current_index = -1
        self.state_var.set("Running")
        self._start_next_step()

    def _start_next_step(self) -> None:
        if not self.running:
            return

        self.current_index += 1
        if self.current_index >= len(self.steps):
            self.running = False
            self.state_var.set("Completed")
            self.master_app.safe_stop_output()
            return

        step = self.steps[self.current_index]
        try:
            self.master_app.apply_values(step.voltage, step.current, step.temperature)
            self.master_app.set_output(step.output_on)
        except Exception as exc:
            self.running = False
            self.state_var.set(f"Fault: {exc}")
            self.master_app.safe_stop_output()
            messagebox.showerror("Routine run", str(exc), parent=self)
            return

        self.step_started_at = time.monotonic()
        self.state_var.set(
            f"Step {self.current_index + 1}/{len(self.steps)}: "
            f"V={step.voltage:.3f} I={step.current:.3f} T={step.temperature:.1f} "
            f"for {step.duration_s:.2f}s"
        )
        self.job = self.after(100, self._tick)

    def _tick(self) -> None:
        if not self.running or self.current_index < 0:
            return

        step = self.steps[self.current_index]
        elapsed = time.monotonic() - self.step_started_at
        if elapsed >= step.duration_s:
            self._start_next_step()
            return
        self.job = self.after(100, self._tick)

    def on_stop(self) -> None:
        self.running = False
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        self.master_app.safe_stop_output()
        self.state_var.set("Stopped")

    def _on_close(self) -> None:
        self.on_stop()
        self.destroy()


class StudioApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IPS3608 Studio")
        self.resizable(False, False)

        self.dev: Optional[IPS3608] = None
        self.auto_refresh_job: Optional[str] = None
        self.routine_window: Optional[RoutineWindow] = None

        self.port_var = tk.StringVar(value="COM13")
        self.baud_var = tk.StringVar(value="9600")

        self.v_set_var = tk.StringVar(value="3.0")
        self.i_set_var = tk.StringVar(value="1.0")
        self.t_set_var = tk.StringVar(value="60.0")

        self.memory_slot_var = tk.StringVar(value="1")
        self.memory_cache: dict[int, tuple[float, float]] = {}

        self.v_meas_var = tk.StringVar(value="-")
        self.i_meas_var = tk.StringVar(value="-")
        self.p_meas_var = tk.StringVar(value="-")
        self.t_meas_var = tk.StringVar(value="-")

        self.status_var = tk.StringVar(value="Disconnected")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        conn = ttk.LabelFrame(main, text="Connection", padding=8)
        conn.grid(row=0, column=0, sticky="ew")
        ttk.Label(conn, text="Port").grid(row=0, column=0, sticky="w")
        ttk.Entry(conn, textvariable=self.port_var, width=9).grid(row=0, column=1, padx=(6, 10))
        ttk.Label(conn, text="Baud").grid(row=0, column=2, sticky="w")
        ttk.Entry(conn, textvariable=self.baud_var, width=9).grid(row=0, column=3, padx=(6, 10))
        ttk.Button(conn, text="Connect", command=self.on_connect).grid(row=0, column=4, padx=4)
        ttk.Button(conn, text="Disconnect", command=self.on_disconnect).grid(row=0, column=5, padx=4)

        setp = ttk.LabelFrame(main, text="Set Parameters", padding=8)
        setp.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(setp, text="V").grid(row=0, column=0)
        ttk.Entry(setp, textvariable=self.v_set_var, width=9).grid(row=0, column=1, padx=6)
        ttk.Label(setp, text="I").grid(row=0, column=2)
        ttk.Entry(setp, textvariable=self.i_set_var, width=9).grid(row=0, column=3, padx=6)
        ttk.Label(setp, text="T OTP").grid(row=0, column=4)
        ttk.Entry(setp, textvariable=self.t_set_var, width=9).grid(row=0, column=5, padx=6)
        ttk.Button(setp, text="Apply V/I/T", command=self.on_apply).grid(row=0, column=6, padx=6)

        mem = ttk.LabelFrame(main, text="Internal Memories (1..6)", padding=8)
        mem.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(mem, text="Slot").grid(row=0, column=0)
        ttk.Combobox(mem, textvariable=self.memory_slot_var, values=[str(i) for i in range(1, 7)], width=5, state="readonly").grid(row=0, column=1, padx=6)
        ttk.Button(mem, text="Save Current -> Slot", command=self.on_save_memory).grid(row=0, column=2, padx=4)
        ttk.Button(mem, text="Load Slot -> Set", command=self.on_load_memory).grid(row=0, column=3, padx=4)

        out = ttk.LabelFrame(main, text="Output + Routine", padding=8)
        out.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(out, text="START", command=self.on_start).grid(row=0, column=0, padx=4)
        ttk.Button(out, text="STOP", command=self.on_stop).grid(row=0, column=1, padx=4)
        ttk.Button(out, text="Read Now", command=self.on_read_now).grid(row=0, column=2, padx=8)
        ttk.Button(out, text="Auto 1s", command=self.toggle_auto_refresh).grid(row=0, column=3, padx=4)
        ttk.Button(out, text="Open Routine Studio", command=self.on_open_routine).grid(row=0, column=4, padx=(16, 4))

        meas = ttk.LabelFrame(main, text="Live Readings", padding=8)
        meas.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(meas, text="V").grid(row=0, column=0)
        ttk.Label(meas, textvariable=self.v_meas_var, width=12).grid(row=0, column=1, padx=(4, 12))
        ttk.Label(meas, text="I").grid(row=0, column=2)
        ttk.Label(meas, textvariable=self.i_meas_var, width=12).grid(row=0, column=3, padx=(4, 12))
        ttk.Label(meas, text="P").grid(row=0, column=4)
        ttk.Label(meas, textvariable=self.p_meas_var, width=12).grid(row=0, column=5, padx=(4, 12))
        ttk.Label(meas, text="T").grid(row=0, column=6)
        ttk.Label(meas, textvariable=self.t_meas_var, width=12).grid(row=0, column=7, padx=(4, 0))

        status = ttk.LabelFrame(main, text="Status", padding=8)
        status.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(status, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def ensure_connected(self) -> bool:
        if self.dev is None:
            messagebox.showwarning("Not connected", "Connect to the power supply first.")
            return False
        return True

    def on_connect(self) -> None:
        if self.dev is not None:
            self._set_status("Already connected")
            return
        try:
            baud = int(self.baud_var.get())
            dev = IPS3608(self.port_var.get().strip(), baud)
            dev.connect()
            self.dev = dev
            self._set_status(f"Connected to {self.port_var.get().strip()} @ {baud}")
            self.on_read_now()
        except Exception as exc:
            self.dev = None
            messagebox.showerror("Connect error", str(exc))
            self._set_status("Connection failed")

    def on_disconnect(self) -> None:
        self._stop_auto_refresh()
        if self.dev is None:
            self._set_status("Already disconnected")
            return
        try:
            self.dev.close()
        except Exception:
            pass
        self.dev = None
        self._set_status("Disconnected")

    def apply_values(self, v: float, i: float, t: float) -> None:
        if not self.ensure_connected():
            raise RuntimeError("Device not connected")
        if not (0.0 <= v <= 36.0):
            raise ValueError("V out of range (0..36)")
        if not (0.0 <= i <= 8.2):
            raise ValueError("I out of range (0..8.2)")
        if not (0.0 <= t <= 99.0):
            raise ValueError("T out of range (0..99)")

        assert self.dev is not None
        self.dev.set_voltage(v)
        time.sleep(0.03)
        self.dev.set_current(i)
        time.sleep(0.03)
        self.dev.set_temperature_limit(t)

        self.v_set_var.set(f"{v:.3f}")
        self.i_set_var.set(f"{i:.3f}")
        self.t_set_var.set(f"{t:.1f}")

    def set_output(self, on: bool) -> None:
        if not self.ensure_connected():
            raise RuntimeError("Device not connected")
        assert self.dev is not None
        self.dev.output(on)
        self._set_status("Output START" if on else "Output STOP")

    def safe_stop_output(self) -> None:
        try:
            if self.dev is not None:
                self.dev.output(False)
        except Exception:
            pass

    def on_apply(self) -> None:
        try:
            self.apply_values(float(self.v_set_var.get()), float(self.i_set_var.get()), float(self.t_set_var.get()))
            self._set_status("Applied V/I/T")
        except Exception as exc:
            messagebox.showerror("Apply error", str(exc))

    def on_start(self) -> None:
        try:
            self.set_output(True)
        except Exception as exc:
            messagebox.showerror("Start error", str(exc))

    def on_stop(self) -> None:
        try:
            self.set_output(False)
        except Exception as exc:
            messagebox.showerror("Stop error", str(exc))

    def on_save_memory(self) -> None:
        if not self.ensure_connected():
            return
        try:
            slot = int(self.memory_slot_var.get())
            v = float(self.v_set_var.get())
            i = float(self.i_set_var.get())
            if not (0.0 <= v <= 36.0) or not (0.0 <= i <= 8.2):
                raise ValueError("V/I out of range")
            assert self.dev is not None
            self.dev.write_preset(slot, v, i)
            self.memory_cache[slot] = (v, i)
            self._set_status(f"Saved memory slot {slot}: V={v:.3f}, I={i:.3f}")
        except Exception as exc:
            messagebox.showerror("Memory save", str(exc))

    def on_load_memory(self) -> None:
        if not self.ensure_connected():
            return
        try:
            slot = int(self.memory_slot_var.get())
            assert self.dev is not None
            values = self.dev.read_preset(slot)
            if values is None:
                values = self.memory_cache.get(slot)
            if values is None:
                raise RuntimeError("Unable to read memory slot from device")
            v, i = values
            self.v_set_var.set(f"{v:.3f}")
            self.i_set_var.set(f"{i:.3f}")
            self._set_status(f"Loaded slot {slot} into set fields")
        except Exception as exc:
            messagebox.showerror("Memory load", str(exc))

    def on_read_now(self) -> None:
        if not self.ensure_connected():
            return
        try:
            assert self.dev is not None
            live = self.dev.read_live()
            temp = self.dev.read_temp()

            if live is None:
                self.v_meas_var.set("n/a")
                self.i_meas_var.set("n/a")
                self.p_meas_var.set("n/a")
            else:
                v, i, p = live
                self.v_meas_var.set(f"{v:.3f} V")
                self.i_meas_var.set(f"{i:.3f} A")
                self.p_meas_var.set(f"{p:.3f} W")

            self.t_meas_var.set("n/a" if temp is None else f"{temp:.2f} C")
            self._set_status("Read complete")
        except Exception as exc:
            messagebox.showerror("Read error", str(exc))

    def toggle_auto_refresh(self) -> None:
        if self.auto_refresh_job is None:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _start_auto_refresh(self) -> None:
        if not self.ensure_connected():
            return
        self._set_status("Auto refresh ON")
        self._auto_refresh_tick()

    def _stop_auto_refresh(self) -> None:
        if self.auto_refresh_job is not None:
            self.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
            self._set_status("Auto refresh OFF")

    def _auto_refresh_tick(self) -> None:
        self.on_read_now()
        self.auto_refresh_job = self.after(1000, self._auto_refresh_tick)

    def on_open_routine(self) -> None:
        if self.routine_window is not None and self.routine_window.winfo_exists():
            self.routine_window.lift()
            self.routine_window.focus_force()
            return
        self.routine_window = RoutineWindow(self)

    def _on_close(self) -> None:
        self._stop_auto_refresh()
        if self.routine_window is not None and self.routine_window.winfo_exists():
            self.routine_window.on_stop()
            self.routine_window.destroy()
        self.on_disconnect()
        self.destroy()


if __name__ == "__main__":
    app = StudioApp()
    app.mainloop()
