# V2 Gate e Piano Migrazione

## Scopo

Definire quando il progetto puo dichiarare una major `2.0.0` e come migrare in sicurezza da `1.x`.

## Gate Decisionale 2.0.0

Passare a `2.0.0` solo se almeno una di queste condizioni e vera:

- cambia il formato dati persistenti (preset, routine, log) in modo non retrocompatibile
- cambia il comportamento operativo base in modo incompatibile con flussi `1.x`
- viene introdotta un'API di automazione non compatibile con i contratti precedenti

## Checklist di Rilascio Major

- definizione esplicita delle breaking changes
- script o routine di migrazione dati validata su casi reali
- fallback o backup automatico prima migrazione
- documentazione operativa aggiornata con differenze `1.x` vs `2.x`
- test regressione su connessione seriale, output control, logging, routine

## Strategia Migrazione Dati

1. Backup automatico dei file JSON correnti in `backup/v1/` con timestamp.
2. Rilevamento versione schema in apertura.
3. Migrazione guidata a nuovo schema con report finale.
4. Possibilita di rollback ai file originali.

## SemVer Operativo

- `1.0.x`: fix e stabilizzazione linea attuale
- `2.0.0-dev.y`: sviluppo major in branch dedicato
- `2.0.0`: prima release major con breaking changes documentate
