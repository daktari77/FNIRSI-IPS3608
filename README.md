# IPS3608 Remote Control

Versione corrente: `1.0.0`

Desktop app Python per il controllo del FNIRSI IPS3608, con interfaccia PySide6, grafici realtime, datalogger, memorie M1..M6 e modalità simulata per sviluppo/test.

## Funzionalità

- connessione reale via seriale con `pyserial`
- modalità simulata per usare tutta l'app senza dispositivo collegato
- controllo output separato dalla connessione PC-dispositivo
- letture realtime di tensione, corrente, temperatura e potenza calcolata
- grafico realtime V/I su asse X temporale
- datalogger con export CSV e tabella log
- memorie fisse M1..M6 con nome, Vset e Iset persistenti
- routine con rampe temporali e stop output a fine esecuzione
- UI modulare con launcher principale

## UI Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FNIRSI IPS3608 Remote Control                          ● Connected / Error  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Menu: File | Datalogger | Graphs | Routine | Memory | Instrument | Mode     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Connection: [COM3 ▼] [Refresh] [Connect] [Disconnect]                       │
│ Output:     [Vset 12.00 V] [Iset 1.500 A] [START OUTPUT / STOP OUTPUT]      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Datalogger: ● OFF / IN CORSO  [1 s ▼] [START LOG] [STOP LOG] [CSV] [Table]  │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ Realtime Cards                │ Realtime Graph                               │
│ [Voltage] [Current]           │  V/I vs Time                                 │
│ [Temperature] [Power]         │  Y: 0..40 V                                  │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ Status Bar: connection | output | datalogger | samples | last data | errors  │
└──────────────────────────────────────────────────────────────────────────────┘
```

The layout keeps connection, output control, memories/routines and live feedback
visually separated so the app reads like a bench instrument, not a generic form.

## Avvio

### Dipendenze

```powershell
pip install PySide6 pyqtgraph pyserial
```

### Avvio applicazione desktop

```powershell
python ips3608_remote_ui.py
```

## Struttura progetto

- `ips3608_remote_ui.py`: launcher dell'app desktop
- `ips3608_app/`: package con UI, client seriale, memorie e routine
- `ips3608_cli.py`: CLI di supporto
- `ips3608_gui.py`: mini GUI Tkinter
- `ips3608_live.ps1`: monitor live PowerShell
- `CHANGELOG.md`: cronologia release
- `docs/IPS3608_Documentazione_Obsidian.md`: documentazione operativa

## Note operative

- Range supportati nell'app desktop:
  - Vset: `0..36.00 V`
  - Iset: `0..8.20 A`
- Il grafico V/I è limitato al range operativo con asse Y base `0..40 V`.
- La temperatura resta visibile nelle card realtime, ma non è plottata.
- Le memorie M1..M6 sono persistenti su file JSON locale.

## Documentazione

- [Documentazione operativa](docs/IPS3608_Documentazione_Obsidian.md)
- [Changelog](CHANGELOG.md)

## Stato progetto

Repo inizializzata per sviluppo locale e sincronizzazione su GitHub.
