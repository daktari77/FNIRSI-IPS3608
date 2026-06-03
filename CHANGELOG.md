# Changelog

## 2.0.0-dev.0 - Unreleased

Linea major in preparazione per evolvere il progetto verso un frontend di laboratorio professionale.

### Added (dev)

- central design-token module (`ips3608_app/theme.py`) as the single source of truth for colors, radii, and the app stylesheet
- no-data state on the realtime metric cards: disconnected/connecting/error shows `--` in muted slate, not a misleading `0.00`
- arm-to-confirm on output enable (two-step, ~3 s window); stopping stays immediate
- keyboard shortcuts and menu mnemonics (Connect `Ctrl+K`, Start output `Ctrl+Return`, logging `Ctrl+L`, etc.) and logical tab order through the setpoints
- tooltips on setpoints, OTP, the output button, and mode actions
- recovery hint in the Connection panel on disconnect / communication error

### Changed (dev)

- full UI translated to English (no mixed Italian strings)
- connection state machine keyed off `UiState` instead of display text (localization-safe)
- fan-active indicator no longer uses Voltage Blue (Channel Monopoly Rule); OTP setpoint range corrected to 0–99 °C
- portable build driven solely by `IPS3608RemoteControl.spec` (output `dist/FNIRSI-IPS3608`); build scripts and README aligned

### Planned

- gate di decisione per breaking changes
- piano di migrazione dati/configurazioni da `1.x`
- roadmap major con milestone `2.0.0`, `2.1.0`, `2.2.0`

### Potential Breaking Changes

- possibile evoluzione schema preset/routine con metadata estesi
- possibile introduzione audit trail strutturato e formato log aggiornato
- possibile API locale per automazione con nuovi contratti

## 1.0.0 - 2026-05-20

Prima release completa e funzionante dell'app desktop FNIRSI IPS3608 Remote Control.

### Aggiunto

- UI modulare PySide6 con launcher desktop
- connessione reale e modalità simulata
- controllo output separato dalla connessione
- letture realtime di tensione, corrente, temperatura e potenza
- grafico realtime V/I su asse temporale
- datalogger con export CSV e tabella log
- memorie persistenti M1..M6
- routine con rampe temporali e stop output finale
- documentazione operativa e README aggiornati
