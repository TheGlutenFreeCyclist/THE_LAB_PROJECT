# THE LAB / Nova — R196.4 rhythm scheduling (2026-10-15)

Scope: **weekday learning and audit only**. Parent `5c0c99315fe9090458fb35b701d52744edb707ce` (R196.3). No changes to hard-workout power targets, the seven primary goals, recovery/race overrides, audit-download button, or upcoming-card design.

## Root cause / correction
R196.3 rounded the blended weekly training-day frequency and selected the top N weekdays. Consequently a separately evidenced day could be discarded solely because it was ranked sixth. R196.4 separates **expected weekly volume** from **candidate-day eligibility**. An eligible weekday now requires repeated evidence: at least 2 of its recent observed occurrences with >=2/3 recent frequency, or established >=2/3 frequency across >=4 opportunities with at least 3 observations and >=0.50 blended score. The training rhythm still blends 21d recent and 42d established priors, now with up to **180d** longer-term observations from the **already fetched 365d Intervals history**. Recovery, race and explicit scheduling rules retain authority.

For irregular 4–5d/week patterns that would otherwise make all seven weekdays eligible, the scheduler treats uniform low-confidence rhythms as `LOW`, preserving its gap-based fallback rather than implicitly scheduling every day.

Diagnostic `training_rhythm.weekday_evidence` exposes observed/possible counts (21/42/180d), recent recorded dates, support decision and reason. It does **not** prove that Intervals has all of an athlete's activities; compare with raw upstream data before attributing missing observations to Intervals. `NO SESSION YET` with misleading `missed` styling becomes `NOT SCHEDULED` when no candidate existed; explicit blocks and completed workouts retain their separate states. The Coach Clock 14d explanatory text was corrected to 21d.

## Verification and limitations
- Python `py_compile`: PASS on complete 3.39MB module.
- Local synthetic regression suite: **12/12 PASS**, covering a previously excluded sixth day, unsupported Friday, sparse history, 1d/week, everyday vs irregular patterns, mixed modalities, and calendar blackouts.
- Existing R196.2 atomic test groups: **21/21 PASS**.
- This repository additionally includes `tests/test_r1964_rhythm.py` (six isolated evidence-policy regressions).
- Full historical handover suite: **NOT CERTIFIED** in this environment. Several archived R196.1 tests rely on old candidate implementations and assert superseded behavior; one R196.3 test hardcodes its previous version string. Do not misrepresent that as a production or complete CI PASS.
- Existing science risks SCI-001/SCI-002 remain OPEN. No live tester re-snapshot, Render deploy status, or real Intervals reconciliation was performed as part of this code commit.

## Operational rollback
A rollback should use a new revert commit, not force-push. Confirm the branch HEAD first, then `git revert <R1964_COMMIT>`; leave historic R196.2 and R196.3 unaffected. Validate a real tester Snapshot and audit evidence before calling the fix proven in production.
