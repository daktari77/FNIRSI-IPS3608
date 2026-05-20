---
title: IPS3608 - Routine System Spec
aliases:
  - IPS3608 Sequence Engine
  - Routine Builder Spec
tags:
  - ips3608
  - routine
  - automation
  - safety
created: 2026-05-20
---

# IPS3608 - Routine System Spec

Specifica del sistema routine per eseguire sequenze di funzionamento temporizzate e ripetibili.

---

## 1. Obiettivo

Permettere la definizione ed esecuzione di profili automatici tipo:
1. 3.0V per 10s
2. 4.0V per 5s
3. 2.0V per 1s

con controllo di sicurezza, allarmi, logging e stop immediato.

---

## 2. Requisiti Funzionali

1. Definizione routine a step ordinati.
2. Ogni step deve poter impostare:
- tensione target (V)
- corrente limite (I)
- limite temperatura OTP (T)
- durata
- stato uscita (RUN/STOP)
3. Supporto loop (ripeti routine N volte).
4. Supporto pre-delay e post-delay.
5. Esecuzione manuale start/stop/pause/resume.
6. Stop di emergenza con uscita immediata OFF.
7. Salvataggio routine come preset editabili.

---

## 3. Modello Step

Campi step consigliati:
1. id
2. name
3. set_v
4. set_i
5. set_t
6. duration_ms
7. output_on (true/false)
8. ramp_ms (opzionale, se supportato)
9. settle_ms (tempo stabilizzazione)
10. note

Vincoli:
1. set_v: 0..36
2. set_i: 0..8.2
3. set_t: 0..99
4. duration_ms: >= 100

---

## 4. Stato Esecuzione Runtime

Stati macchina:
1. IDLE
2. PRECHECK
3. RUNNING
4. PAUSED
5. COMPLETED
6. ABORTED
7. FAULT

Telemetria runtime:
1. routine_id
2. step_index corrente
3. elapsed_step_ms
4. elapsed_total_ms
5. loop corrente / loop totali
6. motivo stop (user, alarm, comm-lost, fine)

---

## 5. Sicurezza e Fail-safe

1. Precheck obbligatorio prima start:
- device connesso
- limiti validi
- allarmi critici assenti
2. Durante routine:
- monitor continuo V/I/P/T
- trigger allarmi su soglie
3. Regole stop automatico:
- alarm critical -> output OFF
- comm-lost -> output OFF
- checksum/error burst -> pause o abort (policy)
4. Su abort:
- comando STOP output
- log evento
- stato finale ABORTED/FAULT

---

## 6. Datalogger Integrato con Routine

Per ogni campione loggare:
1. timestamp
2. step_index
3. set_v/set_i/set_t
4. live_v/live_i/live_p/live_t
5. output_state
6. alarm_state

Per ogni evento loggare:
1. step_start
2. step_end
3. loop_start
4. loop_end
5. pause/resume
6. abort/fault

---

## 7. Esempio Routine Richiesta

Nome: Test Sequenza Base

Step:
1. Step 1
- V=3.0
- I=1.0
- T=60
- durata=10s
- output=ON
2. Step 2
- V=4.0
- I=1.0
- T=60
- durata=5s
- output=ON
3. Step 3
- V=2.0
- I=1.0
- T=60
- durata=1s
- output=ON

Fine routine:
1. output OFF
2. salvataggio summary run

---

## 8. Formato JSON Consigliato

```json
{
  "name": "Test Sequenza Base",
  "version": 1,
  "loops": 1,
  "safe_stop_on_end": true,
  "steps": [
    {"id": 1, "name": "S1", "set_v": 3.0, "set_i": 1.0, "set_t": 60.0, "duration_ms": 10000, "output_on": true, "settle_ms": 200},
    {"id": 2, "name": "S2", "set_v": 4.0, "set_i": 1.0, "set_t": 60.0, "duration_ms": 5000,  "output_on": true, "settle_ms": 200},
    {"id": 3, "name": "S3", "set_v": 2.0, "set_i": 1.0, "set_t": 60.0, "duration_ms": 1000,  "output_on": true, "settle_ms": 200}
  ]
}
```

---

## 9. UX del Routine Builder

Componenti:
1. tabella step editabile (add/delete/duplicate/reorder)
2. validazione inline per range e durata
3. pulsante Simula (stima durata totale)
4. pulsante Start Routine
5. pulsanti Pause, Resume, Abort
6. pannello runtime con progress bar e step corrente

KPI visuali runtime:
1. tempo residuo step
2. tempo residuo totale
3. numero loop
4. stato sicurezza

---

## 10. Alarm Policy durante Routine

Livelli:
1. info
2. warning
3. critical

Policy suggerita:
1. info -> log
2. warning -> log + banner
3. critical -> stop immediato output + abort routine

Ack:
1. gli allarmi critici devono richiedere acknowledge manuale prima di nuovo start.

---

## 11. Criteri di Accettazione

1. routine a 3 step eseguibile con timing corretto entro tolleranza +/-150 ms per step.
2. stop manuale porta output OFF in meno di 300 ms.
3. allarme critical interrompe routine e disattiva output.
4. log sessione include step, campioni e eventi.
5. routine salvabile/caricabile da JSON.

---

## Link interni

- [[IPS3608_UI_UX_Spec_Obsidian]]
- [[IPS3608_Documentazione_Obsidian]]
