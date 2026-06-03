# Contributing

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

The repository is public and welcomes external contributions. Full guidelines live in [`CONTRIBUTING.md`](../blob/main/CONTRIBUTING.md); this is a quick summary.

## Workflow

1. Fork the repo.
2. Branch: `feature/<short-desc>` or `fix/<short-desc>`.
3. Make a clear, focused commit.
4. Run the tests when relevant: `python -m pytest`.
5. Open a PR against `main`.

## Tests

The pure layers are unit-tested under `tests/`:

- `test_serial_commands.py` — packet build, checksum, frame validate/extract, payload parse.
- `test_routines.py` — runner state machine, migration, durations.
- `test_memory_presets.py` — slot load/save/migrate.

Protocol functions (`build_packet`, `validate_frame`, `extract_frames`) are pure and the natural place to add coverage first.

## Build

```powershell
pip install pyinstaller
.\build_portable.ps1   # → dist/FNIRSI-IPS3608
```

## Code style

Standard Python, readable and consistent with existing patterns. Keep PRs small and focused; add tests or docs where appropriate.

## Issues

Use the GitHub issue templates (bug report / feature request). Include a clear description, reproduction steps, and expected behavior.

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#contributing)

Il repository è pubblico e accoglie contributi esterni. Le linee guida complete sono in [`CONTRIBUTING.md`](../blob/main/CONTRIBUTING.md); questo è un riepilogo rapido.

## Flusso di lavoro

1. Fai il fork del repo.
2. Branch: `feature/<descrizione-breve>` o `fix/<descrizione-breve>`.
3. Fai un commit chiaro e mirato.
4. Esegui i test quando rilevante: `python -m pytest`.
5. Apri una PR verso `main`.

## Test

I layer puri sono testati con unit test in `tests/`:

- `test_serial_commands.py` — build pacchetto, checksum, validate/extract frame, parse payload.
- `test_routines.py` — macchina a stati del runner, migrazione, durate.
- `test_memory_presets.py` — load/save/migrate degli slot.

Le funzioni di protocollo (`build_packet`, `validate_frame`, `extract_frames`) sono pure e il posto naturale dove aggiungere copertura per primo.

## Build

```powershell
pip install pyinstaller
.\build_portable.ps1   # → dist/FNIRSI-IPS3608
```

## Stile del codice

Python standard, leggibile e coerente con i pattern esistenti. PR piccole e mirate; aggiungi test o documentazione dove opportuno.

## Issue

Usa i template di issue GitHub (bug report / feature request). Includi descrizione chiara, passi di riproduzione e comportamento atteso.
