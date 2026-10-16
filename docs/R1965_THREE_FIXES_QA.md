# THE LAB / Nova — R196.5 atomic UI and scoring corrections

Parent: 3bf7f89f7b1b079d30d807e039dc4322f489709f (R196.4).

1. Replaced redundant "no AI call" copy in relevant athlete journal, note, consent, and Nova-answer surfaces. Historic provider and admin integrations are **NOT removed**; removing dormant routes or secrets requires a separately tested migration.
2. Energy Bank: replaced coarse initialization with a continuous, bounded relative heuristic using TSB, ATL/CTL, sleep difference versus individual habitual duration, sleep quality, and numeric deviation from available HRV/RHR/sleep-score references. Daily load, movement, health overrides, and existing cost logic stay intact. \`energy_components\` makes each contribution auditable. This is **not** a physiological percentage of reserves.
3. The former "PLAN ADHERENCE" is now truthfully displayed as **STRATEGY ALIGNMENT**, retaining prior numeric methodology and historical audit keys. Added a distinct *Nova quality execution* indicator drawn only from attributable archived quality contracts (FULFILLED with a linked activity versus explicit MISSED_UNEXECUTED). Unknown links, cancelled/superseded obligations, future commitments, easy days and rest are excluded. No whole-plan compliance score is invented. The number is unavailable when historical attribution is insufficient.

Verification of changes against an R196.4 copy: \`python -m py_compile the_lab_app.py\` PASS; local R196.5 isolated tests 12/12 PASS; R196.4 rhythm tests 6/6 PASS. The full archival suite did not pass in this environment (missing old renamed candidate files, and R196.3 version hardcoding); there is no certified full-suite green status. Flask is unavailable here, so an actual server HTML render/mobile E2E test was not performed. No live tester follow-up, Intervals sync or Render deployment status verified. SCI-001/SCI-002 unchanged.

**Rollback:** Verify main HEAD, use a new revert commit for this one commit; never force push. Confirm HTML rendering and fresh QA/CA on a real R196.5 snapshot before treating the work as proven in production.
