#!/usr/bin/env python3
"""Minimal FNIRSI IPS3608 CLI over serial protocol."""

from __future__ import annotations

import argparse
import struct
import sys
import time
from typing import Iterable, Optional

try:
    import serial
except ImportError:
    print("Missing dependency: pyserial. Install with: pip install pyserial", file=sys.stderr)
    sys.exit(2)


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


def cmd_live(dev: IPS3608, interval: float, count: int) -> int:
    print("Time       Voltage(V)  Current(A)  Power(W)  Temp(C)")
    print("---------------------------------------------------")
    i = 0
    while count <= 0 or i < count:
        i += 1
        live = dev.read_live()
        temp = dev.read_temp()
        ts = time.strftime("%H:%M:%S")
        if live is None:
            print(f"{ts}   n/a         n/a         n/a       {temp if temp is not None else 'n/a'}")
        else:
            v, a, w = live
            t = f"{temp:7.2f}" if temp is not None else "   n/a "
            print(f"{ts}   {v:9.3f}  {a:10.3f}  {w:8.3f}  {t}")
        time.sleep(interval)
    return 0


def cmd_set(dev: IPS3608, volts: float, amps: float, temp_c: Optional[float]) -> int:
    if not (0.0 <= volts <= 36.0):
        print("Voltage out of range (0..36V)", file=sys.stderr)
        return 2
    if not (0.0 <= amps <= 8.2):
        print("Current out of range (0..8.2A)", file=sys.stderr)
        return 2
    if temp_c is not None and not (0.0 <= temp_c <= 99.0):
        print("Temperature limit out of range (0..99C)", file=sys.stderr)
        return 2

    dev.set_voltage(volts)
    time.sleep(0.05)
    dev.set_current(amps)

    if temp_c is not None:
        time.sleep(0.05)
        dev.set_temperature_limit(temp_c)
        print(f"Setpoints updated: {volts:.3f} V, {amps:.3f} A, OTP {temp_c:.1f} C")
    else:
        print(f"Setpoints updated: {volts:.3f} V, {amps:.3f} A")

    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FNIRSI IPS3608 serial CLI")
    p.add_argument("--port", default="COM13", help="Serial port (default: COM13)")
    p.add_argument("--baud", type=int, default=9600, help="Baud rate (default: 9600)")

    sp = p.add_subparsers(dest="cmd", required=True)

    live = sp.add_parser("live", help="Read live V/A/W in loop")
    live.add_argument("--interval", type=float, default=0.5, help="Seconds between reads")
    live.add_argument("--count", type=int, default=20, help="Number of samples, <=0 means forever")

    setp = sp.add_parser("set", help="Set voltage/current and optional temperature limit")
    setp.add_argument("voltage", type=float)
    setp.add_argument("current", type=float)
    setp.add_argument("temperature", type=float, nargs="?", help="Optional OTP limit in C (0..99)")

    sp.add_parser("on", help="Enable output")
    sp.add_parser("off", help="Disable output")
    sp.add_parser("start", help="Enable output (RUN/STOP -> RUN)")
    sp.add_parser("stop", help="Disable output (RUN/STOP -> STOP)")
    sp.add_parser("status", help="Single live read")

    return p.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    dev = IPS3608(args.port, args.baud)
    try:
        dev.connect()

        if args.cmd == "live":
            return cmd_live(dev, args.interval, args.count)
        if args.cmd == "set":
            return cmd_set(dev, args.voltage, args.current, args.temperature)
        if args.cmd in ("on", "start"):
            dev.output(True)
            print("Output enabled")
            return 0
        if args.cmd in ("off", "stop"):
            dev.output(False)
            print("Output disabled")
            return 0
        if args.cmd == "status":
            live = dev.read_live()
            temp = dev.read_temp()
            if live is None:
                print("No live response")
                return 1
            v, a, w = live
            if temp is None:
                print(f"V={v:.3f}V  I={a:.3f}A  P={w:.3f}W")
            else:
                print(f"V={v:.3f}V  I={a:.3f}A  P={w:.3f}W  T={temp:.2f}C")
            return 0

        return 2
    finally:
        dev.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
