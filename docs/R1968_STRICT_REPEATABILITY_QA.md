# R196.8 — strict repeated-dose truth and observed PB in Upcoming Sessions

## Scope and evidence
R196.7 showed exploratory bands to athletes but retained an exact power_prescription.target_watts and could omit observed bests in the third canonical quality card. A completed 6-minute repeated set does not verify a 7-minute repeated set, and a single fresh 7-minute PB is only contextual observation.

This patch does not change canonical three-card ordering, session identity, fueling ownership or the complete content audit. It enriches compiled canonical quality sessions with direct exact-duration best-power-curve evidence when available, never interpolations.

## Scientific invariants
- Only strong canonical repeated events, matched to the selected activity and interval length, with enough repetitions and non-shorter recovery context, support a fixed repeated-work target.
- An activity without verified laps is not automatically comparable just because the overall workout completed.
- Longer target intervals than verified repeats, or a novel durability/race-transfer preload, remain exploratory: target_watts is null, mode EXPLORATORY_RANGE, confidence LOW, and structure-only / non-punitive power assessment.
- Valid FTP-derived starters are provisional ranges, not completed repeatability: target_watts is null, mode PROVISIONAL_RANGE.
- Missing or noncomparable recovery causes the direct-work prescription to fail closed.
- An observed best is displayed with its source/duration and a caution about fresh efforts. No interpolation is presented as a measured best.

## Evidence levels
- Source review and isolated negative/unit tests: targeted PASS.
- Full application py_compile and unittest on repository HEAD: NOT RUN in this connector-only environment; GitHub CI must supply an independent result.
- Seven-goal end-to-end matrix, historical replay, mobile browser, live Snapshot/deploy: NOT RUN. Do not infer production certification.
- The 2026-10-16 18:34 Content Audit records R196.6, thus cannot certify R196.8 deployment.

## Rollback
Revert only the R196.8 commit via GitHub (non-force). Never overwrite private user audits in the repository.
