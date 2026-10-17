# R196.8.4 · Missing sleep neutrality and corroborated marginal-load warning

## Source evidence
The beta Snapshot at 2026-10-17 18:57 reports POWER_20, sleep_quality=null, RHR and HRV within baseline, habitual sleep within range, ATL/CTL=1.20, 7d load=495 vs prior weekly=467 (ratio 1.06), CTL 28d +10.6, ramp +2.2. Recovery state is driven by ACUTE_CHRONIC_LOAD alone. Nova action HOLD and quality window RECOVERY HOLD generate EASY_ONLY. This is **not** direct evidence of low sleep quality. An older 2x12-min fixed watt anchor is already marked non-executable.

## Invariants
1. In readiness, missing sleep quality no longer falls into the *poor quality* branch. Grey sleep duration stays neutral with missing quality; objectively short sleep still contributes an independent modest warning.
2. The existing 1.18 acute-to-chronic ratio threshold becomes a *load watch* rather than an unconditional hold **only** when it is the sole driver, it is below 1.25, weekly load is at most 1.15x established baseline, CTL growth and moderate ramp corroborate, HRV/RHR/habitual sleep are normal and there are no adverse subjective or health signals.
3. Never release high/multiple load alarms, real poor sleep, red physiological markers, health/race restrictions, or uncertain baseline data.
4. De-escalation does not prescribe any intensity. Workout selection, spacing, evidence-based power and validation/test eligibility retain authority. Goal-independent, all seven goals.
5. Never artificially raise measured fitness or best watts. The missing 12–20min canonical exposure remains an evidence gap.

## Verification
- 12 isolated policy tests passed locally before integration.
- 14 repo regression tests included (12 policy gates, 1 sleep behavior, 1 wiring).
- Full app integration, Render deploy and a new post-fix beta Snapshot are **not** certified.

Rollback this commit atomically if deployment shows any unexpected issue.
