#!/usr/bin/env python3
"""Lightweight CLI wrapper around the IPS3608 Python library."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from ips3608_app.clients import IPS3608Client, SimulatedIPS3608Client
from ips3608_app.models import DEFAULT_DEVICE_CONFIG, DeviceConfig


def build_device_config(port: str, baudrate: int, timeout: float) -> DeviceConfig:
    return DeviceConfig(
        port=port,
        baudrate=baudrate,
        bytesize=DEFAULT_DEVICE_CONFIG.bytesize,
        parity=DEFAULT_DEVICE_CONFIG.parity,
        stopbits=DEFAULT_DEVICE_CONFIG.stopbits,
        timeout=timeout,
        command_terminator=DEFAULT_DEVICE_CONFIG.command_terminator,
        response_terminator=DEFAULT_DEVICE_CONFIG.response_terminator,
    )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lightweight scripting CLI for the FNIRSI IPS3608."
    )
    parser.add_argument(
        "--port",
        default="",
        help="Serial port path or name (e.g. COM3 or /dev/ttyACM0).",
    )
    parser.add_argument("--baud", type=int, default=9600, help="Serial baud rate.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.2,
        help="Serial read timeout in seconds.",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulated device mode instead of real serial hardware.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show current voltage, current, power, and temperature.")
    subparsers.add_parser("on", help="Enable the output.")
    subparsers.add_parser("off", help="Disable the output.")
    set_parser = subparsers.add_parser("set", help="Set voltage and current.")
    set_parser.add_argument("voltage", type=float, help="Target voltage in volts.")
    set_parser.add_argument("current", type=float, help="Target current in amps.")
    return parser.parse_args(list(argv))


def format_measurement(measurement) -> str:
    return (
        f"{measurement.voltage_v:.3f} V, "
        f"{measurement.current_a:.3f} A, "
        f"{measurement.power_w:.3f} W, "
        f"{measurement.temperature_c:.1f} C"
    )


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if args.simulate:
        config = build_device_config(args.port, args.baud, args.timeout)
        client = SimulatedIPS3608Client(config)
    else:
        if not args.port:
            print("Error: --port is required for real device mode.", file=sys.stderr)
            return 2
        config = build_device_config(args.port, args.baud, args.timeout)
        client = IPS3608Client(config)

    try:
        client.connect()
    except Exception as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "status":
            measurement = client.read_measurements()
            print(format_measurement(measurement))
        elif args.command == "on":
            client.start_output()
            print("Output enabled")
        elif args.command == "off":
            client.stop_output()
            print("Output disabled")
        elif args.command == "set":
            client.set_voltage(args.voltage)
            client.set_current(args.current)
            print(f"Setpoints updated: {args.voltage:.3f} V, {args.current:.3f} A")
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 2
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
