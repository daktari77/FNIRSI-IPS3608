---
title: IPS3608 - Documentazione Operativa
aliases:
  - FNIRSI IPS3608 Guide
  - IPS3608 COM13 Control
tags:
  - ips3608
  - fnirsi
  - seriale
  - automazione
  - laboratorio
created: 2026-05-20
---

## IPS3608 - Documentazione Operativa

Documentazione pratica per controllo dell'alimentatore **FNIRSI IPS3608** via seriale USB su Windows.

Versione stabile: `1.0.0`

Versione in sviluppo (branch `feature/v2-0-0-planning`): `2.0.0-dev.0`

Contenuto principale:

- comunicazione seriale verificata su COM13
- script PowerShell per misure live
- CLI Python per set parametri e start/stop
- mini GUI per uso quotidiano
- sezione comandi completa

---

## 1. Panoramica Rapida

Il dispositivo IPS3608 non usa SCPI testuale in questo setup, ma un protocollo binario proprietario FNIRSI.

Parametri seriali funzionanti verificati:

- Porta: `COM13`
- Baud rate: `9600`
- Formato: `8N1`
- Handshake: `None`

Flusso operativo tipico:

1. Impostare parametri `V`, `I`, `T`.
2. Eseguire `START` per attivare uscita.
3. Leggere valori live `V/I/P/T`.
4. Eseguire `STOP` per disattivare uscita.

---

## 2. File Disponibili

Nella cartella `ips3608_tools`:

- `ips3608_live.ps1`: monitor live in PowerShell
- `ips3608_cli.py`: CLI Python (set, status, live, start, stop)
- `ips3608_gui.py`: mini GUI Tkinter con campi V/I/T e pulsanti START/STOP

---

## 3. Prerequisiti

### 3.1 Python

Python usato:

- `3.14.x` (system install)

### 3.2 Dipendenze

Pacchetto richiesto:

- `pyserial`

Installazione:

```powershell
pip install pyserial
```

### 3.3 Permessi/Concorrenza

Note operative:

- Evitare di tenere aperti contemporaneamente CLI/GUI/monitor sulla stessa COM.
- Se una app tiene bloccata la porta, chiuderla prima di lanciare l'altra.

---

## 4. Protocollo (Sintesi)

Formato comando inviato:

- Header request: `0xF1`
- Struttura: `[F1] [CmdType] [Register] [Length] [Data...] [Checksum]`
- Checksum: `(Register + Length + sum(Data)) & 0xFF`

Formato risposta:

- Header response: `0xF0`
- Struttura: `[F0] [CmdType] [Register] [Length] [Payload...] [Checksum]`

Registri principali usati:

- `0xC1`: set tensione
- `0xC2`: set corrente
- `0xC3`: lettura live (V, I, P)
- `0xC4`: lettura temperatura
- `0xD4`: limite temperatura (OTP)
- `0xDB`: stato uscita (start/stop)

---

## 5. Avvio Rapido

### 5.1 Monitor live PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utente\ips3608_tools\ips3608_live.ps1 -PortName COM13 -BaudRate 9600 -IntervalMs 500 -Count 20
```

### 5.2 Stato singolo (CLI Python)

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 status
```

### 5.3 GUI

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_gui.py
```

---

## 6. Sezione Comandi

Questa sezione raccoglie i comandi piu utili, pronti da copiare.

### 6.1 Comandi CLI Python

Sintassi base:

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 <comando>
```

### a) Impostazione parametri V/I/T

Imposta tensione, corrente e limite temperatura OTP:

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 set 5.0 1.0 60
```

Imposta solo V/I (senza modificare T):

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 set 3.3 0.5
```

Range validi:

- V: `0 .. 36`
- I: `0 .. 8.2`
- T: `0 .. 99`

### b) Start/Stop uscita

START:

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 start
```

STOP:

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 stop
```

Alias equivalenti:

- `start` == `on`
- `stop` == `off`

### c) Letture

Lettura singola:

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 status
```

Lettura continua (20 campioni):

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 live --interval 0.5 --count 20
```

Loop continuo (fino a Ctrl+C):

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 live --interval 1.0 --count 0
```

### 6.2 Comandi PowerShell

Monitor live rapido:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Utente\ips3608_tools\ips3608_live.ps1 -PortName COM13 -BaudRate 9600 -IntervalMs 300 -Count 10
```

Parametri utili script PowerShell:

- `-PortName` (default `COM13`)
- `-BaudRate` (default `9600`)
- `-IntervalMs` intervallo campionamento
- `-Count` numero righe (`<=0` infinito)

### 6.3 Flusso GUI (operatore)

Workflow consigliato:

1. Avvia `ips3608_gui.py`
2. `Connect`
3. Inserisci `V`, `I`, `T`
4. `Apply V/I/T`
5. `START`
6. `Read Now` o `Auto 1s`
7. `STOP`
8. `Disconnect`

---

## 7. Esempi Operativi

### 7.1 Test a vuoto 3V

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 set 3.0 1.0 60
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 start
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 status
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 stop
```

### 7.2 Monitor continuo durante test carico

```powershell
python C:\Users\Utente\ips3608_tools\ips3608_cli.py --port COM13 --baud 9600 live --interval 0.2 --count 0
```

---

## 8. Troubleshooting

### 8.1 Errore porta occupata

Sintomo:

- errore apertura COM13

Azioni:

1. Chiudere GUI/CLI/monitor gia aperti.
2. Verificare che software terzi non stiano usando COM13.
3. Ricollegare cavo USB-C e riprovare.

### 8.2 Nessuna risposta

Azioni:

1. Verificare porta corretta (`COM13`).
2. Verificare baud (`9600`).
3. Verificare cavo dati (non solo ricarica).
4. Spegnere/riaccendere alimentatore.

### 8.3 pyserial mancante

```powershell
pip install pyserial
```

---

## 9. Sicurezza Operativa

Raccomandazioni:

- Prima di `START`, verificare sempre i setpoint.
- Per test iniziali, usare corrente limitata.
- Evitare variazioni brusche con carichi sensibili.
- Terminare sempre con `STOP` prima di scollegare il carico.

---

## 10. Possibili Estensioni

Idee future:

- logging CSV automatico (timestamp, V, I, P, T)
- profili preset richiamabili da GUI
- allarmi software su soglie V/I/T
- safe-start obbligatorio con conferma

---

## 11. Roadmap Frontend Professionale

Obiettivo: evolvere l'app da controllo remoto a frontend da laboratorio con sicurezza, ripetibilita e tracciabilita.

### 11.1 Release 2.0.0 - Safety e Logging Professionale

Feature target:

- soft-start configurabile e profili safe-default
- limiti software hard su `V/I/P/T` con conferma operatore
- watchdog comunicazione seriale con fail-safe `Output OFF`
- metadata sessione obbligatori (`operatore`, `DUT`, `lotto`, `note`)
- marker eventi in log (`START`, `STOP`, cambio setpoint, allarmi)

Criteri di accettazione:

- nessun `START` consentito se i setpoint superano i limiti configurati
- a perdita comunicazione, output spento entro timeout configurato
- ogni CSV include metadata e timeline eventi

### 11.2 Release 2.1.0 - Routine Avanzate e Report

Feature target:

- routine `step/ramp/hold` con durata e stop finale opzionale
- validazione preventiva routine (dry-run in simulazione)
- report sessione in PDF con grafico, statistiche e allarmi
- storico preset con versione e data modifica

Criteri di accettazione:

- routine non valide bloccate prima dell'esecuzione
- ogni sessione produce artefatto esportabile (CSV + PDF)

### 11.3 Release 2.2.0 - Multi-Device e Automazione

Feature target:

- gestione multi-strumento in dashboard unica
- start/stop sincronizzato su gruppi di device
- API locale (`REST/WebSocket`) per orchestrazione test bench
- audit trail operazioni con utente, timestamp e azione

Criteri di accettazione:

- controllo simultaneo stabile di almeno 2 device
- API in grado di avviare/arrestare test senza uso UI

---

## Link interni (Obsidian)

- [[ips3608_live.ps1]]
- [[ips3608_cli.py]]
- [[ips3608_gui.py]]
