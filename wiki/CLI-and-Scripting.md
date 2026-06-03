# CLI & Scripting

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

Two command-line entry points are provided.

## `ips3608_shell.py` — scripting wrapper

High-level wrapper around the app library (`ips3608_app/`). Supports **simulation**, so it runs without hardware. Best for automation and tests.

Options: `--port`, `--baud` (default 9600), `--timeout` (default 0.2 s), `--simulate`.

Commands:

| Command | Action |
|---------|--------|
| `status` | Print voltage, current, power, temperature |
| `on` | Enable output |
| `off` | Disable output |
| `set <V> <A>` | Set voltage and current |

```powershell
python ips3608_shell.py --port COM3 status
python ips3608_shell.py --port COM3 set 5.0 1.0
python ips3608_shell.py --port COM3 on
python ips3608_shell.py --simulate status
```

For real-device mode `--port` is required; in `--simulate` it is optional.

## `ips3608_cli.py` — minimal serial CLI

Talks the protocol directly (no app library client). Adds a `live` loop and an optional OTP temperature limit. Default `--port COM13`, `--baud 9600`.

| Command | Action |
|---------|--------|
| `status` | Single live read |
| `live [--interval S] [--count N]` | Continuous read loop (`--count <= 0` = forever) |
| `set <V> <A> [<TempC>]` | Set voltage, current, optional OTP limit (0–99 °C) |
| `on` / `start` | Enable output |
| `off` / `stop` | Disable output |

```powershell
python ips3608_cli.py --port COM3 live --interval 0.5 --count 20
python ips3608_cli.py --port COM3 set 12.0 2.0 60
```

Ranges are validated: V 0–36, A 0–8.2, OTP 0–99 °C.

## Other helpers

- `ips3608_gui.py` — lightweight Tkinter GUI variant.
- `ips3608_studio.py` — experimental Tkinter "Studio" with a routine-window DSL and direct preset-register addressing.
- `ips3608_live.ps1` — PowerShell live-monitoring script.

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#cli--scripting)

Sono forniti due entry point da riga di comando.

## `ips3608_shell.py` — wrapper di scripting

Wrapper di alto livello sulla libreria dell'app (`ips3608_app/`). Supporta la **simulazione**, quindi funziona senza hardware. Ideale per automazione e test.

Opzioni: `--port`, `--baud` (default 9600), `--timeout` (default 0.2 s), `--simulate`.

Comandi:

| Comando | Azione |
|---------|--------|
| `status` | Stampa tensione, corrente, potenza, temperatura |
| `on` | Abilita output |
| `off` | Disabilita output |
| `set <V> <A>` | Imposta tensione e corrente |

```powershell
python ips3608_shell.py --port COM3 status
python ips3608_shell.py --port COM3 set 5.0 1.0
python ips3608_shell.py --port COM3 on
python ips3608_shell.py --simulate status
```

In modalità dispositivo reale `--port` è obbligatorio; con `--simulate` è opzionale.

## `ips3608_cli.py` — CLI seriale minimale

Parla il protocollo direttamente (senza il client della libreria). Aggiunge un loop `live` e un limite di temperatura OTP opzionale. Default `--port COM13`, `--baud 9600`.

| Comando | Azione |
|---------|--------|
| `status` | Lettura live singola |
| `live [--interval S] [--count N]` | Loop di lettura continuo (`--count <= 0` = infinito) |
| `set <V> <A> [<TempC>]` | Imposta tensione, corrente, limite OTP opzionale (0–99 °C) |
| `on` / `start` | Abilita output |
| `off` / `stop` | Disabilita output |

```powershell
python ips3608_cli.py --port COM3 live --interval 0.5 --count 20
python ips3608_cli.py --port COM3 set 12.0 2.0 60
```

I range sono validati: V 0–36, A 0–8.2, OTP 0–99 °C.

## Altri strumenti

- `ips3608_gui.py` — variante GUI leggera in Tkinter.
- `ips3608_studio.py` — "Studio" sperimentale in Tkinter con DSL a finestra per le routine e indirizzamento diretto dei registri preset.
- `ips3608_live.ps1` — script PowerShell di monitoraggio live.
