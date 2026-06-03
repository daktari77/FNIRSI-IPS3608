# FNIRSI IPS3608 Remote Control

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

A portable Python desktop application for controlling the **FNIRSI IPS3608** programmable power supply over serial. It ships a PySide6 GUI, real-time V/I/P/T readings, a live plot, CSV datalogging, six persistent memory presets, timed routines, and a hardware-free **simulation mode**.

- **Stable:** `1.0.0`
- **Development branch:** `feature/v2-0-0-planning` — version `2.0.0-dev.0`

## Wiki pages

| Page | Contents |
|------|----------|
| [Installation](Installation) | Dependencies, running, portable build |
| [GUI Usage](GUI-Usage) | Connection, output control, graph, datalogger |
| [CLI & Scripting](CLI-and-Scripting) | `ips3608_cli.py`, `ips3608_shell.py`, simulation |
| [Memory Presets](Memory-Presets) | M1..M6 slots, storage format |
| [Routines](Routines) | Timed step sequences, loops, JSON format |
| [Protocol Reference](Protocol-Reference) | Serial framing, registers, checksum |
| [Architecture](Architecture) | Package layout, threading model |
| [Contributing](Contributing) | How to contribute, tests, build |

## At a glance

- Real serial control via `pyserial` (9600 8N1) and a simulated device for development.
- Operating ranges: **Vset 0–36.00 V**, **Iset 0–8.20 A**, **OTP limit 0–99 °C**.
- Real-time voltage, current, computed power, and temperature.
- Connection flow is **separate** from output enable — you connect first, then arm the output.

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#fnirsi-ips3608-remote-control)

Applicazione desktop Python portabile per controllare l'alimentatore programmabile **FNIRSI IPS3608** via seriale. Include una GUI PySide6, letture realtime V/I/P/T, grafico live, datalogging CSV, sei memorie persistenti, routine temporizzate e una **modalità simulata** senza hardware.

- **Stabile:** `1.0.0`
- **Branch di sviluppo:** `feature/v2-0-0-planning` — versione `2.0.0-dev.0`

## Pagine della wiki

| Pagina | Contenuto |
|--------|-----------|
| [Installation](Installation) | Dipendenze, avvio, build portabile |
| [GUI Usage](GUI-Usage) | Connessione, controllo output, grafico, datalogger |
| [CLI & Scripting](CLI-and-Scripting) | `ips3608_cli.py`, `ips3608_shell.py`, simulazione |
| [Memory Presets](Memory-Presets) | Slot M1..M6, formato di salvataggio |
| [Routines](Routines) | Sequenze a passi temporizzati, loop, formato JSON |
| [Protocol Reference](Protocol-Reference) | Framing seriale, registri, checksum |
| [Architecture](Architecture) | Struttura del package, modello a thread |
| [Contributing](Contributing) | Come contribuire, test, build |

## In sintesi

- Controllo seriale reale via `pyserial` (9600 8N1) e dispositivo simulato per lo sviluppo.
- Range operativi: **Vset 0–36.00 V**, **Iset 0–8.20 A**, **limite OTP 0–99 °C**.
- Tensione, corrente, potenza calcolata e temperatura in tempo reale.
- Il flusso di connessione è **separato** dall'abilitazione dell'output: prima ci si connette, poi si arma l'uscita.
