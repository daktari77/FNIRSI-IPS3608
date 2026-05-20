import serial
import struct
import threading

class FNIRSIProtocol:
    HEADER_REQ = 0xF1
    HEADER_RESP = 0xF0
    CMD_READ = 0xA1
    CMD_WRITE = 0xB0
    CMD_WRITE_BYTE = 0xB1
    CMD_CONNECT = 0xC1

    REG_VOLTAGE = 0xC0
    REG_CURRENT = 0xDE
    REG_LIVE = 0xC3
    REG_TEMP = 0xC4
    REG_OUTPUT = 0xDB
    REG_PROTECTION = 0xDC
    REG_MODE = 0xDD
    REG_ALL = 0xFF

    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.lock = threading.Lock()

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    def _checksum(self, register, length, data):
        return (register + length + sum(data)) & 0xFF

    def _send_packet(self, cmd_type, register, data):
        length = len(data)
        packet = bytearray([
            self.HEADER_REQ,
            cmd_type,
            register,
            length
        ])
        packet.extend(data)
        checksum = self._checksum(register, length, data)
        packet.append(checksum)
        with self.lock:
            self.ser.write(packet)

    def _read_response(self):
        header = self.ser.read(1)
        if not header or header[0] != self.HEADER_RESP:
            return None
        cmd_type = self.ser.read(1)
        register = self.ser.read(1)
        length = self.ser.read(1)
        if not (cmd_type and register and length):
            return None
        cmd_type = cmd_type[0]
        register = register[0]
        length = length[0]
        data = self.ser.read(length)
        checksum = self.ser.read(1)
        if not checksum:
            return None
        checksum = checksum[0]
        if checksum != self._checksum(register, length, data):
            return None
        return {
            'cmd_type': cmd_type,
            'register': register,
            'data': data
        }

    def connect_device(self, on=True):
        # Connect: F1 C1 00 01 01 02, Disconnect: F1 C1 00 01 00 01
        data = [0x01] if on else [0x00]
        self._send_packet(self.CMD_CONNECT, 0x00, data)
        return self._read_response()

    def set_voltage(self, voltage):
        # Set voltage: F1 B0 C0 04 [float32le] [checksum]
        data = list(struct.pack('<f', voltage))
        self._send_packet(self.CMD_WRITE, self.REG_VOLTAGE, data)
        return self._read_response()

    def set_current(self, current):
        # Set current: F1 B0 DE 04 [float32le] [checksum]
        data = list(struct.pack('<f', current))
        self._send_packet(self.CMD_WRITE, self.REG_CURRENT, data)
        return self._read_response()

    def output_on(self, on=True):
        # Output ON: F1 B1 DB 01 01 DD, OFF: F1 B1 DB 01 00 DC
        data = [0x01] if on else [0x00]
        self._send_packet(self.CMD_WRITE_BYTE, self.REG_OUTPUT, data)
        return self._read_response()

    def read_live_values(self):
        # Read live: F1 A1 C3 01 00 C4
        self._send_packet(self.CMD_READ, self.REG_LIVE, [0x00])
        resp = self._read_response()
        if resp and resp['register'] == self.REG_LIVE:
            # Data: [V(float32), A(float32), W(float32)]
            data = resp['data']
            if len(data) >= 12:
                v, a, w = struct.unpack('<fff', data[:12])
                return {'voltage': v, 'current': a, 'power': w}
        return None

    def read_all(self):
        # Read all: F1 A1 FF 01 00 00
        self._send_packet(self.CMD_READ, self.REG_ALL, [0x00])
        return self._read_response()

    def read_temperature(self):
        # Read temp: F1 A1 C4 01 00 C5
        self._send_packet(self.CMD_READ, self.REG_TEMP, [0x00])
        resp = self._read_response()
        if resp and resp['register'] == self.REG_TEMP:
            data = resp['data']
            if len(data) >= 4:
                temp, = struct.unpack('<f', data[:4])
                return temp
        return None
