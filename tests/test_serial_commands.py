import struct
import unittest

from ips3608_app.serial_commands import (
    CMD_READ,
    REG_LIVE,
    RESP_HEADER,
    build_packet,
    checksum,
    extract_frames,
    parse_live_payload,
)


class SerialCommandsTests(unittest.TestCase):
    def test_build_packet_uses_protocol_checksum(self):
        payload = b"\x00"

        packet = build_packet(CMD_READ, REG_LIVE, payload)

        self.assertEqual(packet, bytes([0xF1, CMD_READ, REG_LIVE, 1, 0, checksum(REG_LIVE, payload)]))

    def test_extract_frames_skips_noise_and_consumes_valid_frame(self):
        payload = struct.pack("<fff", 12.0, 1.5, 18.0)
        frame = bytes([RESP_HEADER, CMD_READ, REG_LIVE, len(payload)]) + payload + bytes([checksum(REG_LIVE, payload)])
        buffer = bytearray(b"\x99\x88" + frame)

        frames = extract_frames(buffer)

        self.assertEqual(frames, [frame])
        self.assertEqual(buffer, bytearray())

    def test_parse_live_payload_returns_floats(self):
        payload = struct.pack("<fff", 12.0, 1.5, 18.0)

        self.assertEqual(parse_live_payload(payload), (12.0, 1.5, 18.0))


if __name__ == "__main__":
    unittest.main()
