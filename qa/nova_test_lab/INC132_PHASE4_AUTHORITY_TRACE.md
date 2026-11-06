# INC132 · Fase 4 — tracciatura delle autorità R150 (sola TEST)

**Stato:** analisi statica e confronto con il diagnostico esistente, NON implementazione prodotto, NON validazione scientifica né E2E.  
**Norma:** DTM v1.0.74, BH-000–BH-008, senza modificarlo.  
**Baseline:** `the_lab_app.py` SHA256 `6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73`; Git blob `ca07e9f135328c5c7e4aa1c4a5be9711a53cd714`.  
**HEAD prima di questa scrittura:** `c0d395da435fa93729298bf7db87e310bf360a5e`, branch `fix/neon-report-egress-r196999`.  
**Fonte:** archivio di handover Fase 3.1 del 06/11/2026 e analisi AST del sorgente R150, confrontati con il branch TEST. Numeri di riga riferiti a R150 IMMUTATA.

## 1. Percorsi realmente distinti

| Responsabilità | Codice R150 | Significato e vincolo |
|---|---|---|
| Punto di composizione Snapshot | `the_lab_app.py:29265–29272,29308–29316,29447–29450` | Prima issuer della quality odierna, poi pianificazione futura indipendente, infine attestazione dopo la composizione. |
| Issuer HARD odierno | `_nova_r196956_build_offer`, wrapper finale `:66696–66765`; `_nova_inc076_seal_ok` `:65265–65279` | Il veto `EASY_ONLY` deve restare applicato. HMAC dell'offerta non è prova di libertà di esecuzione futura. |
| Planner scientifico futuro | `_nova_inc056_plan_result` `:65719–65770` | Seleziona tramite `_nova_inc088_scientific_candidate` `:65636–65716`; verifica replay watt, ma genera deliberatamente solo `mechanics`, `workout=None`, `PERSONAL_POWER_NOT_COMPILED`. |
| Tentativo di compilazione futura completa | `_nova_inc050_future_quality` finale `:65906–65963` | Il ramo INC091 richiede `PLANNED_NOT_CLEARED`, nessuna offerta attiva e nessun infortunio dichiarato. Prima prova `_nova_inc091_truth`, poi `_nova_inc091_compile_native`. |
| Provenienza e confine auth | `_nova_inc091_truth` (wrapper finale `:66441–66482`, precedente `:65788–65838`) | Richiede request Flask `analyze`, attore owner e eventi server `RESOLVED` coerenti. Una stringa `DEVICE_LAPS` in fixture offline NON costituisce la prova. L'ulteriore ricevuta RAW FIT resta esplicitamente NON verificata. |
| Compilazione scientifica | `_nova_inc091_compile_native` (wrapper finale `:66488–66545`, precedente `:65841–65903`) | Replay originale, banda W, renderer canonico, `_v19697_session_envelope`, durata e `_v19696_execution_contract`; nessun giorno/slot inventato. |
| Attestazione futuro | `_nova_inc051_attest_future_snapshot` `:66037–66079`; `_nova_inc091_eligible` `:65976–66034` | Ricontrolla owner, digest, replay, composizione, fueling e `authority_seal`. Il piano futuro rimane `not_issued/not_scheduled`: non è l'issuer di HARD corrente. |
| Presentazione C3 | `_nova_r1969104_canonical_card3` `:66082–66110` | Solo dati eleggibili e attestati; UI non inventa dose. |
| Contrasto C07/BH-001 | `HOME_PAGE` patch INC121 `:67549–67569` | Ancora previsto placeholder grigio/inattivo quando quality è in Card1/2: incompatibile con nuova Card3 sempre completa e con identità condivisa. Da riformare mantenendo una sola prescrizione/ledger. |

## 2. Blocco preciso (provenienza ≠ dose ≠ clearance)

Nel probe reale sintetico CI `42194585623`, `decision=TRAIN`, prescrizione `EASY_ONLY`, rifiuti `CURRENT_NOVA_DECISION_DOES_NOT_AUTHORIZE_HARD`. Il planner indipendente è `PLANNED_NOT_CLEARED`, con `mechanics` ma senza `workout`, `COMPATIBLE_STRUCTURE_ONLY_NOT_A_QUALITY`. Il probe è **SUCCESS diagnostico** perché non falsifica l'issuer; la feature C3 è **RED**.

La via INC091 *può teoricamente* arrivare a `COMPILED_UNSCHEDULED` con watt e fueling, ma questa fixture offline non soddisfa il gate di provenance owner-bound nella richiesta autenticata, né verifica ricevute RAW byte. Non dichiarare coperto il ramo positivo compilato; non usare mock, `strong=True`, `DEVICE_LAPS` autoassegnato o HMAC test come prova reale.

### Matrice sperimentale da implementare/testare

| Scenario | Numeric science replay | Auth/provenienza | HARD oggi | C3 futura | Interpretazione |
|---|---|---|---|---|---|
| N0: nessuna evidenza, goal valido | Negativo | No | Negata | RED, non inventare | Fail-closed necessario, prodotto ancora non conforme BH-001 |
| N1: ripetizioni sintetiche comparabili | Testare positivo/negativo col modello originale | Non attestata | Negata se `EASY_ONLY` | Non chiamare completa | Test soltanto numerico, non prova della feature |
| P1: evento raw realmente validato, owner-binding e replay medesimo Snapshot (TEST autorizzato) | Positivo richiesto | Positiva richiesta | Separata | Compilazione+attestazione+fueling richiesti | **NOT_VERIFIED**, non simulare ricevute come se fossero vere |
| X1: altra identità, stale, replay diverso, injury `NO INTENSITY` | Irrilevante | Invalida / safety stop | Negata | Fail-closed secondo injury e provenance | Da eseguire su Flask/auth con isolamento rigoroso |
| X2: quality già pianificata in Card1/2 | Dipende da contratto | Medesimo owner/ID | Nessuna doppia HARD | Medesima quality leggibile in C3 | R150 ha placeholder grigio da correggere prima del GO |

## 3. Sequenza obbligata di sviluppo

1. Scrivere test RED veri per due percorsi separati: un workout futuro completo e sottoposto a provenance/compilatore/attestazione; un HARD day-of rifiutato se `EASY_ONLY`. I test numerici sintetici sono *non certificanti*.
2. Verificare su runtime autorizzato il percorso INC091 con ricevuta raw e boundary owner; in assenza di dato autentico il gate rimane NOT_VERIFIED, non bypassato.
3. Implementare in TEST BH-001 Card3, rimuovendo il placeholder C07 **senza clonare il workout, la prescription authority o il ledger**; assicurare titolo, fasi, W, durata, fueling e ID.
4. Solo dopo, introdurre Card2 Tempo come alternativa nello *stesso producer*, con dose distinta e controlli rigorosi per ciascuno dei 7 goal (3 ancora RESEARCH_ONLY).
5. Card1 Z2 sotto LT1 attestata; arbitro di priorità; singolo bordo snapshot-bound; Jinja/Flask/auth/mobile; matrice Q01–Q24. Nessun deploy né modifica a produzione/Neon/Render/main.

## 4. Gate attuali

- `TEST_BRANCH_ALIGNED=PASS`; `R150_LOCAL_SHA256=PASS`; `STATIC_AUTHORITY_TRACE=COMPLETE`.
- `SYNTHETIC_NUMERIC_FOUNDATION=PREVIOUS_76_PASS_NOT_REVALIDATED_HERE`.
- `FUTURE_FULL_WORKOUT_AUTHENTICATED=NOT_VERIFIED`; `CARD3_BH001=RED`; `CARD2_RUNTIME=NOT_IMPLEMENTED`.
- `ISSUER_LIVE_AUTH=NOT_VERIFIED`; `RAW_FIT_RECEIPT=NOT_VERIFIED`; `Q01_Q24=NOT_VERIFIED`.
- `PRODUCTION=NO_GO`. Il workflow storico R141 è ancora da migrare con controllo indipendente; NON disattivare i test.

_Nessun dato privato, scrittura ledger, calendario, deploy o cambio R150 in questa tracciatura._

## 5. Evidenza nuova Fase 4, CI 42197108259 (06/11/2026)

[CI TEST](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42197108259), commit `1208fc40e97fc6c05a919e657fd28f5a350bb6db`: **SUCCESS di probe isolato**; sono stati eseguiti sul vero R150 i due script `run_inc132_issuer_gate_diagnostic.py` e `run_inc132_phase4_science_split_probe.py`.

- Riproduzione legacy: `EASY_ONLY`, due slot HARD respinti, planner `PLANNED_NOT_CLEARED`, sola `mechanics`, nessun workout futuro, nessuna offerta issuer.
- Nuovo contrasto controllato: fixture di ripetizioni sintetiche → `synthetic_numeric_positive=true`, `native_compiler_observation=NUMERIC_COMPILED_NOT_AUTHENTICATED`. La matematica di watt e il compilatore *possono* funzionare in isolamento.
- Evidenza assente / watt alterati → rifiutati; accesso alla provenance fuori dalla request autenticata → rifiutato. Non è stata simulata una ricevuta RAW FIT né costruito un owner autenticato fittizio.
- `live_authenticated_quality_full=NOT_VERIFIED`; `live_raw_fit_byte_receipt=NOT_VERIFIED`; `card3_bh001=RED`; `card2_runtime=NOT_IMPLEMENTED`; `production=NO_GO`.
- Il workflow storico R141 non è stato riparato né escluso. Nessun cambiamento al sorgente `the_lab_app.py`.

**Prossimo gate obbligato:** test autenticato del percorso `INC091` con sorgente realmente attestata e intera catena owner→compiled future→fueling→seal→Jinja, mantenendo indipendente il veto HARD day-of. In assenza di provenienza verificata, segnare RED/NOT_VERIFIED, non creare una falsa fixture positiva.

## 6. Fase 4 / BH-001 — correzione C07 candidata, integrazione reale SOLO nella CI TEST (06/11/2026)

**DTM normativo fermo:** v1.0.74 SHA256 `7ebd387abee2ef1479e26000c0244928c9bdfb1689882cb77ff567c6fabc3a27`. Fonte: pacchetto di handover Fase 4, BH-000–BH-008. La parte C07 non può rendere grigia Card3; Card2 deve essere diversa e scientificamente validata.

- RED baseline R150: presenza del placeholder INC121; un HARD di calendario anche differente può bloccare il display Card 3.
- GREEN **solo renderer isolato**: `qa/nova_test_lab/inc132_card3_mirror.py` trasforma il template, senza nuova selezione/issuer/ledger/calendario, e `run_inc132_card3_mirror_probe.py` renderizza il vero Jinja con (1) stesso workout ID, (2) altro HARD calendario, (3) Card3 non attestate, (4) drift guard. CI [42199698880](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42199698880): SUCCESS.
- GREEN **app sorgente candidata transitoria**, senza commit app: `build_inc132_c07_candidate.py` deriva R151 dal R150 con SHA-256 attestato. Artefatto effimero Git blob `1203822a8ffe5e1879e6ddd3a65e795b8211ff35`, SHA256 `e4ba3cbc34dec545f7ffc0c5b44950f5bb1178e6a801b397527118b174e02d7d`. La [CI 42200521995](https://github.com/TheGlutenFreeCyclist/THE_LAB_PROJECT/actions/runs/42200521995) ha verificato sorgente, `py_compile`, Flask import, Jinja, `/healthz`, rendering ID uguale / HARD estranea e stato incompleto fail-closed: SUCCESS.
- Nessuna modifica di `the_lab_app.py` persistentemente nel branch GitHub: resta il blob `ca07e9f135328c5c7e4aa1c4a5be9711a53cd714` (R150). Nessun deploy, nessuna scrittura database/ledger/calendario, e nessun accesso alla provenienza privata.
- **Restano RED/NOT_VERIFIED:** C3 sempre completa per tutti sette goal e ogni Snapshot; dose attesa da prova vera autenticata RAW, completa fino al fueling; Card2 Tempo individualizzata; arbitro/priority; E2E reale owner-bound, browser/mobile; matrice Q01–Q24. L'app candidata R151 non è una release.

**Sequenza successiva:** preservare la sorgente R150 finché non esistono prove end-to-end e rollback; diagnosticare i sette goal sul vero catalogo canonico, separare l'ammissibilità scientifica dalla selezione della priorità e non riempire C2 con template `RESEARCH_ONLY`. Nessun GO.
