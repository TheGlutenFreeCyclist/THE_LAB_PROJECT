# THE LAB R37 · METABOLIC TRAINING BLOCKS
## Regression + handover addendum · 18 Sep 2026

### Baseline
- Source baseline: `THE_LAB_PRODUCT_v4_8_74_WIP_R36_GLOBAL_DETERMINISTIC_TRAINING_CONTRACT.py`
- Candidate: `THE_LAB_PRODUCT_v4_8_74_WIP_R37_METABOLIC_TRAINING_BLOCKS.py`
- R36 deterministic training/validation contract remains the coaching baseline.

## Product decision
`Previous Training Blocks` remains an eight-session internal evidence window. The athlete UI renders only the latest three sessions.

The raw eight-session list is still consumed before presentation by Execution Model, completed-quality review, W′bal/repeatability evidence, feedback linking and stored-report tools. The UI reduction happens only at the presentation boundary and is duplicated by a defensive `[:3]` Jinja slice.

No new macrosection/card was added.

## Python-only metabolic model
R37 adds deterministic local calculations only. The provider does not calculate them and does not receive the detailed `metabolic_load` or per-session `metabolic_profile` structures.

### Per-session inputs
- duration;
- power-zone distribution when available;
- Intervals `icu_intensity` only as a fallback when zones are absent;
- training-family fallback only when both zones and IF are unavailable;
- mechanical work from Intervals `joules`, else average power × time;
- native Intervals W′bal depletion when already present in the existing analysed-interval request;
- HEAT only as a small recovery-context modifier, never as fabricated mechanical work or glycogen use.

Calories are not used by the new metabolic-demand index.

### Per-session outputs shown inside the existing block
- METABOLIC DEMAND · LOW / MODERATE / HIGH / VERY HIGH
- GLYCOGEN PRESSURE · LOW / MODERATE / HIGH / VERY HIGH
- HIGH-INTENSITY DEMAND · MINIMAL / MODERATE / HIGH / VERY HIGH
- RECOVERY PRESSURE · LOW / MODERATE / HIGH / VERY HIGH
- mechanical work in kJ when power evidence exists
- demand density (easy-hour-equivalent internal scale)
- existing interval detail, duration, load, average watts, HR, drift, power/HR zones and consideration remain unchanged
- existing repeatability and native W′bal evidence is additionally surfaced when available

The internal demand units are heuristic relative-model units, not kcal, calorimetry, glycogen grams or a laboratory metabolic-efficiency measurement.

## Longitudinal model
`build_training_metabolic_load()` uses up to 42 days of completed CYCLING activities and compares the rolling current 7 days with up to five prior rolling 7-day windows.

It keeps separate:
- total relative metabolic demand;
- demand density per riding hour;
- high-intensity minutes;
- mechanical work (kJ).

This allows volume and intensity to diverge instead of being collapsed into one calorie number.

### Context-only sport isolation
Non-cycling modalities never enter the cycling zone/density model. They may still raise systemic recovery/fueling context conservatively through their aggregate load/duration, preserving the R30 systemic-context contract without letting running/swimming/etc. contaminate cycling-specific metabolic trends.

## Reuse elsewhere in the current architecture
### Previous Training Blocks
Primary visual surface. Latest 3 displayed; 8 retained internally.

### Fuel & Recovery → Carbohydrate Demand
The existing `glycogen_pressure` driver no longer uses provider kcal thresholds. It now comes from the deterministic 48 h cycling metabolic-demand model, with a conservative systemic context-only load/duration bump when another modality is present.

Provider calories remain visible only as raw historical context where already present; they do not drive the new metabolic-pressure model.

### Post-Workout Recovery / Nutrition Plan
Existing carbohydrate logic already consumes `glycogen_pressure`. Therefore R37 improves this input without adding a new nutrition engine or new section. Session kind, duration, turnaround and race context remain separate existing determinants.

`RECOVERY NOW` additionally shows the just-completed session's deterministic metabolic-demand and glycogen-pressure labels. Macro targets are still produced by the existing nutrition rules.

### Physiological State → ENERGY
This existing system already consumes `glycogen_pressure`; it automatically benefits from the new calorie-independent pressure calculation.

### Energy Bank
Intentionally NOT modified. Energy Bank already spends reserve from training load, duration, intensity and learned day context. Adding R37 metabolic demand to the score would double-count overlapping training stress.

### AI / provider boundary
Detailed R37 structures are stripped before provider calls:
- `metabolic_context.metabolic_load` removed;
- `previous_training_blocks[*].metabolic_profile` removed.

Existing high-level nutrition context remains available as before, but the new calculations are owned entirely by Python.

## Regression matrix
### Static/runtime-safe checks
- `python -m py_compile`: PASS
- AST parse: PASS
- Jinja: 11 / 11 PASS
- Flask routes: 55 → 55
- `_call_ai_provider(` sites: 4 → 4
- `requests.get(` sites: 8 → 8
- `requests.post(` sites: 3 → 3
- removed functions: 0

Intentional changed existing functions only:
- `build_previous_training_blocks`
- `build_metabolic_context`
- `_v4891_prepare_snapshot_for_ui`
- `_v4890_provider_safe_snapshot_context`
- `_v4890_provider_safe_analysis_args`

New R37 engine functions:
- `_v4894_work_kj`
- `_v4894_session_metabolic_profile`
- `_v4894_pct_delta`
- `build_training_metabolic_load`

### Ecosystem metabolic matrix
2,224 invariant checks PASS across:
- durations: 20 / 40 / 60 / 90 / 150 / 240 min;
- easy → mixed → high-intensity zone distributions;
- Z2 / Tempo / Threshold / VO₂ / Sprint / HEAT labels;
- mechanical-work changes independent from metabolic-density changes;
- calories changed from 100 → 5,000 with identical session physiology: metabolic model unchanged;
- W′bal depletion modifies only high-intensity/recovery context, not work or base metabolic/glycogen units;
- IF fallback monotonicity;
- missing/malformed duration fails closed;
- 42-day learning vs established states;
- context-only Run contamination guard;
- eight-session internal / three-session presentation invariant.

Key synthetic regression examples:
- same 7-day mechanical work, more high intensity: metabolic demand +27.4%, intensity density +27.4%, mechanical work 0% change;
- double duration/work at same intensity: metabolic demand +100%, mechanical work +100%, intensity density 0% change;
- unchanged weekly structure: demand/density/work deltas all 0%.

## GitHub size gate
- R37: 2,062,896 bytes
- 2 MiB boundary: 2,097,152 bytes
- margin: 34,256 bytes
- SHA-256: `2b7fe0c876156a715729a142b40daad1c69abe611197f8b1fc9e486221374b04`

The file remains below the GitHub preview boundary with >34 KB headroom. Future releases must re-run this size gate before delivery.

## Limits
No live Flask/browser/provider smoke was run in this container. The deterministic calculations, Jinja parsing, static architecture and synthetic ecosystem matrix were tested offline. No extra Intervals request site and no extra AI call site were introduced.
