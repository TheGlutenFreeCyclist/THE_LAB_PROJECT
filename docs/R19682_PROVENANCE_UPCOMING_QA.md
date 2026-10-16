# R196.8.2 · source-qualified repeatability badges and conditional quality UI

Real persisted CA at 2026-10-16 20:01 (R196.8.1) identified an activity with two ~7min descriptive segments, RAW_FALLBACK/ICU_INTERVALS and repeatability=null, while the history incorrectly carried “Excellent repeatability.” The existing score is a descriptive low-trust variance, NOT verified repeatability.

- Keep descriptive watts, work evidence, duration and historical structure untouched; remove only the unsupported excellent-repeatability badge and label descriptive degradation as UNVERIFIED INTERVAL BOUNDARIES when repeated-work source truth is not RESOLVED/HIGH, canonical and multi-rep.
- Verified canonical repeats retain the original badges and scores.
- Preserve athlete-facing “recheck recovery” condition for provisional quality (including the third Upcoming card) rather than replacing it with generic exploration text.
- Never use single-effort power best as repeated-work proof; leave R196.8 power-contract, range, non-punitive scoring and 3-card/fueling rules unchanged.
- Isolated focused tests: 5 pass in sandbox. Full application import/render, history replay, seven-goal E2E, Render deployment and new CA are not certified.
- Rollback by reverting this commit; do not force push or upload private audit data.
