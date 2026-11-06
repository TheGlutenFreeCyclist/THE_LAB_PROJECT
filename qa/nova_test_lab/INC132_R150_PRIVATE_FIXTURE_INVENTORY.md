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

## 06/11/2026 · GitHub ↔ Neon TEST CONNECTED — riparazione verificata

**CI [42205575451](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42205575451)** sul branch TEST:

- `neon-connection-verified`: **SUCCESS**. Secret GitHub compatibile con host TEST, porta 5432, autenticazione PostgreSQL TLS e utente `nova_r139_qa_reader`; database `nova_lab`, SELECT consentita e INSERT/UPDATE/DELETE negate.
- Diagnosi causale: il server Neon accetta il normale startup PostgreSQL TLS, ma il precedente client che inviava `options="-c default_transaction_read_only=on -c statement_timeout=12000"` in startup andava in timeout. Correzione: aprire connessione TLS, poi `db_connection.set_session(readonly=True, autocommit=False)`. L'identità e il gate `transaction_read_only=on` sono ricontrollati prima di ogni SELECT.
- `authorized-private-r150`: **FAIL SCIENTIFICO**, NON errore di collegamento. Entrambe le fixture lossless sono state lette in memoria e processate dal vero R150. Ciascuna presenta 3 divergenze nei 10 assert registrati: `canonical_plan_id`, `hard_session_count`, `workout_ids`. Mutation suite **non PASS** per entrambe. Nuova semantica: `SCIENTIFIC_DRIFT` con exit code 1; il sistema non considera tali scostamenti un PASS.
- Nessun nuovo Snapshot, nessun accesso a Neon produzione, nessuna modifica a DB, nessun dump JSON, nessun secret esportato in log, nessuna modifica a `the_lab_app.py`.
- Prossima ricerca: capire se queste tre differenze sono la conseguenza prevista del fail-closed R150 rispetto ai vecchi expected R135/R136 oppure una regressione non consentita. Non aggiornare gli expected per ottenere verde senza esaminare DTM/provenienza, e non usare fixture storiche come prova RAW FIT.

**Verdetto:** `GITHUB_NEON_TEST_LINK=PASS`, `R150_HISTORICAL_SCIENCE=FAIL/UNDER_INVESTIGATION`, `CARD3_BH001=RED`, `CARD2_BH004=RED`, `RAW_PROVENANCE=NOT_VERIFIED`, `PRODUCTION=NO_GO`.


## 06/11/2026 · Fase 4.3 — triage privacy-safe del drift R135/R136 → R150

È stata estesa **solo** la diagnostica del replay, senza modificare R150, DTM, fixture/expected o dati Neon:
- [Commit diagnostico 1](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/commit/8ace7b43f3cf4748016dbe41326640e89d879d5a): transizione HARD storica e R27, mutazioni differenziate;
- [Commit diagnostico 2](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/commit/97cdffc98bf2350b9b30a83fd29ca4b3bb1a733d): stadio di perdita HARD, R116 SKIPPED vs FAIL, authority e stato della prescrizione;
- [CI conclusiva 42209511450](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42209511450): connessione Neon TEST read-only **PASS**; replay privato R150 **FAIL SCIENTIFIC_DRIFT**, non errore di rete.

Esito identico su **entrambe** le fixture autorizzate (solo valori categoriali pubblicati):
- Expected storico: HARD presente. R150: **HARD assente**.
- R150: `hard_loss_stage=NO_HARD_REQUESTED`, `prescription_status=EASY_ONLY`, `execution_status=EASY_ONLY`.
- Gate nativo R27: **NOT_APPLICABLE**. Non è la causa di queste due divergenze.
- `authority_final_pass=true`: il blocco non è dovuto a un FAIL dell'autorità finale.
- 3/10 invarianti storici divergono: `canonical_plan_id`, `hard_session_count`, `workout_ids`. Gli altri sette corrispondono.
- La mutation suite R115 fallisce **solo il caso BASELINE_IDENTITY**; zero altri casi falliti tra gli eseguiti.
- I casi R116 di completamento realistico sono **SKIPPED_WRONG_PHASE** / not applicable, **non** FAIL fisiologico. Non contarli come test verdi né come regressione positiva.

**Nuova localizzazione:** R150 non domanda HARD **prima del compilatore**. I valori della decisione (`decision_action`/`decision_dimension`) continuano a coincidere con gli expected storici, quindi indagare lo storico del producer `build_nova_prescription` e i suoi gate, non falsificare `expected` e non introdurre un workaround UI. Una trasformazione safety fail-closed è plausibile ma **non provata**; resta aperta la distinzione safety corretta / regressione.

Workflow storico [42209511539](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42209511539): **FAIL sui pin R141** nei vecchi job; non indica perdita connessione Neon del workflow INC132.

**Stato:** ACCESS NEON TEST=PASS, REPLAY SCIENTIFICO=FAIL, R116 scenari=SKIPPED, R150 invariato, CARD3 BH-001=RED, CARD2 BH-004=RED, RAW FIT/owner-auth E2E=NOT_VERIFIED, PRODUZIONE=NO_GO. Nessun dump, write DB, Snapshot o calendario.


## 06/11/2026 · Fase 4.4 — Root cause confermata, compiler numerico PASS, owner E2E non verificato

Tutti gli interventi da `b7fdad80` a `49d89f9a` riguardano **solo diagnostica/test QA** sul branch autorizzato. DTM v1.0.74 e `the_lab_app.py` R150 con SHA256 `6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73` restano invariati. Nessun accesso ai DB produttivi; Neon LAB letto tramite ruolo SELECT-only. Solo aggregati e classi codificate in CI, nessun watt/ID attività/JSON/secret esposto.

**Diagnosi definitiva sulla coppia R135/R136 autorizzata (identica):**
1. Il producer originale ha inizialmente generato **1 HARD**, ma con `_tl_v1943_power_band.source=INTERVALS_DATED_FTP_EXPLORATORY`, `repeatability_state=NOT_VERIFIED_FOR_THIS_WORKOUT`, **nessun activity binding** e recuperi comparabili non attestati. `INC111` lo rifiuta correttamente con `CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN`. Non è un guasto del compiler: la richiesta HARD non gli arriva. Il retry del producer torna `EASY_ONLY`, `WORKOUT_LIBRARY_NO_CANDIDATE`.
2. Scansione aggregata sull'**originale** catalogo e modello: 25 template goal/dimension, 18 bande numeriche `PRESCRIBED`, **6** bande da ripetizioni comparabili che superano anche il **vero replay scientifico INC083**. Tuttavia **0/6** sono meccanicamente compatibili con i **3** slot dichiarati. Questo limita la **HARD day-of**, non dimostra l'impossibilità di una quality futura non schedulata.
3. Per tutti e 6 i candidati validati numericamente, `_nova_inc091_compile_native` **compila una sessione futura senza data**: 6/6 PASS per fixture, 0 errori, 0 booking inventati. Il componente nativo non è la causa del drift storico.
4. L'intero `_nova_inc050_future_quality` invocato **senza alcun owner autenticato né Flask analyze** rimane `PLANNING_BLOCKED` con causa `OWNER_NOT_AUTHENTICATED`, 0 workout emessi. Non è lecito interpretarlo come FAIL del selettore; è un gate di sicurezza corretto. La fixture R115 offline non fornisce RAW FIT byte receipt né identity owner-bound.
5. Expected storici R135/R136 **NON alterati**: 3/10 drift (`canonical_plan_id`, `hard_session_count`, `workout_ids`), `BASELINE_IDENTITY` FAIL, altri mutation case R115 0 FAIL, R116 `SKIPPED_WRONG_PHASE`. La CI privata continua intenzionalmente a uscire con **SCIENTIFIC_DRIFT/FAIL**: non colorare verde un comportamento cambiato senza governance scientifica.

**CI verificati:** [sorgente banda originale e rifiuto](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42211016565), [controllo sintetico scienza+compiler+FTP esplorativo FAIL-CLOSED: SUCCESS](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42211248954), [sei candidati prova numerica vs tre slot](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42211494517), [sei compilazioni native unscheduled](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42211709435), [owner assente: fail-closed](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42212120255). Su ciascuna CI privata il job di connessione TLS Neon TEST è **PASS**, il job scientifico storico resta **FAIL** per drift invarianti, non per network/DB.

**Decisione tecnica:** non modificare o aggirare INC111, non usare FTP esplorativo come watt attestati, non forzare i workout nei 3 slot, non creare una seconda autorità UI e non modificare gli expected. R150 numerico/INC091 unscheduled ha test positivi delimitati; **NON è una versione prodotto stabile certificata**.

**Prossimi gate verso la stabilità effettiva:** in TEST con richiesta Flask `/analyze` **autenticata dal vero owner**, con ricevute realmente risolte RAW FIT, eseguire planner futuro → INC091 provenance → compilazione non schedulata → digest/seal → fueling → Card3 Jinja, conservando indipendente il veto HARD corrente; realizzare Card2 Tempo distinta e 7/7 goal con autorità unica; Q01–Q24 e browser/mobile, doppia seduta, rollback. Non inventare owner, FIT, slot o dosi. DTM **v1.0.74** vincolante, Card3 BH-001 RED, Card2 BH-004 RED, RAW/owner E2E NOT_VERIFIED, produzione **NO-GO**.


## 06/11/2026 · Fase 4.5 — Intervals FTP: eliminare falsi errori di comunicazione, non le prove scientifiche

**Richiesta atleta:** non trattare l'assenza di un vecchio test FTP qualificante come errore FTP, quando Intervals.icu fornisce una FTP rolling **datata** da usare come intervallo di riferimento. Non chiedere una validazione massimale automatica soltanto per discutere la prossima qualità.

**Confine normativo DTM v1.0.74:** un riferimento FTP provider non è una ricevuta di lavoro completato con recuperi comparabili. O6 per la prescrizione individuale Tempo conserva `prescription_watts` e validità; INC083/INC111 e l'issuer restano fail-closed. Mai promuovere `INTERVALS_DATED_FTP_EXPLORATORY` a `COMPARABLE_VERIFIED_REPEATED_WORK`, né modificare gli expected R135/R136 per ottenere CI verde.

**Implementazione nuova, esclusivamente candidata effimera R151 in CI TEST:**
- [builder verificato da hash R150](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/blob/fix/neon-report-egress-r196999/qa/nova_test_lab/build_inc132_ftp_reference_candidate.py): genera `R196.9.151` in checkout temporaneo, modifica solo interpretazione testo AI `ftp_anchor_text` e proiezione HTML/UI con il riferimento dato da `_nova_power_coaching_reference` (fonte originale). Mantiene valori, sorgenti e reason code nel Content Audit tecnico. R150 `the_lab_app.py` nel repo rimane invariato.
- [test candidato](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/blob/fix/neon-report-egress-r196999/qa/nova_test_lab/run_inc132_ftp_reference_candidate.py): FTP rolling datata di Intervals con vecchio `NO TEST-BACKED FTP` → comunicazione athlete-facing **AVAILABLE, riferimento contestuale**; data più vecchia ancora rappresentata come contesto più incerto; nessun valore inventato quando mancante; Jinja reale della sezione FTP senza `NO VALIDATED ANCHOR`, `REFRESH DUE`, codici sorgente tecnici. Nessun esame FTP automatico.
- [workflow isolato](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/blob/fix/neon-report-egress-r196999/.github/workflows/nova-inc132-ftp-reference-candidate.yml): verifica SHA256 baseline, diagnostica scientifica originale positiva/negativa, confronto AST per 8 funzioni science/issuer/auth con R150 immutata, generazione candidata, Flask `/healthz` e Jinja, numerico positivo con `_nova_inc091_compile_native` non schedulato; FTP senza prova di ripetibilità continua a essere respinta da INC083.
- **CI [42215898058](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42215898058): SUCCESS** `PASS_TEST_CANDIDATE_ONLY`. Tutti i controlli aggiuntivi sono passati, nessuna scrittura DB/Calendar/ledger, nuovo Snapshot, API esterna, deploy o secret letta.

**Limiti NON superati:** non è ancora una modifica committata al `the_lab_app.py` né distribuita; non prova acquisizione viva Intervals/owner-bound, RAW FIT, completezza Card3 BH-001, Card2 BH-004 o matrice Q01–Q24. I tre invarianti scientifici R135/R136 restano DRIFT per HARD day-of, distinti dall'FTP di coaching. Workflow storico R141 sul branch LAB continua a fallire per pin diverso; non è stato disattivato.

**Prossimi passi:** convalidare l'interfaccia completa nel percorso autenticato `/analyze` e `last_report` usando owner reale; verificare che l'FTP visualizzata appartenga all'owner e allo Snapshot e che non riemergano codici grezzi nei messaggi AI, chat e tutte le varianti delle card; mantenere separata la quality futura attestata senza slot dalle HARD day-of. Solo dopo le prove E2E proporre la promozione a nuova versione e un rollback verificato.

**Verdetto:** `FTP_PRESENTATION_CANDIDATE=PASS`, `R150_SCIENCE_AST=UNCHANGED`, `PRODUCTION=NO_GO`.
