# Routines

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

A routine is a sequence of timed steps applied to the PSU. Defined in `ips3608_app/models.py`, stored by `RoutineRepository`, and driven in real time by `ActiveRoutineRunner` (`ips3608_app/routines.py`).

## Step (`RoutineStep`)

| Field | Meaning |
|-------|---------|
| `voltage_v` | Setpoint for the step |
| `current_a` | Setpoint for the step |
| `duration_s` | How long the step holds |
| `output_on` | Whether output is on during the step (default `True`) |
| `otp_limit_c` | Per-step over-temperature limit; `0` = disabled |
| `settle_ms` | Stabilisation hint at step start (metadata, default 200) |
| `name` | Optional label |

## Routine (`RoutineDefinition`)

| Field | Meaning |
|-------|---------|
| `name` | Routine name |
| `steps` | List of `RoutineStep` |
| `loops` | Full repetitions; **`0` = infinite** |
| `stop_output_on_finish` | Stop output when the routine ends (default `True`) |
| `execution_limit_s` | *Deprecated*, kept for JSON compatibility |

Derived: `total_step_duration_s` (one loop) and `total_duration_s` (× loops, or `inf` when looping forever).

## Runner state machine

`RoutineState`: `IDLE → RUNNING ⇄ PAUSED → COMPLETED` / `ABORTED`.

`ActiveRoutineRunner` exposes `start / pause / resume / abort`, a `tick()` that returns the `(voltage, current, output_on)` for the current instant (auto-transitioning to `COMPLETED` after the last loop), and `runtime_info()` for live progress (current loop, step index/name, elapsed/remaining).

## Storage format

JSON, **schema version 3**:

```json
{
  "version": 3,
  "routines": [
    {
      "name": "burn-in",
      "loops": 1,
      "stop_output_on_finish": true,
      "steps": [
        {"voltage_v": 12.0, "current_a": 2.0, "duration_s": 30.0, "output_on": true,
         "otp_limit_c": 0.0, "settle_ms": 200.0, "name": "warm"}
      ]
    }
  ]
}
```

**Auto-migration on load:**
- raw list → versioned dict (backup `_legacy`),
- old v2 ramp format (`voltage_start_v`/`voltage_end_v`) → constant-setpoint steps using end values (backup `_v2_ramp`), then rewritten as version 3.

Backups land in `backup/v1/`, atomic writes, max 10 retained.

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#routines)

Una routine è una sequenza di passi temporizzati applicati all'alimentatore. Definita in `ips3608_app/models.py`, salvata da `RoutineRepository` e guidata in tempo reale da `ActiveRoutineRunner` (`ips3608_app/routines.py`).

## Passo (`RoutineStep`)

| Campo | Significato |
|-------|-------------|
| `voltage_v` | Setpoint del passo |
| `current_a` | Setpoint del passo |
| `duration_s` | Durata del passo |
| `output_on` | Output attivo durante il passo (default `True`) |
| `otp_limit_c` | Limite di sovratemperatura per passo; `0` = disabilitato |
| `settle_ms` | Suggerimento di stabilizzazione a inizio passo (metadata, default 200) |
| `name` | Etichetta opzionale |

## Routine (`RoutineDefinition`)

| Campo | Significato |
|-------|-------------|
| `name` | Nome routine |
| `steps` | Lista di `RoutineStep` |
| `loops` | Ripetizioni complete; **`0` = infinito** |
| `stop_output_on_finish` | Ferma l'output al termine (default `True`) |
| `execution_limit_s` | *Deprecato*, mantenuto per compatibilità JSON |

Derivati: `total_step_duration_s` (un loop) e `total_duration_s` (× loop, oppure `inf` se loop infinito).

## Macchina a stati del runner

`RoutineState`: `IDLE → RUNNING ⇄ PAUSED → COMPLETED` / `ABORTED`.

`ActiveRoutineRunner` espone `start / pause / resume / abort`, un `tick()` che ritorna `(voltage, current, output_on)` per l'istante corrente (passando automaticamente a `COMPLETED` dopo l'ultimo loop), e `runtime_info()` per l'avanzamento live (loop corrente, indice/nome passo, trascorso/rimanente).

## Formato di salvataggio

JSON, **schema versione 3**:

```json
{
  "version": 3,
  "routines": [
    {
      "name": "burn-in",
      "loops": 1,
      "stop_output_on_finish": true,
      "steps": [
        {"voltage_v": 12.0, "current_a": 2.0, "duration_s": 30.0, "output_on": true,
         "otp_limit_c": 0.0, "settle_ms": 200.0, "name": "warm"}
      ]
    }
  ]
}
```

**Auto-migrazione al caricamento:**
- lista grezza → dict versionato (backup `_legacy`),
- vecchio formato a rampa v2 (`voltage_start_v`/`voltage_end_v`) → passi a setpoint costante usando i valori finali (backup `_v2_ramp`), poi riscritto come versione 3.

I backup finiscono in `backup/v1/`, scritture atomiche, max 10 conservati.
