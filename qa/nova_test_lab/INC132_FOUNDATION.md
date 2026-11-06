# INC132 · LAB research scaffold · 2026-11-06

**Branch:** `fix/neon-report-egress-r196999`. **Not app-integrated; PRODUCTION NO-GO.**

This folder holds test-only research hypotheses for Card 1 Z2 and Card 2 complementary Tempo/Z3. The canonical producer, issuer, Card 3, ledger, calendar, Health, HMAC and source `the_lab_app.py` are **untouched**. No runnable workout or athlete-facing recommendation has been created.

## Verified baseline discrepancy

The source `the_lab_app.py` on `main` is Git blob `ca07e9f135328c5c7e4aa1c4a5be9711a53cd714`, matching the delivered R150. Source on this TEST branch was `ec8a147b6dce5170467e9d47caf1d415cea7988b` before INC132. Their histories diverge (8 commits ahead on main, 104 ahead on TEST) and TEST has separate QA files. Do not blindly replace the branch source or merge main. Reconcile before a true runtime modification.

## Scientific foundation

- Card 1 Z2 must remain below an athlete-specific **LT1/VT1** threshold. Continuous, variable and interval structures are plausible according to the 2025 experts' viewpoint [PMID 40010355](https://pubmed.ncbi.nlm.nih.gov/40010355/). Four *research formats* exist in `inc132_candidate_gate.py` (steady, easy intervals, progressive within Z2, comfortable cadence changes); neither universally valid intervals nor automatic watts are claimed.
- Cadence changes must not be conflated with torque/strength gains; imposed very-low-cadence protocols have inconsistent evidence [PMID 28095074](https://pubmed.ncbi.nlm.nih.gov/28095074/) and a 2026 cycling review [PMID 42828469](https://pubmed.ncbi.nlm.nih.gov/42828469/). No compulsory 40-60 rpm intervention.
- Card 2 cycling **seven-zone Z3 Tempo is HARD**. Treat as an alternative to Card 3, not an additional weekly quality. INC038 contains pre-existing mechanics for four goals (POWER_5, VO2MAX, POWER_20, TIME_TRIAL); POWER_1, SPRINTER and ENDURANCE_BASE remain **RESEARCH_ONLY**, even with verified FTP.
- The 2025 individual participant meta-analysis [PMID 39888556](https://pubmed.ncbi.nlm.nih.gov/39888556/) supports no blanket distribution superiority. A producer must decide from actual goal, exposures, fatigue, recovery, dose and verified data, never for attractive 50/50 UI statistics.

## Test commands

```bash
cd qa/nova_test_lab
python -m unittest -v test_inc132_candidate_gate.py
```

These tests use synthetic values and **DO NOT** establish athlete-specific dose validity or Flask/UI/auth E2E. Fields `potential_power_watts` are a screened *hypothetical* value, not a recommendation. Every result has `executable=False`, `scheduled=False`, `fueling=None`, `recommended_priority=None` and `ledger_write=False`. Missing, stale, cross-owner, injury, unreviewed HARD exposure and unvalidated 3-goal dose fail closed.

## Integration gates still blocked

1. Reconcile the divergent branch source and produce RED tests for C2, C3 and Z2 within the actual app.
2. Within ONE canonical producer: construct two unique sealed quality candidates, each with verified personal watts, progressions and fueling. Preserve every real chronological second session.
3. Scientifically validate new Tempo roles and doses for the other three goals; do not upgrade hypotheses automatically.
4. Implement producer-owned recommendation and a single snapshot-bound border, no local sticky state. Card 3 visible except explicit injury; future ≠ today's clearance.
5. Verified activity ID must reconcile only the executed workout. Test same-day double sessions, ownership, stale Health and Load Last Report.
6. Real authenticated Flask/Jinja/Chromium and owner-scope gates Q01–Q24 must pass in TEST before discussing production.

**Current status:** OFFLINE_SCAFFOLD only; runtime LAB and release gates remain NOT_VERIFIED / NO-GO.
