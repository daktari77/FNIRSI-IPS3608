# Memory Presets

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

Six fixed preset slots **M1..M6**, each storing a label, voltage setpoint, and current setpoint. Managed via `MemoryPresetDialog` and persisted by `MemoryRepository` (`ips3608_app/memory_presets.py`).

## Slot model (`MemoryPreset`)

| Field | Meaning |
|-------|---------|
| `slot_id` | `M1`..`M6` |
| `label` | User name; display becomes `M2 - 5V rail` |
| `voltage_v` | 0–36.00 V |
| `current_a` | 0–8.20 A |
| `enabled` | `True` once saved |

## Dialog actions

- **Load From Current Output** — copy the live setpoints into the editor.
- **Recall To Output** — emits `recall_requested(V, A)`; the main window applies it to device + spinboxes.
- **Save Slot** / **Clear Slot**.

The dialog is decoupled from the main window: it receives `current_voltage`/`current_current` and communicates back only through the `recall_requested` signal.

## Storage format

JSON, **schema version 2**:

```json
{
  "version": 2,
  "presets": [
    {"slot_id": "M1", "label": "5V rail", "voltage_v": 5.0, "current_a": 1.0, "enabled": true}
  ]
}
```

- A legacy raw-list file is auto-migrated to the versioned object on load (a `_legacy` backup is written first).
- Every save writes a timestamped backup under `backup/v1/` and **rotates** to keep at most 10 backups.
- Writes are atomic (temp file + replace).

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#memory-presets)

Sei slot preset fissi **M1..M6**, ciascuno con etichetta, setpoint di tensione e setpoint di corrente. Gestiti da `MemoryPresetDialog` e salvati da `MemoryRepository` (`ips3608_app/memory_presets.py`).

## Modello slot (`MemoryPreset`)

| Campo | Significato |
|-------|-------------|
| `slot_id` | `M1`..`M6` |
| `label` | Nome utente; visualizzato come `M2 - 5V rail` |
| `voltage_v` | 0–36.00 V |
| `current_a` | 0–8.20 A |
| `enabled` | `True` dopo il salvataggio |

## Azioni del dialog

- **Load From Current Output** — copia i setpoint live nell'editor.
- **Recall To Output** — emette `recall_requested(V, A)`; la finestra principale lo applica a dispositivo + spinbox.
- **Save Slot** / **Clear Slot**.

Il dialog è disaccoppiato dalla finestra principale: riceve `current_voltage`/`current_current` e comunica indietro solo tramite il signal `recall_requested`.

## Formato di salvataggio

JSON, **schema versione 2**:

```json
{
  "version": 2,
  "presets": [
    {"slot_id": "M1", "label": "5V rail", "voltage_v": 5.0, "current_a": 1.0, "enabled": true}
  ]
}
```

- Un file legacy a lista grezza viene auto-migrato nell'oggetto versionato al caricamento (prima viene scritto un backup `_legacy`).
- Ogni salvataggio scrive un backup con timestamp in `backup/v1/` e applica la **rotazione** mantenendo al massimo 10 backup.
- Le scritture sono atomiche (file temporaneo + replace).
