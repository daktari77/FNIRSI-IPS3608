from __future__ import annotations

import struct
from dataclasses import dataclass


# Verified protocol values from existing tools in this workspace.
CMD_READ = 0xA1
CMD_WRITE_BYTE = 0xB1
CMD_CONNECT = 0xC1  # cmd_type byte (packet[1]) — coincides numerically with REG_SET_VOLT but occupies a different packet position

REG_SET_VOLT = 0xC1  # register byte (packet[2]) — same numeric value as CMD_CONNECT by protocol design
REG_SET_CURR = 0xC2
REG_LIVE = 0xC3
REG_TEMP = 0xC4
REG_OTP_LIMIT = 0xD4
REG_OUTPUT = 0xDB

REQ_HEADER = 0xF1
RESP_HEADER = 0xF0


@dataclass(frozen=True)
class ProtocolPacket:
    cmd_type: int
    register: int
    payload: bytes

    def to_bytes(self) -> bytes:
        return build_packet(self.cmd_type, self.register, self.payload)


def checksum(register: int, payload: bytes) -> int:
    length = len(payload)
    return (register + length + sum(payload)) & 0xFF


def build_packet(cmd_type: int, register: int, payload: bytes) -> bytes:
    length = len(payload)
    cs = checksum(register, payload)
    return bytes([REQ_HEADER, cmd_type, register, length]) + payload + bytes([cs])


def validate_frame(frame: bytes) -> bool:
    if len(frame) < 5 or frame[0] != RESP_HEADER:
        return False
    length = frame[3]
    if len(frame) != 5 + length:
        return False
    register = frame[2]
    payload = frame[4 : 4 + length]
    expected = checksum(register, payload)
    return frame[4 + length] == expected


def extract_frames(buffer: bytearray) -> list[bytes]:
    frames: list[bytes] = []
    while True:
        if len(buffer) < 5:
            break
        if buffer[0] != RESP_HEADER:
            del buffer[0]
            continue
        frame_len = 5 + buffer[3]
        if len(buffer) < frame_len:
            break
        frame = bytes(buffer[:frame_len])
        del buffer[:frame_len]
        if validate_frame(frame):
            frames.append(frame)
    return frames


def parse_live_payload(payload: bytes) -> tuple[float, float, float]:
    if len(payload) != 12:
        raise ValueError(f"Unexpected live payload length: {len(payload)}")
    voltage_v = struct.unpack("<f", payload[0:4])[0]
    current_a = struct.unpack("<f", payload[4:8])[0]
    power_w = struct.unpack("<f", payload[8:12])[0]
    return voltage_v, current_a, power_w


def parse_temp_payload(payload: bytes) -> float:
    if len(payload) != 4:
        raise ValueError(f"Unexpected temperature payload length: {len(payload)}")
    return struct.unpack("<f", payload)[0]


def cmd_connect(on: bool) -> ProtocolPacket:
    return ProtocolPacket(CMD_CONNECT, 0x00, bytes([1 if on else 0]))


def cmd_read_live() -> ProtocolPacket:
    return ProtocolPacket(CMD_READ, REG_LIVE, b"\x00")


def cmd_read_temp() -> ProtocolPacket:
    return ProtocolPacket(CMD_READ, REG_TEMP, b"\x00")


def cmd_set_voltage(voltage_v: float) -> ProtocolPacket:
    return ProtocolPacket(CMD_WRITE_BYTE, REG_SET_VOLT, struct.pack("<f", float(voltage_v)))


def cmd_set_current(current_a: float) -> ProtocolPacket:
    return ProtocolPacket(CMD_WRITE_BYTE, REG_SET_CURR, struct.pack("<f", float(current_a)))


def cmd_output(on: bool) -> ProtocolPacket:
    return ProtocolPacket(CMD_WRITE_BYTE, REG_OUTPUT, bytes([1 if on else 0]))


# TODO: verify if some IPS3608 firmware revisions require CR/LF terminators.
# TODO: if additional registers are needed, define them here (not in UI modules).
