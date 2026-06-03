# Architecture

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

## Package layout (`ips3608_app/`)

| Module | Responsibility |
|--------|----------------|
| `serial_commands.py` | Pure protocol: packet build, frame validate/extract, payload parse. No I/O. |
| `clients.py` | `IPS3608Client` (real serial) and `SimulatedIPS3608Client` (synthetic). |
| `models.py` | Dataclasses & enums: `DeviceConfig`, `Measurement`/`LogSample`, `AppState`, `UiState`, `RoutineState`, `RoutineStep/Definition/RuntimeInfo`, `MemoryPreset`. |
| `worker.py` | `MeasurementThread(QThread)` — serial I/O off the UI thread. |
| `main_window.py` | `MainWindow`, wiring, menus, lifecycle. |
| `ui_panels.py` | `ConnectionPanel`, `OutputControlPanel`, `RealtimeCardsPanel`, `GraphPanel`, `DataloggerPanel`, `StatusLogPanel`. |
| `log_table_dock.py` | `LogTableDockWidget` for the sample table. |
| `memory_presets.py` | `MemoryRepository` + `MemoryPresetDialog`. |
| `routines.py` | `RoutineRepository` + `ActiveRoutineRunner`. |
| `routine_dialogs.py` | Routine editor/manager dialogs. |

Entry point: `ips3608_remote_ui.py` → `ips3608_app.main_window:main`.

## Threading model

- Serial I/O runs on `MeasurementThread`, a `QThread` using `isInterruptionRequested()` + `msleep()`; results reach the UI via signals (`_on_measurement_ready`, `_on_measure_error`). No polling `QTimer` on the main thread.
- `IPS3608Client` guards the port with a `threading.Lock`. The lock wraps each full write→read cycle in `_query_first_matching_frame` (held ≤ the read timeout ~0.6 s) so a main-thread `set_voltage` cannot inject a command between a request and its response. Disconnect waits for the measurement thread before touching the client.

## Persistence

Both `MemoryRepository` and `RoutineRepository` use the same pattern: atomic temp-file writes, versioned JSON, auto-migration of legacy formats, and timestamped backups under `backup/v1/` rotated to a max of 10.

## Tests

`tests/` covers the pure layers: `test_serial_commands.py`, `test_routines.py`, `test_memory_presets.py`. Run with `python -m pytest`.

## Design docs

`PRODUCT.md`, `DESIGN.md`, `IPS3608_UI_UX_Spec_Obsidian.md`, `IPS3608_Routine_System_Spec.md`, and `docs/` (operational docs + v2 migration notes).

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#architecture)

## Struttura del package (`ips3608_app/`)

| Modulo | Responsabilità |
|--------|----------------|
| `serial_commands.py` | Protocollo puro: build pacchetto, validate/extract frame, parse payload. Nessun I/O. |
| `clients.py` | `IPS3608Client` (seriale reale) e `SimulatedIPS3608Client` (sintetico). |
| `models.py` | Dataclass & enum: `DeviceConfig`, `Measurement`/`LogSample`, `AppState`, `UiState`, `RoutineState`, `RoutineStep/Definition/RuntimeInfo`, `MemoryPreset`. |
| `worker.py` | `MeasurementThread(QThread)` — I/O seriale fuori dal thread UI. |
| `main_window.py` | `MainWindow`, wiring, menu, ciclo di vita. |
| `ui_panels.py` | `ConnectionPanel`, `OutputControlPanel`, `RealtimeCardsPanel`, `GraphPanel`, `DataloggerPanel`, `StatusLogPanel`. |
| `log_table_dock.py` | `LogTableDockWidget` per la tabella campioni. |
| `memory_presets.py` | `MemoryRepository` + `MemoryPresetDialog`. |
| `routines.py` | `RoutineRepository` + `ActiveRoutineRunner`. |
| `routine_dialogs.py` | Dialog editor/manager delle routine. |

Entry point: `ips3608_remote_ui.py` → `ips3608_app.main_window:main`.

## Modello a thread

- L'I/O seriale gira su `MeasurementThread`, un `QThread` che usa `isInterruptionRequested()` + `msleep()`; i risultati arrivano alla UI via signal (`_on_measurement_ready`, `_on_measure_error`). Nessun `QTimer` di polling sul main thread.
- `IPS3608Client` protegge la porta con un `threading.Lock`. Il lock avvolge ogni ciclo completo write→read in `_query_first_matching_frame` (tenuto ≤ il timeout di lettura ~0.6 s) così che un `set_voltage` dal main thread non possa iniettare un comando tra richiesta e risposta. La disconnessione attende il thread di misura prima di toccare il client.

## Persistenza

Sia `MemoryRepository` che `RoutineRepository` usano lo stesso pattern: scritture atomiche su file temporaneo, JSON versionato, auto-migrazione dei formati legacy e backup con timestamp in `backup/v1/` ruotati a max 10.

## Test

`tests/` copre i layer puri: `test_serial_commands.py`, `test_routines.py`, `test_memory_presets.py`. Esegui con `python -m pytest`.

## Documenti di design

`PRODUCT.md`, `DESIGN.md`, `IPS3608_UI_UX_Spec_Obsidian.md`, `IPS3608_Routine_System_Spec.md` e `docs/` (documentazione operativa + note migrazione v2).
