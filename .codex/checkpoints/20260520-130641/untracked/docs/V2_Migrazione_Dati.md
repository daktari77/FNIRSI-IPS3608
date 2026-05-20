# Migrazione dati V2.0

## Routine
- Formato ora: oggetto con `version` e array `routines`.
- Backup automatico in `backup/v1/` ad ogni salvataggio o migrazione.
- Migrazione trasparente da vecchio formato (array) a nuovo formato (oggetto versionato).

## Preset di memoria
- Formato ora: oggetto con `version` e array `presets`.
- Backup automatico in `backup/v1/` ad ogni salvataggio o migrazione.
- Migrazione trasparente da vecchio formato (array) a nuovo formato (oggetto versionato).

## Note operative
- I repository (RoutineRepository, MemoryRepository) gestiscono la migrazione e i backup.
- I file legacy vengono salvati in backup/v1/ con suffisso _legacy.
- La struttura dati è pronta per future evoluzioni e rollback.

## Esempi

### Routine
```json
{
  "version": 2,
  "routines": [
    {
      "name": "Test",
      "steps": [
        { "voltage_start_v": 12.0, "voltage_end_v": 12.0, "current_start_a": 1.0, "current_end_a": 1.0, "duration_s": 10.0 }
      ],
      "stop_output_on_finish": true,
      "execution_limit_s": 0.0
    }
  ]
}
```

### Preset
```json
{
  "version": 2,
  "presets": [
    { "slot_id": "M1", "label": "", "voltage_v": 0.0, "current_a": 0.0, "enabled": false }
  ]
}
```
