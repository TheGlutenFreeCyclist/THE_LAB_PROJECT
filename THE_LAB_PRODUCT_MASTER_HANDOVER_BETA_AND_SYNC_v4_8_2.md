# THE LAB PRODUCT — MASTER HANDOVER
## Beta testing, multi-athlete architecture, sync with personal THE LAB

**Handover date:** 3 September 2026  
**Current Product release candidate:** `THE_LAB_PRODUCT_v4_8_2_POWER_CURVE_VO2_HISTORY_TRAINING_JOURNEY.py` / deploy `app.py` V4.8.2  
**Immediate Product base used for V4.8.2:** V4.8.1 — Preflight/Unavailable/VO₂ corrective candidate (V4.8, V4.7 remain preserved)  
**Repository:** private GitHub repository `THE_LAB_project`  
**Deployment:** separate Render Web Service  
**Database:** separate Neon PostgreSQL project (500 MB free tier currently used by this project)  
**Client:** installable PWA; no APK/native branch at this stage.




# V4.8.2 UPDATE — POWER-CURVE RESILIENCE + VO₂ HISTORY MERGE + BEFORE → DECISION → NOW

V4.8.2 is a **new complete Product release candidate built from the full V4.8.1 file**. V4.8.1 is preserved untouched. There are no new database migrations, dependencies, Render secrets or changes to the Product/Personal Neon split. Keep the Product Gunicorn Start Command at:

`python -m gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30`

## 1. Best Wattage Output / 42-day power-curve resilience
The 42-day Intervals.icu power curve now receives one bounded retry because it is the shared source for Best Wattage Output, recent CP/W′ and today's Intervals 5-minute VO₂ estimate. The season (`s0`) curve is secondary and cannot blank current 42-day outputs if it fails.

If the fresh 42-day curve is still unavailable after the bounded retry, Best Wattage Output may retain the last valid stored values from the athlete's Last Report. The UI explicitly labels that state; stored data never masquerades as a fresh curve. Fresh Intervals data always wins.

## 2. VO₂ history no longer collapses to only today
V4.8.1 recovered today's performance VO₂ when all historical checkpoints failed, but because the fresh series was then technically non-empty, the previous stored historical series was not used. V4.8.2 fixes that logic.

The performance and wearable VO₂ series are now **merged by date**:
- stored historical checkpoints provide continuity;
- fresh checkpoints replace stored values on the same date;
- a single fresh current point cannot erase the previous longitudinal history;
- today's already-fetched 42-day power curve is reused for the current performance VO₂ point instead of making a duplicate request;
- historical power-curve calls use modest concurrency and remain best-effort.

## 3. Training Direction historical journey — BEFORE → DECISION → NOW
The deterministic Training Direction engine now reconstructs how the athlete trained **before the current declared block** using the Intervals activity data already present in the 90-day Snapshot payload. No extra Intervals endpoint is required.

The new shared Live / Preview / Stored Report block shows:
- **BEFORE YOUR CURRENT BLOCK** — observed model and Low/Moderate/High distribution from the 28 days immediately before `started_on`;
- if there are fewer than 3 usable pre-block sessions, the historical window expands to 42 days;
- **YOUR DECISION** — the athlete-declared distribution and primary goal plus the declaration date;
- **NOW** — observed post-selection model, current Low/Moderate/High distribution and current adherence state.

This is intentionally descriptive history, not retroactive scoring. **No pre-selection session can affect current Plan Adherence.** Adherence still starts exactly at the strategy plan `started_on` date and remains capped by the existing rolling 28-day current-block window.

Example narrative:
`PYRAMIDAL before → athlete chose POLARIZED · 5 MIN POWER → current block reads POLARIZED`

If the current block has too little post-selection data, NOW remains `LEARNING` while BEFORE can still be shown independently.

## 4. AI / scientific ownership
`training_direction_text()` now includes the historical previous-block context so the AI can explain the transition, but Python remains authoritative for historical classification, declared intent, current classification and adherence. The existing health/restriction/race/recovery priority hierarchy is unchanged.

The following scientific/runtime functions are source-identical to V4.8.1: `compute_metrics`, `build_training_state`, `build_physiological_state`, `build_advanced_physiology_metrics`, `build_aerobic_efficiency`, `build_power_model`, `build_metabolic_context`, `build_nutrition_plan`, `build_coach_clock`, `build_week_memory`, `build_previous_training_blocks`, `build_heat_response_pattern`, personal form/fatigue thresholds and health override functions. Strategy persistence and pre-Snapshot form persistence are also unchanged.

## 5. V4.8.2 regression checks
Completed on the final candidate:
- `python -m py_compile`: PASS.
- Full module import with Flask/Werkzeug test stubs: PASS.
- 42-day power-curve first-call failure → bounded retry → Best Wattage recovered: PASS.
- persistent current power-curve failure → explicit stored Best Wattage continuity fallback: PASS.
- one fresh VO₂ point + seven stored historical points → merged eight-point series, fresh current value retained: PASS.
- current 42-day payload reuse prevents duplicate today's VO₂ power-curve request: PASS.
- synthetic pre-block PYRAMIDAL → declared POLARIZED + 5 MIN POWER → current POLARIZED journey: PASS.
- plan starting today: previous block visible while current adherence remains LEARNING and only today's post-selection session is assessed: PASS.
- Jinja compile: HOME_PAGE, OWNER_PORTAL_PAGE, ADMIN_PAGE: PASS.
- full Preview render: PASS.
- CSS parse: 1559 rules, 0 errors: PASS.
- four rendered JavaScript blocks checked with Node: PASS.
- section order remains Training Direction → Best Wattage Output → Power Model: PASS.
- no database schema change; Product/Personal persistence boundaries unchanged.

No real-device/Chromium screenshot is claimed by these tests; production visual confirmation should still be done after Render deployment.

**Final app.py SHA-256:** `26d530d91331d116baad6e45115f6a87b919f28b214c7a1ef733f09974773843`

**Deploy bundle SHA-256:** `a4e427ea7e11fdc8b3f1a6c59a5ea5e9395b4d04b6125fc80cebd5567676ee62`

## Release rule after V4.8.2
V4.8.2 is a release candidate until validated on Render. Never overwrite V4.8.1. If production validation passes, V4.8.2 becomes the next stable Product base.




# V4.8.1 UPDATE — PREFLIGHT TRAINING DIRECTION + COMPACT UNAVAILABLE METRICS + VO₂ RESILIENCE

V4.8.1 is a **surgical corrective release built only from the complete V4.8 file**. V4.8 remains untouched. There are no new database migrations, dependencies or Render secrets. The Product/Personal Neon split from V4.7 and the Training Direction Engine from V4.8 are preserved.

## 1. Training Direction moved before Snapshot generation
The editable model/goal controls are no longer embedded inside an already-generated Snapshot. They now live inside **Snapshot Status** immediately before `Generate Snapshot`.

Live flow:
1. choose/confirm Training Model;
2. choose/confirm Primary Goal;
3. press `Generate Snapshot`;
4. THE LAB persists/version-resolves the strategy on Product Neon **before any external Intervals.icu or AI call**;
5. the same Snapshot is generated using that strategy.

Unchanged selections continue the active block. A changed model or goal creates a new versioned strategy block. The lower Training Direction report is read-only analysis/adherence. Preview shows a disabled preflight example; Stored Last Report remains read-only and displays the strategy captured when the report was generated. This behavior is identical for OWNER and ordinary athlete accounts.

## 2. Advanced Physiology missing-data UI simplified
The fragile `Data gaps` title + explanatory paragraph was removed from the visible accordion header. It is now only:

`🗃️ Unavailable metrics  <count>  +`

The underlying DATA NEEDED / UNAVAILABLE cards and scientific logic are unchanged and remain expandable. The same compact header is shared by Live Snapshot, Preview and Stored Last Report.

## 3. VO₂ trend resilience
V4.7 and V4.8 had identical core VO₂ retrieval/build functions; Training Direction did not intentionally remove VO₂. V4.8.1 hardens the graph against a fresh Intervals payload/checkpoint returning no usable point:
- Wellness VO₂ still prefers the top-level `vo2max` field; a narrowly keyed fallback also checks the already-requested `sportInfo` structure for a `vo2max`/`vo2Max` value.
- If every parallel historical 5-minute-power VO₂ checkpoint fails, THE LAB retries today's checkpoint once sequentially.
- If a fresh wearable or performance series is empty but the athlete's last stored report contains that same Intervals-derived series, the graph can retain the last known stored series and labels it as fallback instead of silently deleting it.
- Fresh data always outranks stored fallback.

## 4. Render/Gunicorn requirement discovered during V4.8 production validation
The V4.8 code itself successfully ran after correcting the Product Render Gunicorn worker timeout. Keep the Product Start Command at:

`python -m gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30`

Reason: external Anthropic calls use an application timeout up to 60 seconds, so Gunicorn must not kill the worker earlier. Do not revert to the default ~30-second Gunicorn worker timeout. No app secret or database setting is involved.

## 5. V4.8.1 regression checks
Completed after the final patch:
- `python -m py_compile`: PASS (repeated).
- Jinja parse: HOME_PAGE, ADMIN_PAGE, OWNER_PORTAL_PAGE, LOGIN_PAGE, ATHLETE_SETUP_PAGE: PASS.
- CSS parse: 1539 rules, zero parse errors: PASS.
- HOME_PAGE JavaScript: four script blocks checked with Node after neutralizing the CSRF Jinja value: PASS.
- Preflight ordering in `/analyze`: strategy save/resolve occurs before `fetch_intervals_data`: PASS.
- No visible old `/training-strategy` editor remains inside generated Snapshot: PASS.
- Compact `Unavailable metrics` header contains no long explanatory text: PASS.
- VO₂ harness: top-level wellness, nested `sportInfo`, current-performance retry, stored fallback and fresh-data priority: PASS.
- V4.7→V4.8 check confirms `fetch_intervals_data`, wearable VO₂, performance VO₂ and VO₂ trend functions were unchanged in V4.8.
- V4.8→V4.8.1 AST regression: core scientific functions, Training Direction scoring, strategy persistence/isolation, Product/Personal data-plane functions and schema initializer are unchanged.

## Release rule after V4.8.1
V4.8.1 becomes the next Product stable candidate only after Render validation. Never overwrite V4.8. Future Product changes must start from the latest validated complete Product release and preserve owner Personal Neon separation, athlete isolation, password recovery, AI gateway/metering and the pre-Snapshot strategy flow.

---

# V4.8 UPDATE — TRAINING DIRECTION ENGINE

V4.8 was built **only from the complete deployed/validated Product V4.7 file**. V4.7 remains untouched. The owner Personal Neon bridge, Product Neon isolation, per-athlete integrations, password reset, AI gateway/metering and mobile Data Gaps hardening are preserved.

## New athlete-declared strategy
The Live Snapshot now contains a **Training Direction** section before **Best Wattage Output** and **Power Model**, so wattage is interpreted after the athlete's season/strategy context. The same visual section exists in Preview and Stored Last Report; controls are active only in the Live Snapshot.

Distribution choices:
- AUTO
- POLARIZED
- PYRAMIDAL
- THRESHOLD

Primary goals:
- 20' POWER
- VO₂MAX
- 5 MIN POWER · PUNCHEUR
- 1 MIN POWER
- SPRINTER
- ENDURANCE BASE
- TIME TRIAL

## Persistence and OWNER separation
A new Product-Neon table `training_strategy_plans` stores only strategy metadata (`user_id`, chosen distribution, primary goal, start/end/status timestamps). It is versioned: changing strategy closes the prior block and starts a new one.

**Important:** this table always uses Product DB access (`_db_execute`). It is deliberately NOT part of `_OWNER_PERSONAL_TABLES`. Therefore the OWNER's personal Daily Logs/Memory/Planning/Last Report remain on Personal Neon, while the OWNER's declared Product strategy metadata is stored on Product Neon under the owner's Product user ID. No Personal Neon migration is performed.

## Deterministic Training Direction Engine
Python now computes:
- observed training distribution from Intervals.icu `icu_zone_times`;
- an independent completed-session-family distribution using THE LAB's existing session classifier;
- observed model (`POLARIZED`, `PYRAMIDAL`, `THRESHOLD`, `MIXED`, or `LEARNING`);
- distribution match score;
- goal-stimulus match score;
- overall Plan Adherence index;
- mesocycle focus;
- next-microcycle direction.

Plan adherence is an internal coaching index, not a clinical/physiological measurement and not a claim that one exact percentage split is universally optimal. The three-zone field model uses Intervals power-zone time plus session families. Health/restrictions, race proximity, recovery and explicit Calendar commitments retain higher priority than strategy.

A newly selected plan is **not back-scored against old training**. Assessment begins from the declared plan date and uses a rolling maximum 28-day window. Until enough post-selection data exist, status is `LEARNING`; THE LAB explicitly warns not to manufacture intensity merely to improve the meter.

## AI integration
`TRAINING DIRECTION` is injected into the normal Snapshot AI context and Stored-Snapshot AI Coach Chat context. Python owns the declared strategy, observed model and adherence; AI explains those outputs and may shape recommendations/upcoming sessions around them, but may not invent a different goal or override higher-priority health/calendar rules. Saving Training Direction itself makes **no AI call**.

## UI / cross-view behavior
- Training Direction is positioned before Best Wattage Output and Power Model.
- Plan Adherence has a dedicated responsive progress bar with state styling.
- Strategy selector uses the existing Snapshot typography, cards, pills and emoji language.
- Preview shows a synthetic strategy with controls disabled.
- Last Report freezes the strategy/adherence captured at generation time and remains read-only.
- Older V4.7 stored reports remain renderable; they display a compatibility message asking for a new Snapshot to activate Training Direction.
- Mobile layout includes explicit 980/700/430/360 px hardening, min-width protection and wrapping.

## V4.8 tests completed before handoff
- `python -m py_compile`: PASS repeatedly.
- Python AST parse: PASS.
- Fake-runtime full module import with Flask/Werkzeug stubs: PASS.
- Fresh SQLite Product schema creates `training_strategy_plans`: PASS.
- V4.7 → V4.8 SQLite migration preserves existing athlete memory and adds strategy table: PASS.
- Per-user strategy isolation A/B: PASS.
- Strategy history versioning (old block completed, new block active): PASS.
- OWNER strategy routing uses Product DB and never `_data_execute`/Personal Neon: PASS.
- Pyramidal detection/adherence synthetic test: PASS.
- Declared Polarized vs observed Pyramidal mismatch detection: PASS.
- New-plan LEARNING/no-backscore behavior: PASS.
- Health/restriction priority over adherence chasing: PASS.
- Requested seven-goal set: PASS.
- Full HOME_PAGE Jinja compile: PASS.
- Full Preview / Live / Stored Report render: PASS.
- Section order Training Direction → Best Wattage Output → Power Model: PASS.
- CSS parse: 0 syntax errors, responsive V4.8 rules present: PASS.
- Rendered JavaScript syntax (`node --check`): PASS. A latent apostrophe escaping bug in the existing Science-search fallback string was discovered by this check and repaired surgically.
- 16 core scientific/runtime functions compared by AST against V4.7 and unchanged: PASS.

No new Render environment variables and no requirements changes are needed for V4.8. Product Neon creates the new strategy table automatically on first application initialization.

---

# V4.7 UPDATE — OWNER WORKSPACE HUB + PERSONAL NEON BRIDGE + MOBILE TEXT HARDENING

V4.7 was built **only from the complete Product V4.6 file**. The current personal THE LAB V49 was inspected only as a reference for the owner’s existing legacy Personal Neon schema and Data Gaps presentation; it was never used to replace Product code.

## Owner login split

After an ADMIN/OWNER login, `_post_login_destination()` now routes to `/owner`, a Snapshot-styled owner workspace hub with two explicit choices:

- **My Health Snapshot** — owner’s normal scientific workspace.
- **Control Center** — Product administration (users, invitations, licenses, password reset, AI access, usage metering, sessions, audit).

Beta athletes do not see this hub and keep their normal athlete flow.

## Personal Neon bridge

Product `DATABASE_URL` **must remain pointed to Product Neon**. V4.7 adds one separate owner-only environment variable:

- `THE_LAB_OWNER_DATABASE_URL` — the exact existing Personal THE LAB Neon connection string (normally copied from the Personal Render service’s `DATABASE_URL`).

The owner bridge directly reads/writes the existing legacy Personal Neon tables (`daily_logs`, `memory_items`, `planning_items`, `latest_report`) without copying data and without adding `user_id` or Product security tables. The bridge performs **no CREATE/ALTER/migration** on Personal Neon. It refuses to become ready if `THE_LAB_OWNER_DATABASE_URL` equals Product `DATABASE_URL`.

This preserves compatibility with the standalone Personal THE LAB service and means the owner does not start with an empty Product-memory account.

Owner Personal Neon operations covered by the bridge:

- Daily Log read/write and 42-day retention;
- Durable Memory CRUD;
- Planning CRUD;
- Latest Full Report read/write;
- JSON/CSV exports and manual cleanup;
- Snapshot storage metrics.

The Control Center always remains on Product Neon. Admin pages/hub do not trigger personal Daily Log housekeeping.

## Owner API / Intervals preservation

V4.7 deliberately leaves `_resolve_intervals_runtime()` and `_resolve_ai_runtime()` byte-identical to V4.6. For the owner ADMIN compatibility path this preserves the existing behavior:

- saved owner Intervals integration if one exists, otherwise `ICU_API_KEY` + `ICU_ATHLETE_ID`;
- saved owner AI integration if one exists, otherwise `ANTHROPIC_API_KEY` with `claude-sonnet-4-6`, matching the current Personal V49 code.

Therefore, to use the same current owner credentials from the unified Product Render service, copy the same owner secrets already used by Personal Render into Product Render if they are not already present:

- `ICU_API_KEY`;
- `ICU_ATHLETE_ID`;
- `ANTHROPIC_API_KEY`;
- optional `ATHLETE_CONTEXT` only if Personal Render overrides the code default.

Do **not** send these secrets to a beta athlete. Do not confuse them with `THE_LAB_PLATFORM_AI_*`, which remains the separate managed-AI facility for selected beta users.

## Data Gaps / overlap fix

The broken native `details/summary` Data Gaps header was replaced in the shared `HOME_PAGE` with THE LAB’s custom `lab-accordion`. The same shared template renders:

- live Snapshot;
- public Preview;
- stored Last Full Report.

Therefore the fix is common to all three views. The new layout uses `minmax(0,1fr)`, `min-width:0`, explicit block title/subtitle/count, `overflow-wrap:anywhere`, and mobile breakpoints at 700 / 430 / 360 px. Additional defensive wrapping was added to dense Snapshot text containers without changing scientific copy, typography hierarchy or metric logic.

## V4.7 regression tests completed

The final V4.7 file was tested twice with the release suite after the last code change:

- `python -m py_compile`: PASS twice;
- exact AST source comparison for 12 critical scientific/runtime functions vs V4.6: unchanged/PASS;
- surgical function diff: only expected storage/routing functions changed; no functions removed;
- legacy Product-user SQL → Personal V49 schema translator: PASS;
- actual in-memory legacy Personal V49 schema CRUD including **Last Full Report** select: PASS;
- 19 Product athlete CRUD functions equivalent to V4.6 after removing the data-plane wrapper: PASS;
- Jinja parse for HOME_PAGE, OWNER_PORTAL_PAGE, ADMIN_PAGE, Athlete Settings and forced-password page: PASS;
- Data Gaps uses no native `<details>/<summary>` and live/Preview/Last Report all use the same HOME_PAGE: PASS;
- CSS parsed with tinycss2: 1448 rules, zero parser errors; mobile hardening selectors present: PASS;
- owner hub ready/not-ready HTML structure: PASS;
- Personal Neon probe read-only and Product/Personal DB separation guard: PASS;
- owner Intervals/AI runtime source unchanged: PASS;
- admin housekeeping separation: PASS;
- owner portal renders no API key or database DSN: PASS.

No new Python dependency is required. Product database schema is unchanged. Personal Neon schema is unchanged.

## V4.7 deployment sequence

1. Replace Product GitHub `app.py` with V4.7 and deploy Product Render.
2. Keep Product `DATABASE_URL` unchanged.
3. Add `THE_LAB_OWNER_DATABASE_URL` to Product Render using the existing Personal Neon connection string.
4. Confirm Product Render has the owner’s existing `ICU_API_KEY`, `ICU_ATHLETE_ID` and `ANTHROPIC_API_KEY` if the owner wants the same current personal integrations from the unified service.
5. Log in as owner: the new workspace hub should appear. Open **My Health Snapshot** and verify existing Memory / Planning / Last Full Report are present before generating a new Snapshot.
6. Open **Control Center** and verify Product users/licenses remain unchanged.
7. On mobile, verify Data Gaps in live Snapshot, Preview and Last Full Report.

Do not delete or repoint the standalone Personal Render/Neon setup during this validation. V4.7 is intentionally reversible: if anything is wrong, Product V4.6 and the existing Personal service remain intact.

---

---

# 0. HOW TO USE THIS FILE IN A NEW CHAT

When a new ChatGPT conversation is needed, upload this handover first.

If code work is requested, also upload/provide:

1. the **latest stable Product `app.py`** currently deployed or last accepted;
2. when syncing changes from the personal project, the **latest stable personal `app.py`** containing those changes;
3. if available, the immediately previous personal stable version, because it makes a clean diff safer.

Then say something like:

> Continue THE LAB Product from the attached MASTER HANDOVER. The latest stable Product file is attached. The latest personal THE LAB file is also attached and contains the changes I want ported. Preserve all Product security/multi-user logic.

The assistant must treat this document as the project state and must NOT reconstruct the project from memory or from an older THE LAB version.

---

# 1. ABSOLUTE RELEASE RULES

These rules are mandatory.

1. **Never overwrite a stable file.** Every release is a new complete Python file with a new name/version.
2. **Always start from the latest stable Product file**, never from an older V1/V2/V3/V3.1 or from the personal branch.
3. The personal THE LAB and THE LAB Product are **two separate branches**.
4. A new personal `app.py` is a **reference/source of deltas**, not a replacement for Product.
5. Port only the requested personal changes into Product while preserving Product-only systems:
   - authentication;
   - users;
   - licenses/access codes;
   - revocable sessions;
   - audit log;
   - admin Control Center;
   - CSRF/security headers;
   - per-user data isolation;
   - encrypted credentials;
   - athlete setup;
   - AI gateway with beta BYOK and future owner-managed PLATFORM mode;
   - persistent per-athlete AI usage metering and daily quota;
   - per-athlete engine binding;
   - workspace authorization gates.
6. Do not re-introduce owner/personal baselines, fueling, timezone, Intervals credentials or AI credentials as defaults for athletes.
7. Before delivering any new release, run at least 2–3 meaningful tests; for Product releases use the larger regression suite described below.
8. Never expose source code, secrets, raw credentials or server internals to beta users.

---

# 2. PRODUCT PHILOSOPHY

THE LAB Product is not “the owner’s THE LAB with more logins”. It must be a multi-athlete system in which the deterministic Python engine remains the source of truth, while each athlete supplies their own identity, data sources, baselines/preferences and AI provider.

Core principles:

- Python/deterministic physiology constrains the AI, not the opposite.
- Athlete-specific data outranks generic assumptions.
- Missing data is not normal data.
- New metrics follow: `DATA NEEDED / UNAVAILABLE -> LEARNING -> TRACKING`.
- Explicit manual references can prevail until dynamic baselines are mature.
- Health/restrictions and deterministic guardrails outrank AI suggestions.
- One athlete must never receive another athlete’s Memory, Planning, logs, reports, credentials, baselines, fueling settings or AI context.

---

# 3. CURRENT INFRASTRUCTURE

The Product infrastructure is intentionally isolated from the owner’s personal THE LAB.

```text
PERSONAL THE LAB                  THE LAB PRODUCT
----------------                  ---------------
Personal GitHub/release           GitHub: THE_LAB_project (private)
Personal Render                   Separate Product Render service
Personal Neon                     Separate Product Neon project
Personal credentials              Per-athlete Product credentials
```

Do NOT point Product `DATABASE_URL` at the personal Neon database.

## Product Render environment variables

Currently relevant server-side environment variables include:

- `DATABASE_URL` — Product Neon pooled PostgreSQL connection string.
- `SECRET_KEY` — Flask/session security; strong, random, 32+ chars.
- `CREDENTIAL_ENCRYPTION_KEY` — dedicated strong encryption material, 32+ chars; used to protect provider credentials.
- `APP_USERNAME` — bootstrap/admin owner username.
- `APP_PASSWORD` — bootstrap admin password; after bootstrap authentication is database-backed with a password hash.
- `PRODUCT_SECURITY_STRICT=1`
- `SESSION_COOKIE_SECURE=1`
- `THE_LAB_DB_LIMIT_BYTES=500000000`

Legacy owner-only variables can exist for backward compatibility, but **athlete accounts must never inherit them**:

- `ICU_ATHLETE_ID`
- `ICU_API_KEY`
- `ANTHROPIC_API_KEY`
- legacy `ATHLETE_CONTEXT`

Do not add athlete OpenAI/Anthropic/Intervals keys to Render. Athletes configure their own credentials in Athlete Settings.

---

# 4. CURRENT PRODUCT BASELINE — V4.3

Current version string:

`THE LAB · PRODUCT V4.3 · LICENSE MANAGEMENT + EU DATE UX · ADMIN UI FIX · ENGINE BINDING + ATHLETE WORKSPACE UNLOCK · PER-ATHLETE INTERVALS + BASELINES + FUELING + MULTI-AI BYOK · NEON · PWA`

The athlete workspace is currently enabled **only for accounts whose isolated setup is complete**.

## Completed product steps

### V4.3 — License management + European date UX — COMPLETE IN CODE

The owner Control Center can now manage the expiry of an athlete's existing license without issuing a new invitation or forcing the athlete to create a new account.

Available actions:

- set an exact expiry using **DD/MM/YYYY**;
- extend by `+30 days`;
- extend by `+90 days`;
- switch to `No expiry`.

Important semantics:

- invitation/license expiry is stored internally using the existing exclusive-next-midnight UTC representation; UI dates are shown as inclusive calendar dates in DD/MM/YYYY;
- an expired but otherwise active license becomes valid again when extended into the future;
- changing expiry does **not** override an explicit `REVOKED` user/license state; the owner must separately use `Reactivate`;
- every expiry change writes `LICENSE_EXPIRY_UPDATED` to the audit log with old/new expiry;
- the native browser `type=date` input was removed from the owner invitation/license UI because it displayed MM/DD/YYYY on some devices; owner-facing date entry is now explicit `GG/MM/AAAA`;
- owner Control Center timestamps are formatted as DD/MM/YYYY HH:MM and invitation expiry is displayed DD/MM/YYYY.

No scientific-engine, per-athlete integration, credential, baseline, fueling, or data-isolation logic was intentionally changed in V4.3.


### Step 1 — Identity & Entitlement Security Foundation — COMPLETE

Implemented and live-tested:

- `users`;
- licenses/entitlements;
- one-time access codes/invitations;
- password hashing;
- server-backed/revocable auth sessions;
- account status: active/suspended/revoked;
- admin role;
- Control Center `/admin`;
- logout all sessions;
- suspend/revoke/reactivate;
- audit log;
- login lockout/rate resistance;
- CSRF protection;
- secure cookie/security headers;
- admin bootstrap from environment variables.

Production/manual test already passed:

- admin login;
- invitation generation;
- athlete activation;
- single-use invitation;
- athlete login;
- session revocation;
- account revoke prevents further access;
- audit trail updates correctly.

### Step 2 — Athlete Data Isolation — COMPLETE

The persistent scientific tables are user-scoped:

- `daily_logs.user_id`
- `memory_items.user_id`
- `planning_items.user_id`
- `latest_report.user_id`

All relevant reads/writes/updates/deletes/exports must remain owner-scoped.

`latest_report` is one latest report per athlete, not one global singleton.

Daily Log 42-day retention is per owner/user context and must never delete another athlete’s data accidentally.

Migration policy: legacy unowned Product records may only be assigned to the ADMIN/OWNER, never to a beta athlete.

Cross-user isolation tests have already passed using two synthetic users.

### Step 3 — Athlete Profile + Integrations + Multi-AI BYOK — COMPLETE

Each athlete has isolated Athlete Settings including:

- display name;
- timezone;
- primary sport;
- usual environment (indoor/outdoor/mixed);
- athlete context;
- baseline mode: Auto Learn or Manual + Auto Learn;
- optional manual physiological references;
- fueling settings;
- Intervals.icu Athlete ID;
- Intervals.icu API key;
- chosen AI provider;
- AI model;
- AI API key.

Intervals integration is stored under the athlete’s user ID. Conceptually:

```text
user_id
provider = INTERVALS
external_athlete_id = ICU_ATHLETE_ID for that athlete
credential_ciphertext = encrypted Intervals API key
status / last_checked / data summary
```

AI BYOK currently supports approved adapters for:

- Anthropic / Claude;
- OpenAI / GPT.

Do not implement arbitrary user-supplied API URLs without a dedicated security review. New AI providers should be explicit server-side adapters.

Important terminology: an athlete choosing OpenAI needs an **OpenAI Platform API key**. A ChatGPT Plus/Pro subscription alone is not an API credential.

Athlete AI credentials must be encrypted and must not fall back to the owner’s provider key.

### Step 4 — Per-Athlete Engine Binding & Workspace Unlock — COMPLETE IN CODE / AWAITING FIRST REAL BETA E2E

V4 binds the authenticated athlete into the scientific engine:

- Intervals Athlete ID per athlete;
- Intervals API key per athlete;
- timezone per athlete;
- athlete context per athlete;
- manual/dynamic baselines per athlete;
- fueling profile per athlete;
- AI provider/model/API key per athlete;
- per-user Memory/Planning/Daily Logs/Latest Report.

`PRODUCT_WORKSPACE_ENABLED_FOR_ATHLETES = True`, but authorization still requires a complete isolated setup.

Owner-only legacy globals may remain internally for the ADMIN compatibility path, but no athlete execution path may inherit owner values.

### V4.1 — Admin UX polish — COMPLETE IN CODE

V4.1 is a surgical Control Center release based on V4. It does **not** change athlete engine behavior. It adds:

- Snapshot-style cyan/ghost navigation buttons in the Control Center, optimized for mobile;
- corrected Product V4.1 copy (removes stale V3 / “waiting for Step 4” text);
- an `admin_hidden` presentation/archive flag for non-admin users;
- inactive (suspended/revoked) users can be hidden from the main roster without deleting accounts, licenses, athlete data or audit history;
- hidden users appear in a collapsed **Hidden users** section and can be restored;
- active users cannot be hidden;
- invitation history shows **REDEEMED BY** username in addition to redemption timestamp;
- Audit Log is collapsed by default behind a `+` control and its expanded body is scroll-bounded;
- hide/restore actions are themselves written to the audit trail.

The admin archive is deliberately not a hard-delete mechanism. Historical security/account records must remain available unless a future explicit account-deletion workflow is designed with data-retention/privacy rules.


### V4.2 — Control Center accordion/rendering fix — COMPLETE IN CODE

V4.2 is based **only** on the stable Product V4.1. It is a Control Center/UI release and must not change athlete engine behavior.

Changes:

- replaces the V4.1 native `<details>/<summary>` Admin accordions with a custom button + JavaScript accordion because the V4.1 Audit summary rendered compressed/unreadable in the owner browser;
- **Security audit** is closed by default, has a clear `+ / −` control, and keeps an internally scroll-bounded event table;
- `Hidden users` UI terminology becomes **Archived users**;
- inactive users expose **Archive** instead of `Hide`; active users still cannot be archived until suspended/revoked;
- archived users remain fully present in PostgreSQL and can be restored to the roster;
- `REDEEMED BY` username remains visible in Invitation history;
- top-right owner navigation is restyled after the Snapshot button language: cyan **THE LAB** return button plus separate logout action, with mobile-friendly layout;
- Admin copy/version label is updated to Product V4.2;
- the old `visibility=hide` POST value remains accepted for backward compatibility, while new UI posts `visibility=archive`;
- new archive events use `ADMIN_USER_ARCHIVED`; historical `ADMIN_USER_HIDDEN` audit rows, if any, remain valid history and must not be rewritten.

Regression rule: future releases must preserve this custom accordion approach unless deliberately redesigned and browser-tested. Do not silently revert to the V4.1 `<details>/<summary>` implementation.

---

# 5. ADMIN UX REQUIREMENT

The owner explicitly does **not** want to type `/admin` on mobile.

The Product dashboard must retain a clearly visible, differently colored **ADMIN** button for the owner/admin that links to the Control Center.

Athlete accounts should see a convenient **SETTINGS** path to their Athlete Settings, not the ADMIN Control Center.

Any future visual sync from the personal branch must preserve these Product navigation additions.

---

# 6. BETA TESTING STRATEGY

## Important rule: do not use the owner’s personal API credentials for `testathlete`

The owner does not want to copy their personal Intervals credentials into the Product test athlete. Respect this.

The owner may later use Product themselves, so their personal data/credentials must remain clean and separate.

## What can be tested internally without real APIs

Use synthetic/local tests rather than real owner keys.

Preferred internal test environment:

- temporary SQLite database;
- Flask test client where useful;
- two or more fake users;
- monkeypatched/mocked `requests.get` and `requests.post`;
- fake Intervals Athlete IDs and API keys supplied only to mocks;
- mocked Intervals activities/wellness/power-curve/activity-detail responses;
- mocked Anthropic response;
- mocked OpenAI response;
- no external API traffic;
- no personal secrets.

### Mandatory internal regression scenarios

1. **Authentication**
   - valid admin login;
   - invalid login;
   - athlete with active license;
   - revoked/suspended athlete denied;
   - session invalidation works.

2. **Authorization**
   - athlete cannot access `/admin`;
   - admin can access Control Center;
   - incomplete athlete is redirected to Athlete Settings;
   - complete athlete is allowed into workspace.

3. **Per-user storage isolation**
   - User A and User B create same-type records;
   - A cannot read/update/archive/delete/export B’s records;
   - B cannot read/update/archive/delete/export A’s records.

4. **Latest Report isolation**
   - A and B can each have a latest report;
   - A never receives B’s stored report.

5. **Intervals binding**
   - mock A uses Athlete ID `ICU-A`, key `KEY-A`;
   - mock B uses `ICU-B`, key `KEY-B`;
   - generated request URLs and Authorization headers always match current user;
   - switching A -> B -> A in the same Python process must not leak credentials/state.

6. **Timezone binding**
   - A e.g. `Europe/Rome`;
   - B e.g. `America/New_York`;
   - local dates/times/log context use the authenticated athlete’s timezone.

7. **Fueling binding**
   - give A and B visibly different numeric fueling profiles;
   - deterministic Nutrition Engine output must use the current athlete’s values only.

8. **Baseline binding**
   - manual reference belongs only to its athlete;
   - AUTO athlete with sufficient synthetic history generates a dynamic range from that athlete’s data;
   - no Product athlete inherits owner Garmin baseline values.

9. **AI BYOK routing**
   - A = OpenAI mock;
   - B = Anthropic mock;
   - correct endpoint/auth/model is selected per athlete;
   - athlete B cannot use A’s key;
   - neither athlete can use owner fallback key.

10. **Credential encryption**
    - plaintext Intervals key absent from database bytes/rows;
    - plaintext AI key absent from database bytes/rows;
    - displayed forms never reveal stored secret again.

11. **Retention**
    - cleaning old Daily Logs for A does not touch B;
    - Memory/Planning/Latest Report are not deleted by 42-day Daily Log retention.

12. **Migration/regression**
    - migrate from previous stable Product schema to new schema;
    - preserve users, licenses, audits, persistent records;
    - no destructive migration without explicit reason and backup strategy.

13. **Syntax/runtime**
    - `python -m py_compile` PASS;
    - Flask app imports successfully with Product dependencies;
    - important routes build/render under test client.

## What cannot be fully proven internally without a real second Intervals account

A mocked test can validate our code and routing, but it cannot prove that a second real Intervals account returns the expected live data and permissions.

The **first beta tester** will therefore provide the first true independent end-to-end integration test using their own:

- Intervals Athlete ID;
- Intervals API key;
- chosen AI provider/API key.

Do not ask the owner to provide their personal keys for this test.

---

# 7. FIRST REAL BETA TESTER — ACCEPTANCE CHECKLIST

Before invitation:

- current Product V4.2 (or later stable) deployed successfully;
- Render secrets healthy;
- Product Neon reachable;
- owner/admin login works;
- Control Center works;
- PWA public URL works over HTTPS;
- no personal owner data exists in beta athlete account.

Create beta invite from Control Center.

The beta tester should then perform:

1. activate one-time invite;
2. create account/password;
3. complete Athlete Profile;
4. confirm timezone;
5. choose baseline mode;
6. set optional manual baselines or leave unavailable fields empty;
7. set fueling preferences;
8. enter their own Intervals Athlete ID;
9. enter their own Intervals API key;
10. run Intervals connection test;
11. choose Anthropic or OpenAI;
12. enter their own AI API key and model;
13. run AI connection test;
14. confirm setup becomes complete;
15. enter workspace;
16. Generate Snapshot;
17. verify activities/wellness visibly belong to them;
18. inspect fueling and baseline states for plausibility;
19. create Daily Log;
20. create Memory item;
21. create Planning item;
22. generate/store Last Full Report;
23. ask AI Coach a question;
24. log out/login again;
25. install/open PWA from home screen if desired;
26. owner checks Control Center status/audit;
27. owner tests `Log out all`;
28. tester logs back in;
29. owner tests `Suspend` and/or `Revoke` at agreed time;
30. confirm revoked session immediately loses authorization.

Record any UI confusion, error text, slow calls, incorrect data attribution, missing metric, baseline anomaly or AI-provider error.

A beta issue involving cross-user data/credentials is **release-blocking severity**.

---

# 8. HOW TO SYNC FUTURE PERSONAL `app.py` CHANGES INTO PRODUCT

This is extremely important because the two projects will evolve in parallel.

## Correct merge direction

```text
LATEST STABLE PRODUCT  <-- base to modify
        +
NEW PERSONAL app.py    <-- reference/source of requested changes
        =
NEW PRODUCT RELEASE
```

Never do:

```text
NEW PERSONAL app.py
        + a few Product snippets
        = Product
```

That would risk deleting the multi-user/security architecture.

## Procedure when owner supplies a new personal app.py

1. Identify the current **latest stable Product file**.
2. Identify the new personal stable file.
3. Compare personal new version against the personal version from which the current Product visual/scientific code was derived, if available.
4. Extract the intended changes only.
5. Classify each change:
   - visual/CSS/template;
   - deterministic scientific logic;
   - new metric/data field;
   - Memory/Planning/log/report behavior;
   - AI prompt/context;
   - API/Intervals behavior;
   - persistence/schema;
   - PWA/service worker;
   - security/auth/navigation.
6. Port changes into Product one area at a time.
7. For every newly introduced owner-global or hardcoded athlete value, convert it to per-athlete runtime configuration before accepting it into Product.
8. For every new database query, enforce `user_id` scoping unless it is explicitly an admin/global security query.
9. For every new AI call, route through the per-athlete AI adapter; do not introduce a direct global Anthropic/OpenAI call for athlete paths.
10. For every new Intervals call, use current athlete Intervals credentials; do not introduce direct athlete-path reads from Render globals.
11. Preserve ADMIN button and Athlete SETTINGS UX.
12. Preserve privacy/security footer/legal surfaces unless the owner explicitly requests a change.
13. Run full regression tests.
14. Produce a new complete file; never overwrite previous Product stable.

## Visual changes

Visual/CSS/template changes can usually be ported nearly verbatim, but verify that they do not remove Product-specific elements:

- ADMIN button for admin;
- SETTINGS link/button for athletes;
- activation/setup screens;
- product access states;
- security/consent/privacy messaging;
- CSRF hidden fields on POST forms;
- role-aware navigation.

## Scientific changes

A scientific change from personal THE LAB may assume the owner’s data, baseline, timezone, fueling or training habits. Before porting it, inspect for:

- hard-coded ranges;
- owner-specific fallback values;
- global variables;
- `Europe/Rome` assumptions;
- owner `ATHLETE_CONTEXT`;
- fixed Intervals credentials;
- fixed Anthropic model/key/provider;
- unscoped memory/log/planning functions.

Convert these to current-athlete values or to LEARNING/DATA NEEDED behavior.

---

# 9. WHERE PRODUCT-SPECIFIC LOGIC LIVES / WHAT TO WATCH

Exact line numbers will change every release, so search by identifiers rather than relying on old line numbers.

Search for these areas before/after any merge:

## Security / access

- `PRODUCT_SECURITY_STRICT`
- `SESSION_COOKIE_SECURE`
- `PRODUCT_WORKSPACE_ENABLED_FOR_ATHLETES`
- `current_user`
- `require_admin`
- authentication/session functions
- `users`
- `licenses`
- `access_codes`
- `auth_sessions`
- `audit_log`
- `/admin`
- `/activate`
- `/login`

## Data ownership

- `_data_owner_user_id`
- `daily_logs`
- `memory_items`
- `planning_items`
- `latest_report`
- every `SELECT`, `INSERT`, `UPDATE`, `DELETE` involving athlete data

## Athlete configuration

- `athlete_profiles`
- `athlete_integrations`
- Athlete Settings route/template
- baseline mode/manual references
- fueling profile
- timezone
- athlete context

## Credentials

- `CREDENTIAL_ENCRYPTION_KEY`
- Fernet/encryption helper
- Intervals integration helpers
- AI integration helpers
- API-key test routines

## Intervals runtime binding

Search for all occurrences of:

- `ICU_ATHLETE_ID`
- `ICU_API_KEY`
- `intervals.icu/api`
- `get_intervals_headers`
- power-curve requests
- activities/wellness requests
- activity-detail requests

For athlete paths, these must resolve from current user configuration. Legacy globals may only serve OWNER/admin compatibility where explicitly intended.

## AI runtime binding

Search for:

- `ANTHROPIC_API_KEY`
- `api.anthropic.com`
- OpenAI endpoint calls
- AI provider dispatcher/router
- AI model selection
- Coach/Snapshot AI calls

Every athlete call must use their stored provider/model/key.

## Baseline/fueling/timezone binding

Search for:

- `GARMIN_BASELINES`
- `ATHLETE_FUELING_PROFILE`
- `ATHLETE_CONTEXT`
- `ROME_TZ`
- `get_rome_now`

The internal legacy function name `get_rome_now` may remain for compatibility, but athlete behavior must resolve the authenticated athlete’s configured timezone.

---

# 10. SECURITY NON-NEGOTIABLES

- GitHub repo private.
- No source distribution to beta athletes.
- No `.env` or secrets committed.
- Passwords hashed, never raw.
- Intervals and AI credentials encrypted at rest.
- Never log API keys.
- Never return API keys to UI after storage.
- HTTPS only in production.
- Secure/HttpOnly/SameSite cookies.
- CSRF on state-changing actions.
- Server-side authorization on every sensitive route; UI hiding is never considered security.
- Revocation must invalidate active sessions.
- Admin authorization is role-based; `/admin` URL secrecy is irrelevant.
- One athlete can never use another athlete’s entitlement or credentials.
- Avoid exposing stack traces/debug mode in production.
- Service worker must not cache private authenticated HTML/data in a way that leaks another user’s state.
- Export/delete functions must be per-user unless explicitly owner/admin-wide.

---

# 11. DATABASE / STORAGE

Product uses its own Neon project.

Current storage policy inherited from THE LAB includes:

- approximately 500 MB configured DB limit;
- monitoring via PostgreSQL database size;
- 42-day automatic retention for raw Daily Logs;
- Durable Memory, Planning and Last Full Report are not deleted by Daily Log retention;
- export tools should remain user-scoped.

Security/audit/session tables also consume storage, though much less than scientific payloads. Future work may add bounded retention for expired sessions and appropriate audit retention, but never silently delete security history without an explicit policy.

Do not claim exact per-user MB from a shared PostgreSQL database unless a proper estimation method is implemented.

---

# 12. PWA

Stay with PWA for now.

The user explicitly does not want APK/native app work at this stage.

Product goal:

- HTTPS web app;
- installable to home screen;
- manifest/icons/service worker;
- server-side Python engine;
- secrets never shipped to browser.

Do not duplicate physiology logic in JavaScript/native code.

---

# 13. LEGAL / PRIVACY WORK STILL TO DO BEFORE COMMERCIAL LAUNCH

Current Product has preliminary privacy/copyright messaging, but before commercial release it still needs a proper legal layer, including as appropriate:

- Privacy Policy;
- Terms of Service;
- health/training disclaimer;
- AI processing disclosure;
- Intervals integration disclosure;
- retention policy;
- access/export/deletion rights;
- consent handling where legally required;
- vendor/processor disclosures and DPAs where appropriate;
- cookie policy if applicable;
- software access/license wording: user receives a right of access/use, not ownership of THE LAB source/software.

Final legal text should be reviewed professionally before commercial launch.

---

# 14. NEXT PRACTICAL PHASE

Current position after V4.4 implementation:

1. Finish internal mock/regression testing without owner personal API keys.
2. Give a one-time BETA invite to the already-selected first beta tester.
3. The beta tester supplies their own Intervals credentials and their own AI API key.
4. Perform the First Real Beta Acceptance Checklist.
5. Fix beta issues with new numbered Product releases.
6. Keep personal and Product branches synchronized using the merge procedure in this handover.
7. After beta stability, improve onboarding/UX, diagnostics, legal/privacy and optional provider additions.

Potential useful future feature: an **ADMIN-only Synthetic Diagnostics** page that runs a no-external-network self-test using mocked/synthetic athlete data. This could make regression checks easier after visual releases, but it must not become a public route and must never contain real secrets.

---

# 15. WHAT THE ASSISTANT NEEDS FROM THE OWNER IN FUTURE CHATS

For a normal Product bug/change:

- this MASTER HANDOVER;
- latest stable Product `app.py`;
- exact symptom/request;
- Render error/log excerpt when relevant (never secrets).

For syncing a new personal THE LAB release into Product:

- this MASTER HANDOVER;
- latest stable Product `app.py`;
- newest stable personal `app.py`;
- ideally previous personal stable `app.py` for a clean diff;
- a short description of which changes are intended to be ported if the personal release contains multiple unrelated changes.

For beta bugs:

- which user role (admin or athlete);
- exact screen/action;
- exact error shown;
- relevant Render log excerpt with secrets redacted;
- whether Intervals connection test passed;
- whether AI connection test passed;
- browser/device/PWA vs regular browser if UI-specific;
- screenshots if visual.

Never ask the owner to paste:

- Neon `DATABASE_URL`;
- Intervals API key;
- Anthropic/OpenAI API key;
- `SECRET_KEY`;
- `CREDENTIAL_ENCRYPTION_KEY`;
- passwords.

---

# 16. DEFINITION OF “SAFE TO SHIP A NEW PRODUCT RELEASE”

A Product release is accepted only when:

- it is a new complete file, not an overwrite;
- it compiles;
- existing Product migration succeeds;
- authentication/admin controls still work;
- athlete authorization still works;
- data remains user-isolated;
- Intervals remains per-athlete;
- AI routing respects the configured gateway mode; beta default is per-athlete BYOK and PLATFORM must use only the owner-managed server credential;
- Snapshot and AI Coach Chat both pass through persistent usage metering and the athlete daily quota;
- owner-only values do not leak into athlete execution;
- baseline/fueling/timezone binding remain per-athlete;
- persistent data from existing users is preserved;
- PWA/private-data caching behavior remains safe;
- requested visual/scientific change is present;
- regression tests pass.

If a change cannot satisfy these conditions, do not unlock or ship it to beta users.

---

# 17. CURRENT CHECKPOINT SUMMARY

**Stable architecture reached:**

```text
Invite / Account
      ↓
Authentication + Entitlement
      ↓
user_id
      ↓
Athlete Settings
 ├─ Profile / timezone / context
 ├─ Manual + dynamic baselines
 ├─ Fueling
 ├─ Intervals Athlete ID + encrypted API key
 └─ AI gateway
      ├─ BYOK (beta default: encrypted per-athlete key)
      └─ PLATFORM (future: one owner-managed server key)
      ↓
AI usage meter + daily quota
      ↓
Per-athlete Engine Binding
      ↓
THE LAB deterministic engine
      ↓
Per-user Snapshot / Memory / Planning / Daily Logs / Report
      ↓
AI Coach using that athlete's chosen provider
```

The remaining major unknown is no longer architecture. It is **real-world beta behavior with the first independent Intervals account and AI provider account**.

That beta must be used to validate UX, onboarding clarity, live provider behavior and scientific output plausibility — while any cross-user privacy/security issue remains an immediate blocker.


# 18. V4.4 — AI GATEWAY, USAGE METERING AND BETA QUOTA

V4.4 prepares THE LAB for a future commercial AI-included model without changing the beta behavior today.

## Current beta mode

`THE_LAB_AI_ACCESS_MODE` defaults to `BYOK`. Athletes still connect their own OpenAI or Anthropic credential exactly as in V4.3. Athlete BYOK never falls back to the owner's/platform key.

## Future owner-managed mode

The scientific engine now calls one centralized AI gateway. A future switch requires configuration rather than rewriting Snapshot or Coach Chat:

```text
THE_LAB_AI_ACCESS_MODE=PLATFORM
THE_LAB_PLATFORM_AI_PROVIDER=OPENAI   # or ANTHROPIC
THE_LAB_PLATFORM_AI_MODEL=<chosen model>
THE_LAB_PLATFORM_AI_API_KEY=<server-only secret>
```

In PLATFORM mode athletes do not need a personal AI key; Athlete Settings treats the owner-managed gateway as the AI setup component. The platform key remains server-side and is never returned to the browser.

## Daily beta quota

The default is controlled centrally by:

```python
AI_DAILY_CALL_LIMIT = max(1, int(os.environ.get("THE_LAB_AI_DAILY_CALL_LIMIT", "10")))
```

Default beta quota: **10 counted AI calls per athlete per local calendar day**. Snapshot and AI Coach Chat share the same quota. Admin/owner calls are metered but are not blocked by the athlete cap. AI credential connection tests are also metered, but do not consume the product quota. Failed/timeout outbound provider calls consume quota because a real provider request occurred.

The preferred future change is a Render environment variable such as `THE_LAB_AI_DAILY_CALL_LIMIT=3`; this changes the cap without editing/releasing Python. If no env override exists, changing the default `10` in the single configuration line has the same effect.

## Persistent AI usage monitor

New table: `ai_usage_events`, scoped by `user_id`. It stores only operational metadata:

- timestamp and athlete-local date;
- call type (`SNAPSHOT`, `COACH_CHAT`, `CONNECTION_TEST`);
- provider/model;
- credential source (`athlete_byok`, `platform_managed`, etc.);
- whether the event counts toward the quota;
- success/error status and HTTP status when available;
- provider-reported input/output/total token counts.

It deliberately does **not** store prompts, AI responses or API keys.

The ADMIN Control Center contains a collapsible **AI usage monitor** showing per-athlete quota use/remaining calls, actual API request count, token totals and recent calls. This is intended to collect real beta economics before deciding subscription pricing and a future included-AI allowance.

## V4.4 regression tests

- Python compile: PASS.
- Synthetic SQLite quota test: 5 Snapshot + 5 Coach Chat = 10; 11th call blocked before provider: PASS.
- Connection test visible in metering but quota-neutral: PASS.
- OpenAI-style token extraction and aggregation: PASS.
- Failed provider request recorded as error and still consumes one quota call: PASS.
- BYOK athlete cannot inherit configured PLATFORM key: PASS.
- Central BYOK -> PLATFORM runtime switch: PASS.
- ADMIN and Athlete Settings Jinja syntax: PASS.
- ADMIN inline JavaScript syntax: PASS.
- Deterministic engine sentinel AST comparison (metrics, baselines, nutrition, energy, training/physiology, Intervals, power/metabolic paths): PASS; unchanged.

Do not remove this metering layer when syncing future personal THE LAB visual/scientific changes into Product. Every outbound product AI call must remain routed through `_call_ai_provider(...)` with a meaningful `usage_kind`.


---

---

# PRODUCT V4.6 · ADMIN PASSWORD RESET + FORCED CHANGE

## Why V4.6 exists
V4.5 had secure hashed passwords and revocable server-side sessions but no owner workflow for an athlete who forgot their password. V4.6 adds an owner-only recovery path without email infrastructure and without exposing or recovering the old password.

## Owner password-reset workflow
In `ADMIN → Users → CONTROL`, every non-admin athlete in the visible roster has `Reset password`.

When pressed:
1. THE LAB generates a strong human-typeable temporary password (`TLAB-RESET-...`).
2. Only the password hash is stored in `users.password_hash`.
3. `users.must_change_password` becomes `1`.
4. Failed-login counters and lockout are cleared.
5. Every active session for that athlete is revoked immediately.
6. The temporary password is shown to the owner once in the Control Center so it can be sent securely to the athlete.
7. `ADMIN_PASSWORD_RESET` is written to the audit log, but the temporary password itself is never written to the audit log or database in plaintext.

## Athlete recovery workflow
The athlete logs in with their normal username and the temporary password.

Because `must_change_password=1`, `_post_login_destination(...)` sends them to `/change-password-required` before Athlete Settings or the scientific workspace. A dedicated `before_request` gate prevents bypassing that page by manually navigating to other private routes.

The athlete must enter and confirm a new password of at least 12 characters. Reusing the temporary password is rejected. After success:
- the new password hash replaces the temporary-password hash;
- `must_change_password` returns to `0`;
- the temporary password stops working;
- `PASSWORD_CHANGED_AFTER_RESET` is audited;
- the existing recovery session continues to the normal post-login destination (Athlete Settings if setup is incomplete, otherwise THE LAB).

## Important access semantics
Password recovery does not alter license state, account status, Intervals credentials, AI credentials, athlete profile, Memory, Planning, Daily Logs or Last Full Report.

If an athlete is expired, suspended or revoked, password reset does not silently restore entitlement. The owner still manages those states with the existing license/access controls.

Archived athletes should be restored to the visible roster before using the password-reset control.

## Database migration
V4.6 adds only:

`users.must_change_password INTEGER NOT NULL DEFAULT 0`

PostgreSQL uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`; SQLite fallback adds the column only when absent. Existing users receive `0`, so deployment does not force password changes on current athletes.

## V4.6 tests completed
- `python -m py_compile`: PASS.
- Jinja parsing of `ADMIN_PAGE` and `FORCE_PASSWORD_CHANGE_PAGE`: PASS.
- V4.5→V4.6 SQLite migration: existing user preserved and `must_change_password=0`: PASS.
- Actual V4.6 reset/change helper AST executed with controlled DB/session/audit stubs: PASS.
- Temporary password format and forced-change flag: PASS.
- All-session revocation invoked on admin reset: PASS.
- Temporary password absent from audit details: PASS.
- Reuse of temporary password as the new permanent password refused: PASS.
- Successful new password clears the forced-change flag: PASS.
- Static route/gate wiring for `/change-password-required` and owner-only reset endpoint: PASS.
- Scientific-engine AST sentinels compared with V4.5: unchanged: PASS.

## Release rule
V4.6 must remain a separate complete release and must never overwrite V4.5. Once V4.6 is confirmed stable on Render, future Product modifications must start from this complete V4.6 file and preserve the forced-password-change gate and password-reset audit/session invariants.


**END OF MASTER HANDOVER**

---

# PRODUCT V4.5 · PER-USER AI ACCESS OVERRIDE

## Why V4.5 exists
V4.4 introduced a central AI gateway, persistent AI-usage metering and a 10-call/day/athlete beta cap, but its BYOK/PLATFORM switch was global. V4.5 makes that decision athlete-specific so the owner can temporarily or permanently provide THE LAB-managed AI to one athlete without changing every other account and without ever sharing the platform API key with that athlete.

## Effective AI mode
The global Render variable `THE_LAB_AI_ACCESS_MODE` remains the default (`BYOK` during beta). Each athlete can now have an optional database override:

- `NULL` / Default → follow `THE_LAB_AI_ACCESS_MODE`
- `BYOK` → require that athlete's own encrypted AI provider credential
- `PLATFORM` → use THE LAB's server-side managed provider/model/key

The new `users.ai_access_mode_override` column stores only the mode. It never stores the managed API key.

## One-time server configuration for THE LAB Managed AI
Before any athlete can be switched to `PLATFORM`, configure these Render secrets once:

- `THE_LAB_PLATFORM_AI_PROVIDER`
- `THE_LAB_PLATFORM_AI_MODEL`
- `THE_LAB_PLATFORM_AI_API_KEY`

The key stays on Render. Once configured, per-athlete switching is done entirely from the Control Center; no further Render edit is needed when changing individual athletes.

## Admin workflow
In `ADMIN → Users → AI` each athlete now has an `AI access` control with:

- `Default · <global mode>`
- `Athlete BYOK`
- `THE LAB managed`

Saving the choice writes only the per-user override and creates `AI_ACCESS_MODE_UPDATED` in the audit log. If managed AI has not been configured on Render, assigning `THE LAB managed` is refused safely.

## Athlete behavior
For an athlete in `PLATFORM` mode:

- Athlete Settings no longer asks for a personal OpenAI/Anthropic key.
- Setup can become complete with Profile + Intervals + configured THE LAB managed AI.
- Snapshot and AI Coach Chat use the same managed credential through the existing central gateway.
- Usage still counts against that athlete's own 10-call/day beta quota.
- `ai_usage_events.credential_source` records `platform_managed`.

For an athlete in `BYOK` mode:

- Their own tested encrypted AI credential is still required.
- They can never inherit the managed API key accidentally.

Switching a managed athlete back to BYOK immediately restores the personal-AI requirement. If they have no saved BYOK credential, their setup becomes incomplete and the workspace gate sends them to Athlete Settings until they connect one.

## Security invariant
The managed API key is never rendered to the browser, never placed in an athlete profile, never stored in `users`, and never written to the audit or usage tables. Neon stores only the access-mode override and ordinary call metadata.

## V4.5 tests completed
- `python -m py_compile`: PASS.
- Per-user isolation: Athlete A PLATFORM + Athlete B BYOK simultaneously: PASS.
- Default BYOK athlete cannot inherit platform secret: PASS.
- Managed athlete setup completes without personal AI key when Profile + Intervals are complete: PASS.
- Switching PLATFORM → BYOK restores personal-AI requirement: PASS.
- `DEFAULT` follows global mode; explicit BYOK can resist a future global PLATFORM default: PASS.
- Managed key absent → admin PLATFORM assignment refused: PASS.
- Usage event preserves `credential_source=platform_managed`: PASS.
- Platform secret absent from users/audit data: PASS.
- V4.4 SQLite database migration preserves existing user and adds nullable `ai_access_mode_override`: PASS.
- Jinja templates parse: PASS.
- Control Center JavaScript syntax: PASS.
- AST surgical diff: no scientific engine functions changed; only setup/admin/runtime-resolution functions plus new access-mode helpers were modified: PASS.

## Release base rule
V4.5 becomes the latest Product stable candidate only after real Render deployment is confirmed. Never overwrite V4.4. Future Product changes must start from the latest confirmed stable Product release and preserve all earlier isolation/security behavior.

