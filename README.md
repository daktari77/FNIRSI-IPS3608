# IPS3608 Remote Control

A portable Python desktop application for controlling the FNIRSI IPS3608 power supply.
It includes a PySide6 UI, real-time graphs, data logging, preset memories, and a simulation mode for development and testing.

## Stable & development versions

- Stable version: `1.0.0`
- Development branch: `feature/v2-0-0-planning`, version `2.0.0-dev.0`

## Features

- real serial control using `pyserial`
- simulated device mode for testing without hardware
- separate output control and device connection flow
- real-time voltage, current, temperature, and computed power readings
- live V/I plot over time
- datalogging with CSV export and table view
- six fixed memory presets (M1..M6) with persistent names, Vset, and Iset
- ramped routines with end-of-routine output stop
- modular UI with a clean main launcher

## Quick start

### Install dependencies

```powershell
pip install PySide6 pyqtgraph pyserial
```

### Run the desktop app

```powershell
python ips3608_remote_ui.py
```

### Build a portable Windows bundle

A portable build is available in `dist/IPS3608RemoteControl` after running:

```powershell
pip install pyinstaller
.\build_portable.ps1
```

This build includes the application assets and font file required by `ips3608_app/assets/fonts/DSEG7Classic-Regular.ttf`.

## Project structure

- `ips3608_remote_ui.py`: desktop application launcher
- `ips3608_app/`: core package with UI, serial client, memory presets, and routines
- `ips3608_cli.py`: command-line support for direct device control
- `ips3608_gui.py`: lightweight Tkinter GUI variant
- `ips3608_live.ps1`: PowerShell live monitoring script
- `CHANGELOG.md`: release history
- `docs/IPS3608_Documentazione_Obsidian.md`: operational documentation

## Operational notes

- Supported desktop app ranges:
  - Vset: `0..36.00 V`
  - Iset: `0..8.20 A`
- The V/I graph is limited to the operating range, with a default Y-axis up to `40 V`.
- Temperature is shown in the real-time cards, but it is not plotted.
- Memory presets are stored locally in JSON files.

## Collaboration

This repository is now public and welcomes contributions from external collaborators.
If you want to contribute:

- open an issue for bugs or feature requests
- submit a pull request for improvements
- ask for help if you want to extend simulation, UI, or device support

I am open to external collaboration, code reviews, and pairing on enhancements.

## Documentation

- [Operational documentation](docs/IPS3608_Documentazione_Obsidian.md)
- [Changelog](CHANGELOG.md)

## Status

Repository initialized for local development and GitHub publishing.
