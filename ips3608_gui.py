#!/usr/bin/env python3
"""Mini GUI for FNIRSI IPS3608 (V/I/T + Start/Stop)."""

from __future__ import annotations

import struct
import time
import tkinter as tk
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

    def read_live(self) -> Optional[tuple[float, float, float]]:
        self.send(CMD_READ, REG_LIVE, b"\x00")
        for f in self.read_frames(0.6):
            if len(f) >= 17 and f[1] == CMD_READ and f[2] == REG_LIVE and f[3] == 0x0C:
                p = f[4:16]
                return (
                    struct.unpack("<f", p[0:4])[0],
                    struct.unpack("<f", p[4:8])[0],
                    struct.unpack("<f", p[8:12])[0],
                )
        return None

    def read_temp(self) -> Optional[float]:
        self.send(CMD_READ, REG_TEMP, b"\x00")
        for f in self.read_frames(0.4):
            if len(f) >= 9 and f[1] == CMD_READ and f[2] == REG_TEMP and f[3] == 0x04:
                return struct.unpack("<f", f[4:8])[0]
        return None


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("IPS3608 Mini GUI")
        self.resizable(False, False)

        self.dev: Optional[IPS3608] = None
        self.auto_refresh_job: Optional[str] = None

        self.port_var = tk.StringVar(value="COM13")
        self.baud_var = tk.StringVar(value="9600")

        self.v_set_var = tk.StringVar(value="3.0")
        self.i_set_var = tk.StringVar(value="1.0")
        self.t_set_var = tk.StringVar(value="60.0")

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
        ttk.Entry(conn, textvariable=self.port_var, width=10).grid(row=0, column=1, padx=(6, 14))

        ttk.Label(conn, text="Baud").grid(row=0, column=2, sticky="w")
        ttk.Entry(conn, textvariable=self.baud_var, width=10).grid(row=0, column=3, padx=(6, 14))

        ttk.Button(conn, text="Connect", command=self.on_connect).grid(row=0, column=4, padx=(0, 6))
        ttk.Button(conn, text="Disconnect", command=self.on_disconnect).grid(row=0, column=5)

        setp = ttk.LabelFrame(main, text="Set Parameters", padding=8)
        setp.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ttk.Label(setp, text="V (0..36)").grid(row=0, column=0, sticky="w")
        ttk.Entry(setp, textvariable=self.v_set_var, width=10).grid(row=0, column=1, padx=(6, 14))

        ttk.Label(setp, text="I (0..8.2)").grid(row=0, column=2, sticky="w")
        ttk.Entry(setp, textvariable=self.i_set_var, width=10).grid(row=0, column=3, padx=(6, 14))

        ttk.Label(setp, text="T OTP (0..99)").grid(row=0, column=4, sticky="w")
        ttk.Entry(setp, textvariable=self.t_set_var, width=10).grid(row=0, column=5, padx=(6, 14))

        ttk.Button(setp, text="Apply V/I/T", command=self.on_apply).grid(row=0, column=6)

        out = ttk.LabelFrame(main, text="Output Control", padding=8)
        out.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ttk.Button(out, text="START", command=self.on_start).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(out, text="STOP", command=self.on_stop).grid(row=0, column=1, padx=(0, 16))
        ttk.Button(out, text="Read Now", command=self.on_read_now).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(out, text="Auto 1s", command=self.toggle_auto_refresh).grid(row=0, column=3)

        meas = ttk.LabelFrame(main, text="Live Readings", padding=8)
        meas.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        ttk.Label(meas, text="V").grid(row=0, column=0, sticky="w")
        ttk.Label(meas, textvariable=self.v_meas_var, width=10).grid(row=0, column=1, sticky="w", padx=(6, 16))

        ttk.Label(meas, text="I").grid(row=0, column=2, sticky="w")
        ttk.Label(meas, textvariable=self.i_meas_var, width=10).grid(row=0, column=3, sticky="w", padx=(6, 16))

        ttk.Label(meas, text="P").grid(row=0, column=4, sticky="w")
        ttk.Label(meas, textvariable=self.p_meas_var, width=10).grid(row=0, column=5, sticky="w", padx=(6, 16))

        ttk.Label(meas, text="T").grid(row=0, column=6, sticky="w")
        ttk.Label(meas, textvariable=self.t_meas_var, width=10).grid(row=0, column=7, sticky="w", padx=(6, 0))

        status = ttk.LabelFrame(main, text="Status", padding=8)
        status.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(status, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _ensure_connected(self) -> bool:
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

    def on_apply(self) -> None:
        if not self._ensure_connected():
            return
        try:
            v = float(self.v_set_var.get())
            i = float(self.i_set_var.get())
            t = float(self.t_set_var.get())
            if not (0.0 <= v <= 36.0):
                raise ValueError("V out of range (0..36)")
            if not (0.0 <= i <= 8.2):
                raise ValueError("I out of range (0..8.2)")
            if not (0.0 <= t <= 99.0):
                raise ValueError("T out of range (0..99)")

            assert self.dev is not None
            self.dev.set_voltage(v)
            time.sleep(0.05)
            self.dev.set_current(i)
            time.sleep(0.05)
            self.dev.set_temperature_limit(t)
            self._set_status(f"Applied V={v:.3f}, I={i:.3f}, T={t:.1f}")
        except Exception as exc:
            messagebox.showerror("Set error", str(exc))

    def on_start(self) -> None:
        if not self._ensure_connected():
            return
        try:
            assert self.dev is not None
            self.dev.output(True)
            self._set_status("Output START")
        except Exception as exc:
            messagebox.showerror("Start error", str(exc))

    def on_stop(self) -> None:
        if not self._ensure_connected():
            return
        try:
            assert self.dev is not None
            self.dev.output(False)
            self._set_status("Output STOP")
        except Exception as exc:
            messagebox.showerror("Stop error", str(exc))

    def on_read_now(self) -> None:
        if not self._ensure_connected():
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

            if temp is None:
                self.t_meas_var.set("n/a")
            else:
                self.t_meas_var.set(f"{temp:.2f} C")

            self._set_status("Read complete")
        except Exception as exc:
            messagebox.showerror("Read error", str(exc))

    def toggle_auto_refresh(self) -> None:
        if self.auto_refresh_job is None:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _start_auto_refresh(self) -> None:
        if not self._ensure_connected():
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

    def _on_close(self) -> None:
        self._stop_auto_refresh()
        self.on_disconnect()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
