# Card 3: source-of-truth, integrity, and release contract

**Public, sanitized contract** for R196.9.106 / INC-051. The detailed confidential project DTM remains in `NOVA_DOCUMENTO_TECNICO_MECCANICO_v1.0.42_DRAFT.md` (private delivery).

- Exactly ONE scientific producer/compiled workout provides Card 3 title, interval structure, personal watt target, phases, purpose and fueling duration. Do not choose workout templates in UI or mix a historical session median with a compiled quality.
- `current_verified` requires science + integrity PASS. `future_conditional` requires producer-side context digest, save-time matching digest, HMAC, owner scope from a validated authenticated user, unchanged compiled workout digest, and explicit **NOT CLEARED** flags.
- If any validation fails, show only an explanatory goal/state: no workout ID, no interval prescription, no work watts, no workout-specific fueling. Never treat a single-effort PB/FTP estimate as a validated repeatable dose.
- No scheduling, issuance, calendar insertion or clearance happens from a conditional future preview. Real availability stays untouched.
- The HTML contains only one execution panel (`r1969104-single-workout`) and no legacy “YOUR WORKOUT EXPLAINED” fallback.
- Automated public source-guard runs on every PR touching Card 3. Full private beta replay and real Flask/DB/Android staging verification remain mandatory for production GO. Configure `Card 3 source-of-truth contract / contract` as a **required** branch protection status check.
- Sensitive athlete exports, personalized data, private snapshots and project DTM containing them must never be uploaded to a public repository.
