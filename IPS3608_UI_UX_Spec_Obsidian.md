---
title: IPS3608 - UI/UX Spec Moderna
aliases:
  - IPS3608 Modern UI Spec
  - UI Power Lab Controller
tags:
  - ips3608
  - ui
  - ux
  - dashboard
  - datalogger
  - alarm
created: 2026-05-20
---

# IPS3608 - UI/UX Spec Moderna

Specifica di interfaccia software moderna, leggera e altamente leggibile per controllo alimentatore, monitoraggio, allarmi, routine e datalogger.

---

## 1. Obiettivi di Design

1. Grafica moderna, pulita, professionale da banco laboratorio.
2. Interfaccia leggera: nessun effetto grafico pesante, zero clutter.
3. Gerarchia visuale netta: parametri fondamentali sempre in primo piano.
4. Numeri principali con carattere digitale monospaziato, molto leggibili.
5. UX orientata alla sicurezza: stato output e allarmi sempre visibili.

---

## 2. Principi UI

1. Primary Data First: V, I, P, T sempre in area superiore centrale.
2. Action Clarity: START e STOP grandi, separati, ad alta riconoscibilita.
3. Information Layers:
- Layer 1: Stato attuale e controllo rapido.
- Layer 2: Configurazioni e funzioni.
- Layer 3: Analisi storica e dati.
4. Consistenza: stessi pattern di input, validazione e feedback in tutto il software.
5. Error Prevention: limiti hard, conferme contestuali solo su azioni critiche.

---

## 3. Layout Proposto (Desktop)

## 3.1 Top Bar

Elementi:
1. Stato connessione seriale.
2. Porta attiva e baud.
3. Stato device (IDLE, RUN, PROTECTION, LOST).
4. Quick actions: Connect, Disconnect, Emergency STOP.

## 3.2 Dashboard Core (Hero Area)

Card principali grandi:
1. Voltage (V)
2. Current (A)
3. Power (W)
4. Temperature (C)

Ogni card mostra:
1. Valore live in grande.
2. Setpoint correlato.
3. Delta live vs setpoint.
4. Mini trend 30-60 s.

## 3.3 Control Panel

Sezione impostazioni:
1. Set V
2. Set I
3. Set T (OTP)
4. Apply V/I/T

Sezione output:
1. START
2. STOP
3. Stato output ben evidente.

Sezione protezioni:
1. OVP
2. OCP
3. OPP
4. OTP

## 3.4 USB Outputs Panel (Nuovo, dedicato)

Due card separate:
1. USB Type-A
2. USB Type-C

Per ogni card:
1. Porta attiva/non attiva.
2. Protocollo negoziato (se disponibile dal device).
3. Potenza erogata stimata o misurata.
4. Stato fault/protezione.

Nota funzionale:
- Il device supporta protocolli moderni di ricarica su USB-A e USB-C.
- La UI deve prevedere indicatori protocollo anche se una parte dei dati inizialmente non fosse telemetrica via protocollo seriale.

## 3.5 Bottom Area

Tab secondarie:
1. Datalogger
2. Allarmi
3. Routine
4. Event Log
5. Settings

---

## 4. Tipografia

## 4.1 Numeri Principali (digit style)

Requisito:
- Font digitale monospaziato per V, I, P, T e timer.

Opzioni consigliate:
1. DSEG7 Classic
2. Digital-7
3. Share Tech Mono (fallback tecnico)
4. JetBrains Mono per testi secondari

Regole:
1. Numeri live: 56-72 px su desktop.
2. Setpoint: 22-28 px.
3. Label unita di misura: 14-16 px.
4. Tracking leggermente positivo per leggibilita.

## 4.2 Testi UI

1. Titoli sezioni: 16-18 px semibold.
2. Testi controllo: 13-15 px regular.
3. Alert critici: 14-16 px semibold.

---

## 5. Sistema Colori (chiaro tecnico)

Direzione estetica:
- Tema chiaro professionale con accenti tecnici, contrasto alto.

Palette proposta:
1. Background: #F4F6F8
2. Surface: #FFFFFF
3. Border: #D7DEE6
4. Text primary: #0F1B2A
5. Text secondary: #4A5A6A
6. Accent voltage: #0B84F3
7. Accent current: #00A86B
8. Accent power: #F59E0B
9. Accent temp: #EF4444
10. START: #16A34A
11. STOP: #DC2626
12. Warning: #F59E0B
13. Critical: #B91C1C

Regola:
- Niente gradienti invadenti; ombre molto leggere; focus su dati.

---

## 6. Componenti Chiave

1. MetricCard grande (digit value + unit + setpoint + sparkline).
2. SafeInput con range, step, validazione istantanea.
3. OutputStateBadge (RUN/STOP/PROTECTION).
4. AlarmBanner sticky con severita.
5. AlarmTable con Ack, filtro, storico.
6. LoggerTimeline con marker eventi/allarmi.
7. USBPortCard con protocol badge.

---

## 7. Allarmi (UX fondamentale)

## 7.1 Visibilita

1. Banner in alto persistente per warning/critical.
2. Icona stato globale sempre presente.
3. Counter allarmi non risolti.

## 7.2 Interazione

1. Ack singolo e ack multiplo.
2. Clear consentito solo quando condizione rientra.
3. Event details con causa, timestamp, valore trigger.

## 7.3 Azioni automatiche

Configurabili:
1. Auto STOP output su critical.
2. Cooldown prima di restart.
3. Logging obbligatorio evento.

---

## 8. Datalogger UX

1. Pulsanti Start/Pause/Stop logging.
2. Session metadata: nome test, note, operatore.
3. Frequenza campionamento selezionabile.
4. Indicatore dimensione sessione e durata.
5. Export rapido CSV/JSON.
6. Overlay eventi e allarmi sul grafico.

---

## 9. Routine UX

1. Editor step-by-step.
2. Tipi step: Set, Wait, Condition, Loop, Stop.
3. Simulazione routine prima dell esecuzione.
4. Execution monitor con progress e step corrente.
5. Abort immediato sempre disponibile.

## 9.1 Parametri Routine (fondamentale)

Ogni step routine deve consentire la definizione completa dei parametri di funzionamento:
1. V target
2. I limite
3. T limite (OTP)
4. durata step
5. stato uscita (RUN/STOP)

Esempio richiesto:
1. 3V x 10s
2. 4V x 5s
3. 2V x 1s

Requisito UX:
1. editor tabellare con step riordinabili drag and drop
2. validazione immediata dei range
3. stima durata totale e loop
4. anteprima esecuzione prima di Start

---

## 10. Performance e Leggerezza

Target:
1. UI fluida a 60 fps con refresh dati 5-10 Hz.
2. Cold start sotto 2 s su PC medio.
3. Consumo RAM contenuto.
4. Nessun blocco UI durante I/O seriale e logging.

Linee guida:
1. I/O su thread dedicato.
2. Batch update UI a intervalli regolari.
3. Virtualizzazione tabelle log grandi.

---

## 11. Architettura Frontend Proposta

1. Shell App con routing tab.
2. State store centralizzato.
3. Device service asincrono.
4. Alarm engine separato.
5. Logger service separato.
6. Routine engine separato.

Tecnologia consigliata:
1. Python + Qt (PySide6) per desktop professionale.
2. Tema custom leggero basato su design token.

Motivazione:
- migliore struttura rispetto a Tkinter per dashboard evolute, tabelle, grafici, theming e scalabilita.

---

## 12. MVP Visuale (prima release grafica)

Include:
1. Dashboard V/I/P/T con font digit.
2. Pannello V/I/T + START/STOP.
3. USB-A/USB-C panel con stato/protocol badge.
4. Alarm banner + lista allarmi base.
5. Datalogger base con grafico live e CSV.

Esclude temporaneamente:
1. Routine complesse multi-condizione.
2. Notifiche esterne (mail/telegram).

---

## 13. Criteri di Accettazione UI

1. Parametri fondamentali leggibili a 1.5 m su monitor 24.
2. START e STOP identificabili in meno di 1 secondo.
3. Nessuna azione critica senza feedback immediato.
4. Allarme critical sempre visibile senza cambiare tab.
5. USB panel presente e coerente con stato device.

---

## 14. Roadmap Implementativa UX/UI

1. Sprint 1: design tokens + layout shell + dashboard core.
2. Sprint 2: control panel + output controls + validazioni.
3. Sprint 3: alarm center + banner + ack flow.
4. Sprint 4: datalogger UI + grafici + export.
5. Sprint 5: routine editor base + hardening.

---

## Link interni

- [[IPS3608_Documentazione_Obsidian]]
- [[ips3608_cli.py]]
- [[ips3608_gui.py]]
- [[ips3608_live.ps1]]
