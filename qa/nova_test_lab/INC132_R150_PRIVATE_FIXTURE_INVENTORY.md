# INC132 — Inventario fixture private nel LAB (read-only) — 06/11/2026

## Ambito e norme
- DTM **v1.0.74** esatto, SHA256 `7ebd387abee2ef1479e26000c0244928c9bdfb1689882cb77ff567c6fabc3a27`; BH-001, BH-004, BH-007 e divieti di bypass.
- Solo progetto Neon **NOVA SCIENCE TEST LAB** (`raspy-frog-60845977`), branch `lab` (`br-icy-sky-bbbs0l19`), DB `nova_lab`. NO accesso ai database produttivi; nessuna mutazione.
- Query eseguite come `nova_r139_qa_reader`: SELECT consentito, INSERT/UPDATE/DELETE negati. Policy: no Snapshot automatico, no API esterne, limite 900000 byte per fixture.
- È una *foto storica di input R115*, **non** un file FIT grezzo autenticato né un nuovo Snapshot.

## Inventario letto direttamente nel TEST, senza payload in output

| Fixture esistente | Stato | Dimensione circa | Attività recenti | Eventi evidence ledger | Eventi ripetibilità |
|---|---|---:|---:|---:|---:|
| `personal-r135-lossless-2026-11-03` | ACTIVE / owner_authorized | 683456 B | 40 | 59 | 16 |
| `personal-r136-last-ca-lossless` | ACTIVE / owner_authorized | 684981 B | 41 | 60 | 16 |
| R135 non-lossless | INACTIVE | ~682 KB | non usata | — | — |
| R136 non-lossless | INACTIVE | ~683 KB | non usata | — | — |

Controlli aggregati sulle fixture **attive**: tutti i 40 e i 41 activity ID sono distinti; 12/16 eventi di ripetibilità etichettati `strong`, 13/16 con recupero osservato completo; nessuna prova bytes FIT/receipt nei campi diretti controllati. La sequenza R135→R136 conserva tutti i 40 ID attività originali e tutti i 59 record del ledger senza modifiche, aggiungendo **1 attività** e **1 evento scientifico**. Conteggi ottenuti con query SQL che non restituiscono record personali.

**Non confondere:**
1. Il JSON contiene `recent_activities`, `power_model`, `evidence_ledger`, inclusi nomi di campi di registrazione originale e ripetizioni.
2. Una label `DEVICE_LAPS` o `source_verified` nel JSON storico NON è una ricevuta RAW FIT attuale legata a un owner/autenticazione.
3. La presenza dei 7 template Tempo e dei 2 replay storici NON dimostra validità individualizzata Card2 né garantisce Card3 sempre completa.

## Tentativo di replay completo con il vero R150

- Creato `qa/nova_test_lab/run_inc132_private_r150_lossless_replay.py`: pin SHA256 R150 e MD5 privata per ciascuna fixture, verifica schema/fingerprint, connessione solo tramite `nova_r139_qa_reader`, transazione READ ONLY, nessuna stampa di output atleta, mutation suite R115, solo conteggi esito.
- Workflow separato: `.github/workflows/nova-inc132-private-r150-replay.yml` con `NOVA_TEST_LAB_DATABASE_URL` secret, branch TEST, nessun artifact, nessuna API esterna.
- GitHub Actions [42202401839](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42202401839): **BLOCKED**, eccezione driver `OperationalError` nella connessione; core non eseguito.
- Seconda CI [42202625072](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42202625072): **BLOCKED/TIMEOUT_OR_NETWORK**; user/database nel secret parsato coerenti, ma collegamento runner→Neon ancora non disponibile. Nessun payload è stato scaricato nella CI, nessun dato pubblicato.
- Il connettore Neon accessibile in questa sessione ha invece svolto i controlli SQL **read-only** sopra con il ruolo corretto. Un PASS SQL **NON** equivale a PASS R150/R115 privato.

## Gate rimanenti
- CI read-only runner→Neon: **BLOCKED, causa timeout ancora da diagnosticare** (rete/endpoint/credenziale eventualmente obsoleta, senza toccare firewall/produzione).
- Replay R150 privato e mutation suite: **NOT_EXECUTED**. Provenienza RAW FIT byte e request owner-bound: **NOT_VERIFIED**.
- Card3 BH-001 e Card2 BH-004: **RED**; Q01–Q24: **NOT_VERIFIED**; **PRODUCTION=NO_GO**.

Per proseguire correttamente: ripristinare solo un collegamento LAB sicuro oppure utilizzare il connettore Neon per ulteriori SELECT aggregati senza esportare le fixture pubblicamente; mai aggirare i gate FIT o usare un owner simulato come autentico.
