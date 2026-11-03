# NOVA TEST LAB — UI / CONTENT / TIMING SUITE

Operational addition to INC103 / DTM v1.0.71, 2026-11-03.
**This is test infrastructure, not a change to the deployed application.**

## What runs

Public GitHub Actions workflow: `.github/workflows/nova-test-lab.yml`,
branch `fix/neon-report-egress-r196999`. Two jobs:
- `scientific-and-flask`: full Python/Flask R136 tests, full R115 baseline replay,
  seven-goal empty-evidence fail-closed matrix, and Coach Clock Rome local time
  boundary tests (06:30 and 18:30, both sides of DST fallback).
- `browser-ui`: installs real Chromium + Playwright 1.56, renders the ACTUAL
  Flask/Jinja/HTML/CSS/JS in an intercepted `https://nova-ui-lab.invalid/`
  browser origin. All external URLs are refused. Test viewports: **320, 390,
  768, 1280 px**. Maximum job time: 10 minutes.

The browser job runs TWO independent scenarios:

1. `--mode preview`: the genuine Flask `GET /preview` with synthetically
   generated training/wellness data. Test that all five panels exist and
   mobile accordion controls actually open; quality status is informative
   even when evidence disallows an issued workout; recovery shows required
   carbohydrate/protein fields; DOM IDs are unique; no page-width overflow;
   headings/body have a coherent computed font family; unexpected JavaScript
   page exceptions do not occur.
2. `--mode synthetic_quality`: calls the genuine preview pipeline and then,
   **after the live presentation adapter**, injects a controlled signed-like
   Card-3 view with a 5×3' plan while the chronological candidate 2×7' is
   unissued. Invokes the REAL INC101 recovery projection under explicitly
   **mocked owner/eligibility** guards. Checks that the full browser Card 3
   shows 5×3' and 350–370 W, and that Recovery shows the same canonical
   workout ID **once**, conditional/unscheduled, without the rejected 2×7'.
   This is a **UI/presentation contract**: it is NOT a cryptographic issuer
   certification, not an athlete-ready prescription, and not a real power
   target for any user.

On public synthetic data only, mobile and desktop screenshots of the
top viewport are stored as 3-day GitHub Actions artifacts. The public job has
NO real athlete data or provider credentials. The PWA Service Worker cannot
register in the intentionally isolated fake origin; that exact and expected
network-failure event is separately counted rather than reported as a genuine
JavaScript defect.

The runner also measures long paragraphs and minor panel overflow.
These are REVIEW signals, not arbitrary absolute UX thresholds: no normative
maximum text count has yet been approved.

## Private actual-context DOM QA

Private GitHub repository: `TheGlutenFreeCyclist/the-lab-db-backups`,
branch `nova-science-private-replay`. Workflow uses a PINNED public R136
code revision and a PRIVATE frozen personal R135 saved-report JSON.
The file is never copied to public GitHub or public artifacts. The test
calls the genuine Flask `GET /last-report`, with only the IO/login boundary
mocked to avoid production access. Runs the same five-panel Chromium checks
in all four viewports, without screenshot upload.

**Important limitation:** R135 issuer/future-plan attestation uses original
production HMAC identity/secrets. The CI runner does not have and must not
import those production credentials. Therefore this route provides
**saved-report presentation/regression evidence**, not a proven reproduction
of the currently signed authenticated Card 3 and Post-Workout Recovery.
The exact original R135 science replay is proved independently in the
existing private R115 runner (10/10 expected + mutation suite).

## Tests demanded by DTM INC103 and actual status

| Domain | Existing automated coverage | Important missing evidence |
|---|---|---|
| Quality shown vs safe absence | 7 goals fail closed, Card 3 descriptive fallback, synthetic 5×3 rendering | Full authenticated owner-bound issuer |
| Timing X vs Y | Rome AM/PM + DST boundary chronology; no backdated clock slots | Correctness of preferred day for each athlete's real availability |
| Quality watt/recovery pairing | Synthetic 5×3 vs discarded 2×7 across all Chromium viewports; Python actual INC101 | Real signed producer→issuer→Card3→Recovery E2E |
| Fueling | Actual `build_nutrition_plan`, Recovery DOM carbs/protein, identity | Complete tolerance/race-context scenario matrix |
| Text length | Audits paragraph sizes and surfaces review notes | UX content judgement by owner / editorial acceptance |
| Fonts | Checks browser computed font families and positive font sizes | Pixel-by-pixel typography review against approved visual baseline |
| Responsive | 320, 390, 768, 1280; accordions; scroll/overflow | Physical mobile/PWA OS-specific checks |
| Security | Anonymous QA route denied | Complete authenticated account/tenant E2E |

Do NOT conflate a green browser suite with closure of the missing evidence.

## Cost guardrails

- Public GitHub standard Ubuntu runners in a public repo: no GitHub Actions
  compute charge under GitHub public repo policy.
- Private repo runner consumes INCLUDED private GitHub Actions minutes (and
  can be billed if included usage is exhausted). No scheduled repeated runs.
- Browser job has 10-minute timeout; private job currently 5 minutes and may
  need to be increased to accommodate Chromium installation.
- Every test runs from existing frozen data. **Zero new Snapshots**, zero
  Intervals/AI calls. No Neon calls during replay.
- The Neon TEST hard quotas and personal/beta privacy rules stay intact.

### Executable commands

```bash
python -m unittest discover -s qa/nova_test_lab -p 'test_*.py' -v
python -m pip install playwright==1.56.0
python -m playwright install chromium
python qa/nova_test_lab/run_ui_browser.py --mode preview --json ui-audit.json
python qa/nova_test_lab/run_ui_browser.py --mode synthetic_quality --json ui-quality-audit.json
```

The private runner passes `--mode private --report <PRIVATE_JSON>`; NEVER
commit that report to the public branch or print athlete text.

## Promotion policy

Nothing from this branch automatically deploys on Render. `main` stays
unchanged. Match the pinned public code SHA in private Actions to the current
candidate when running release QA, and keep PASS/BLOCKED/NOT VERIFIED per
individual domain in the handover.
