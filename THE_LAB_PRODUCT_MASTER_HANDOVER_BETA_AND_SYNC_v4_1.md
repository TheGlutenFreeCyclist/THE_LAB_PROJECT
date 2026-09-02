# THE LAB PRODUCT — MASTER HANDOVER
## Beta testing, multi-athlete architecture, sync with personal THE LAB

**Handover date:** 2 September 2026  
**Current Product baseline:** `THE_LAB_PRODUCT_v4_1_ADMIN_UX.py` / deploy `app.py` V4.1  
**Repository:** private GitHub repository `THE_LAB_project`  
**Deployment:** separate Render Web Service  
**Database:** separate Neon PostgreSQL project (500 MB free tier currently used by this project)  
**Client:** installable PWA; no APK/native branch at this stage.

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
   - multi-AI BYOK;
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

# 4. CURRENT PRODUCT BASELINE — V4.1

Current version string:

`THE LAB · PRODUCT V4.1 · ADMIN UX POLISH · ENGINE BINDING + ATHLETE WORKSPACE UNLOCK · PER-ATHLETE INTERVALS + BASELINES + FUELING + MULTI-AI BYOK · NEON · PWA`

The athlete workspace is currently enabled **only for accounts whose isolated setup is complete**.

## Completed product steps

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

- current Product V4.1 (or later stable) deployed successfully;
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

Current position after V4.1 deployment:

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
- AI remains per-athlete BYOK;
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
 └─ AI provider/model + encrypted BYOK key
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

---

**END OF MASTER HANDOVER**
