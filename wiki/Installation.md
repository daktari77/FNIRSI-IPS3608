# Installation

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

## Requirements

- Python 3.10+ (uses `from __future__ import annotations` and modern type hints)
- A FNIRSI IPS3608 connected over USB/serial (or use simulation mode — no hardware needed)

## Dependencies

```powershell
pip install -r requirements.txt
```

`requirements.txt` pins:

- `PySide6` — GUI toolkit
- `pyqtgraph` — real-time plot
- `pyserial` — serial transport

## Run the desktop app

```powershell
python ips3608_remote_ui.py
```

This launches the modular PySide6 application (`ips3608_app.main_window:main`).

## Portable Windows build

```powershell
pip install pyinstaller
.\build_portable.ps1
```

A portable bundle is produced under `dist/FNIRSI-IPS3608`. The build embeds the
DSEG7 7-segment font required by the readout cards
(`ips3608_app/assets/fonts/DSEG7Classic-Regular.ttf`). On Linux/macOS use
`build_portable.sh`.

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#installation)

## Requisiti

- Python 3.10+ (usa `from __future__ import annotations` e type hint moderni)
- Un FNIRSI IPS3608 collegato via USB/seriale (oppure usa la modalità simulata — nessun hardware necessario)

## Dipendenze

```powershell
pip install -r requirements.txt
```

`requirements.txt` richiede:

- `PySide6` — toolkit GUI
- `pyqtgraph` — grafico realtime
- `pyserial` — trasporto seriale

## Avvio dell'app desktop

```powershell
python ips3608_remote_ui.py
```

Avvia l'applicazione modulare PySide6 (`ips3608_app.main_window:main`).

## Build portabile Windows

```powershell
pip install pyinstaller
.\build_portable.ps1
```

Il bundle portabile viene creato in `dist/FNIRSI-IPS3608`. La build include il
font 7 segmenti DSEG7 usato dalle card di lettura
(`ips3608_app/assets/fonts/DSEG7Classic-Regular.ttf`). Su Linux/macOS usa
`build_portable.sh`.
