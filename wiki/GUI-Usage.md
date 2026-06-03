# GUI Usage

🇬🇧 **English** · 🇮🇹 [Italiano](#-italiano)

The main window (`ips3608_app/main_window.py`) is composed of modular panels.

## Connection

1. Pick the serial port from the **Connection** panel (ports are enumerated via `serial.tools.list_ports`).
2. Click **Connect**. On connect the app sends the connect command and starts the background measurement thread.
3. To work without hardware, enable **Simulated mode** (menu / mode action) — a synthetic device produces plausible V/I/T values.

Connection and output are **decoupled**: connecting does *not* turn on the output.

## Output control

- **Set voltage** (0–36.00 V) and **set current** (0–8.20 A) via the Output Control panel.
- **Output ON/OFF** arms/disarms power delivery. On disconnect the app stops the output first, then closes the link, so the PSU never keeps delivering after the PC drops.

## Real-time readings

- Cards show **V, I, P (computed = V×I), T** with a 7-segment DSEG7 font for arm's-length readability.
- A **fan indicator** is inferred from temperature (≥ 45 °C); the device controls the fan in firmware — no serial register is exposed.

## Live graph

- V and I plotted over time (`pyqtgraph`), limited to the operating range, default Y axis up to 40 V.
- Temperature is shown on the cards but **not** plotted.

## Datalogger

- Start/stop logging of timestamped samples.
- **Export CSV** and view samples in the dockable log table (`LogTableDockWidget`).

## States

UI state machine (`models.UiState`): `DISCONNECTED → CONNECTING → CONNECTED_OUTPUT_OFF → CONNECTED_OUTPUT_ON`, plus `COMMUNICATION_ERROR`.

## Scripting shell from the GUI

**File → Open scripting shell** launches / shows usage of the `ips3608_shell.py` wrapper (see [CLI & Scripting](CLI-and-Scripting)).

---

# 🇮🇹 Italiano

🇮🇹 **Italiano** · 🇬🇧 [English](#gui-usage)

La finestra principale (`ips3608_app/main_window.py`) è composta da pannelli modulari.

## Connessione

1. Seleziona la porta seriale dal pannello **Connection** (le porte sono elencate via `serial.tools.list_ports`).
2. Clicca **Connect**. Alla connessione l'app invia il comando di connect e avvia il thread di misura in background.
3. Per lavorare senza hardware, attiva la **modalità simulata** — un dispositivo sintetico genera valori V/I/T plausibili.

Connessione e output sono **disaccoppiati**: connettersi *non* accende l'uscita.

## Controllo output

- **Imposta tensione** (0–36.00 V) e **corrente** (0–8.20 A) dal pannello Output Control.
- **Output ON/OFF** arma/disarma l'erogazione. Alla disconnessione l'app ferma prima l'uscita e poi chiude il collegamento, così l'alimentatore non continua a erogare dopo lo scollegamento del PC.

## Letture realtime

- Le card mostrano **V, I, P (calcolata = V×I), T** con font 7 segmenti DSEG7, leggibili a distanza di un braccio.
- L'**indicatore ventola** è dedotto dalla temperatura (≥ 45 °C); il dispositivo gestisce la ventola via firmware — nessun registro seriale esposto.

## Grafico live

- V e I tracciate nel tempo (`pyqtgraph`), limitate al range operativo, asse Y di default fino a 40 V.
- La temperatura è sulle card ma **non** viene tracciata.

## Datalogger

- Avvia/ferma il logging di campioni con timestamp.
- **Export CSV** e visualizzazione nella tabella log agganciabile (`LogTableDockWidget`).

## Stati

Macchina a stati UI (`models.UiState`): `DISCONNECTED → CONNECTING → CONNECTED_OUTPUT_OFF → CONNECTED_OUTPUT_ON`, più `COMMUNICATION_ERROR`.

## Shell di scripting dalla GUI

**File → Open scripting shell** avvia / mostra l'uso del wrapper `ips3608_shell.py` (vedi [CLI & Scripting](CLI-and-Scripting)).
