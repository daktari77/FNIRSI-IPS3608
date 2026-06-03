# Protocol Reference

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

Low-level FNIRSI IPS3608 serial protocol, implemented in `ips3608_app/serial_commands.py`. Serial config: **9600 baud, 8N1**, read timeout 0.2 s, no flow control, DTR+RTS asserted.

## Frame format

**Request** (`REQ_HEADER = 0xF1`):

```
F1 | cmd_type | register | length | payload... | checksum
```

**Response** (`RESP_HEADER = 0xF0`):

```
F0 | cmd_type | register | length | payload... | checksum
```

`checksum = (register + length + sum(payload)) & 0xFF`

`validate_frame` checks header, exact length (`5 + length`), and checksum. `extract_frames` scans a rolling buffer, discarding bytes until a `0xF0` header aligns.

## Command / register bytes

| Name | Value | Role |
|------|-------|------|
| `CMD_READ` | `0xA1` | Read command (`cmd_type`) |
| `CMD_WRITE_BYTE` | `0xB1` | Write command (`cmd_type`) |
| `CMD_CONNECT` | `0xC1` | Connect command (`cmd_type`, packet[1]) |
| `REG_SET_VOLT` | `0xC1` | Voltage setpoint register (packet[2]) |
| `REG_SET_CURR` | `0xC2` | Current setpoint register |
| `REG_LIVE` | `0xC3` | Live V/I/P register |
| `REG_TEMP` | `0xC4` | Temperature register |
| `REG_OTP_LIMIT` | `0xD4` | Over-temperature limit register |
| `REG_OUTPUT` | `0xDB` | Output on/off register |

> **Note:** `CMD_CONNECT` and `REG_SET_VOLT` are both `0xC1` by protocol design — they occupy *different packet positions*, so there is no actual collision.

## Payloads

- Setpoints (voltage, current, OTP) are little-endian `float32` (`struct.pack("<f", ...)`).
- **Live** payload = 12 bytes (`length 0x0C`): voltage `[0:4]`, current `[4:8]`, power `[8:12]`, all `<f`.
- **Temperature** payload = 4 bytes (`length 0x04`): one `<f`.

## Concrete frames

| Action | Bytes |
|--------|-------|
| Connect | `F1 C1 00 01 01 02` |
| Disconnect | `F1 C1 00 01 00 00 01` |
| Output ON | `F1 B1 DB 01 01 01 DD` |
| Output OFF | `F1 B1 DB 01 00 00 DC` |
| Status response header | `F0 A1 C3 ...` |

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#protocol-reference)

Protocollo seriale di basso livello del FNIRSI IPS3608, implementato in `ips3608_app/serial_commands.py`. Config seriale: **9600 baud, 8N1**, timeout lettura 0.2 s, nessun controllo di flusso, DTR+RTS asseriti.

## Formato frame

**Richiesta** (`REQ_HEADER = 0xF1`):

```
F1 | cmd_type | register | length | payload... | checksum
```

**Risposta** (`RESP_HEADER = 0xF0`):

```
F0 | cmd_type | register | length | payload... | checksum
```

`checksum = (register + length + sum(payload)) & 0xFF`

`validate_frame` controlla header, lunghezza esatta (`5 + length`) e checksum. `extract_frames` scorre un buffer rolling, scartando byte finché un header `0xF0` non si allinea.

## Byte comando / registro

| Nome | Valore | Ruolo |
|------|--------|-------|
| `CMD_READ` | `0xA1` | Comando lettura (`cmd_type`) |
| `CMD_WRITE_BYTE` | `0xB1` | Comando scrittura (`cmd_type`) |
| `CMD_CONNECT` | `0xC1` | Comando connect (`cmd_type`, packet[1]) |
| `REG_SET_VOLT` | `0xC1` | Registro setpoint tensione (packet[2]) |
| `REG_SET_CURR` | `0xC2` | Registro setpoint corrente |
| `REG_LIVE` | `0xC3` | Registro live V/I/P |
| `REG_TEMP` | `0xC4` | Registro temperatura |
| `REG_OTP_LIMIT` | `0xD4` | Registro limite sovratemperatura |
| `REG_OUTPUT` | `0xDB` | Registro output on/off |

> **Nota:** `CMD_CONNECT` e `REG_SET_VOLT` valgono entrambi `0xC1` per design del protocollo — occupano *posizioni diverse* nel pacchetto, quindi non c'è collisione reale.

## Payload

- I setpoint (tensione, corrente, OTP) sono `float32` little-endian (`struct.pack("<f", ...)`).
- Payload **live** = 12 byte (`length 0x0C`): tensione `[0:4]`, corrente `[4:8]`, potenza `[8:12]`, tutti `<f`.
- Payload **temperatura** = 4 byte (`length 0x04`): un `<f`.

## Frame concreti

| Azione | Byte |
|--------|------|
| Connect | `F1 C1 00 01 01 02` |
| Disconnect | `F1 C1 00 01 00 00 01` |
| Output ON | `F1 B1 DB 01 01 01 DD` |
| Output OFF | `F1 B1 DB 01 00 00 DC` |
| Header risposta status | `F0 A1 C3 ...` |
