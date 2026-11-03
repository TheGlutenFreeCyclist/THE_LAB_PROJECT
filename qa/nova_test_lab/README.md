# NOVA TEST LAB — isolamento senza Neon

**Attivato il 03/11/2026 sul branch esistente `fix/neon-report-egress-r196999`.**
Non è produzione e NON modifica `main`. Il branch è stato riallineato alla R196.9.136 tramite un merge commit a due genitori (storia del vecchio branch conservata). Render THE_LAB_PROJECT segue soltanto `main`: i push qui non fanno deploy produttivi.

## Funzioni operative

- Workflow `.github/workflows/nova-test-lab.yml`: scatta a ogni push ai file del laboratorio, alle dipendenze o al sorgente applicativo, **sul solo branch del laboratorio**.
- Installa Python 3.11 e le dipendenze reali del repository, incluso Flask.
- Importa `the_lab_app.py` completo e prova `/healthz` e la protezione di `/qa/nova-replay` via client Flask, senza avviare un web server pubblico.
- Esegue il calcolo nutrizionale reale su casi **sintetici**, controlla dose/watt/workout ID, proiezione INC101, template Jinja, identità Card 3/Recovery e assenza di mutazioni nel report.
- Esegue anche la vera pipeline deterministica R115 completa su un contesto POWER_5 senza evidenze, richiedendo esito fail-closed (zero quality hard emesse) e replay ripetibile. Test obbligatori: **9**, senza accessi esterni.
- Pubblica soltanto log PASS/FAIL dei casi sintetici, conservati come artifact per 7 giorni.
- Runner limitato a 10 minuti, niente schedule ricorrente, niente nuovi servizi Render o Neon, niente invio di segreti.
- Nessun `DATABASE_URL`, `THE_LAB_OWNER_DATABASE_URL`, Intervals.icu, Garmin o chiave AI nel processo del test. Queste variabili sono forzate a stringhe vuote prima dell'importazione.

## Esecuzione remota

Aprire GitHub > THE_LAB_PROJECT > Actions > **NOVA Test Lab (isolated, no Neon)** e consultare il run del branch. Una modifica ai test, al sorgente o al workflow sul branch avvia automaticamente il controllo. La generazione manuale via `workflow_dispatch` su branch non-default dipende dalle regole GitHub Actions; il trigger di push è quello già validato.

Il workflow è **limitato a quel branch** e non implementa un deploy automatico da GitHub a Render. Non confondere questo runner con una copia completa dell'app pubblicamente raggiungibile.

## Replay R115 con fixture privata (facoltativo)

Se esiste una fixture reale già esportata e **conservata fuori dalla repository**, su un ambiente isolato con le dipendenze installate:

```bash
python qa/nova_test_lab/replay_fixture.py /path/privato/fixture_nova_R115.json
```

Il comando esegue `_v115_replay_nova_core`, confronta le invarianti attese della fixture e prova la mutation suite, mostrando **soltanto stato e nomi delle invarianti fallite**. Non preleva la fixture né richiede un nuovo Snapshot. Non inserire questa fixture nel repo pubblico, nei commenti PR o negli artifact GitHub. Questo replay non è ancora attivato automaticamente nel workflow in assenza di dati sintetici validi o di un canale privato per le fixture.

## Limiti espliciti

- Nessuna validazione di Snapshot live autenticato, emissione reale issuer, persistenza owner-bound con Neon, DOM Chrome/Android, Intervals.icu o beta tester.
- Il caso 5×3' / 2×7' della suite di base è **sintetico**; non è una prova del report personale né dello stato del motore su nuova acquisizione.
- Non è stato introdotto un nuovo piano a pagamento. GitHub Actions applica i propri limiti d'utilizzo e le condizioni di fatturazione correnti: verificare l'account se cambiano.
- Il sorgente e DTM in `main` rimangono invariati. L'autorizzazione dell'owner del 03/11/2026 riguarda il setup del laboratorio su branch non produttivo; NON dà GO a promuovere modifiche del motore sulla produzione.
- Lo stato di una suite PASS certifica soltanto i controlli nominati. Ogni altra verifica resta NOT VERIFIED.

## Registro operativo

- Branch originario: `115d84a3`; codice R136 `main` di partenza: `a5fc7028`.
- Merge di riallineamento: `cab5267a`.
- Primo run CI: `41604146958`, 6/7 PASS (assert test HTTP attendeva 302, Flask risponde correttamente 303).
- Secondo run CI: `41604254482`, **7/7 PASS**; corretto solo l'assert HTTP.
- Run ampliato: `41604844325`, **9/9 PASS**, inclusa pipeline core R115 reale con input sintetici. Il probe esplorativo ha prodotto 47 campi senza emettere una falsa quality.
- Nessun accesso al database di produzione; nessun nuovo Snapshot.

Il laboratorio serve a rendere economiche e ripetibili le regressioni. L'obiettivo successivo è aggiungere fixture sintetiche **con evidenze sufficienti per una quality watt/dose valida** e un circuito sicuro per le fixture reali, senza pubblicare dati personali.
