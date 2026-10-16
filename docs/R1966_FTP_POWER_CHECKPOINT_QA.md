# THE LAB / Nova R196.6 — evidence-gated FTP, exploratory targets and checkpoints
Baseline: R196.5 `33b900556c0640e2c22de39281e7aa510ca44d39`. Scope: four targeted fixes; no changes to seven-goal selector, Energy Bank, rhythm, or race-safety authority.

## FTP provenance
Only an explicit Intervals FTP_UP with recorded wattage and an effort of at least 1200 seconds qualifies as a *test-derived FTP estimate*. 20–29 minutes remains an estimate-only reference (no precise numeric starter); 30+ minutes can support a conservative starter target while fresh (<=120 days). These are NOT direct physiological FTP measurements. Unknown-duration and shorter FTP_UP records, including legacy persisted entries, are excluded from operational anchors. The newest qualifying effort takes priority over the largest automatic FTP_UP. 120–180 day evidence is aging and not usable as a precise starter; >180 days is stale. The raw Intervals rolling and power-model values remain diagnostic, never athlete-facing authority.

## New interval duration
If the best verified repeated evidence is shorter than the prescribed interval, mark the target LOW confidence / EXPLORATORY / non-punitive. Keep the challenging central target, widen the lower side by 20 W, and record actual power and structural completion. Do not grade failure for missing experimental power. Same/longer verified repetitions retain existing strict contracts. No permission to ignore pain, recovery or race-safety overrides.

## Formal checkpoint consistency
A formally completed, activity-linked, exact-duration checkpoint for the same goal in the last 21 days is marked COMPLETED/not due. This prevents TEST SOON contradicting a fresh verified completion, without banning future rechecks beyond that evidence window.

## Athlete-facing UI
Keep power PB achievements. Hide activity rolling/PM FTP signal panels from the breakthrough card; replace the automatically celebratory message. Hide rolling FTP from the FTP test reference card; report absence of a qualifying test instead of an invented anchor. Leave raw sources in QA.

## Verification and limitations
- Local complete-module syntax check on the reconstructed R196.4 source with equivalent R196.6 modifications: PASS.
- Isolated policy tests: 13/13 PASS (5-minute rejection, 20/30-minute distinction, expired/missing anchors, nonpunitive new durations, same-duration strictness, fresh and mismatched checkpoints).
- Jinja template parsing on the reconstructed R196.4 UI with equivalent modifications: PASS.
- This is *not* a certified complete-R196.6 test suite on the R196.5 GitHub baseline. Full seven-goal replay, persisted historical anchors, browser QA, Render runtime and real-account CA are NOT certified; do not claim production PASS.
- SCI-001/SCI-002 remain open: no failed exploratory attempt may be counted as disproving capability; no successful single attempt automatically proves sustainable repeatability.

## Rollback
Confirm current HEAD, then create a new git revert commit (never force-push). Verify account snapshots, sources and test lineage before declaring a release science-PASS.
