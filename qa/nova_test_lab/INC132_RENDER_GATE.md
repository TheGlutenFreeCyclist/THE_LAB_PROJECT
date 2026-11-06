# INC132 QA acceptance seam — 2026-11-06 (TEST ONLY)

## Status
Two new files on the already authorized TEST branch:
- inc132_render_contract.py: synthetic payload-screening boundary (NOT imported in app).
- test_inc132_render_contract.py: 19 deterministic synthetic unittest methods.

This is **not** a new producer, workout compiler, authenticated UI, real issuer verification or scientific dose validation. Issuer flags and evidence IDs in tests are **fake attestations**, not cryptography or physiologic evidence. The module never authorizes training, scheduling or ledger changes.

## Checks
- Three distinct card roles; Card1 easy, Card2 Tempo/Z3 HARD, Card3 specific always present for allowed projections.
- Existing INC038 Tempo workout IDs tied to the correct 4 goal profiles.
- POWER_1, SPRINTER and ENDURANCE_BASE Tempo candidates **NOT APPROVED**.
- Owner, snapshot, digest, unique workout/plan IDs, explicit complete compilation/fueling metadata, requirement for a priority explanation.
- Historical snapshots have no active highlight. Health marker cannot choose or veto independently. HOLD does not remove future specific card. Injury restrictions override new hard offers.
- No duplicate quality completion, no calendar writes.

## Strict interpretation
Local/full offline package separately includes a more extensive render contract and tests (26 cases), Z2 four-format screening and scientific catalog (12 cases), browser mock at 320/390/1280, and archived R150. GitHub QA sources serve the same purpose but are not byte-identical. Neither suite satisfies official INC132 Q01–Q24 acceptance in real Flask/auth/issuer.

## RED/GREEN before integration
Before changing the_lab_app.py on TEST, reconcile the divergent runtime (TEST blob ec8a147b6dce5170467e9d47caf1d415cea7988b versus R150). Then attach the real canonical producer to these contracts, replace mock flags with authenticated attestations, verify cycling LT1 and FTP and per-goal dose, wire renderer to the issuer, run all 24 acceptance gates. Production remains **NO-GO**. No personal/production Neon operations authorized.

GitHub workflow nova-test-lab.yml may run on QA pushes; do not infer a passing run without reading Actions results. It still targets legacy R141 materialization, not verified R150.
