"""Run NOVA's REAL deterministic R115 pipeline on an already existing fixture.

Usage: python qa/nova_test_lab/replay_fixture.py /absolute/path/to/private-fixture.json
Keep fixture files OUTSIDE the public repository and GitHub Actions artifacts.
No report generation, Neon, Intervals or AI access is needed.
Only PASS/FAIL and invariant names are printed, never athlete fields.
"""
import json
import os
import sys
from pathlib import Path

for name in (
    "DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
    "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
    "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY", "THE_LAB_PLATFORM_AI_API_KEY",
):
    os.environ[name] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import the_lab_app as nova  # noqa: E402


def verify_fixture(path):
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(fixture, dict) or fixture.get("schema") != nova.R115_REPLAY_SCHEMA:
        raise ValueError("Unsupported R115 fixture schema")
    if not isinstance(fixture.get("core_inputs"), dict):
        raise ValueError("Missing deterministic core inputs")
    if not isinstance(fixture.get("expected"), dict) or not fixture["expected"]:
        raise ValueError("No expected producer assertions in fixture")
    fingerprint = nova._v115_replay_fingerprint(fixture["core_inputs"])
    if fixture.get("input_fingerprint") != fingerprint:
        raise ValueError("Fixture fingerprint mismatch")

    output = nova._v115_replay_nova_core(fixture)
    actual = nova._v115_replay_expected(output)
    unexpected = sorted(
        name for name, value in fixture["expected"].items()
        if actual.get(name) != value
    )
    mutations = nova._v115_replay_mutation_suite(fixture)
    pass_mutations = isinstance(mutations, dict) and mutations.get("pass") is True
    verdict = not unexpected and pass_mutations
    summary = {
        "kind": "ACTUAL_R115_CORE_REPLAY",
        "status": "PASS" if verdict else "FAIL",
        "source": "EXISTING_PRIVATE_FIXTURE",
        "no_fresh_snapshot": True,
        "no_neon": True,
        "expected_invariants": len(fixture["expected"]),
        "failed_invariant_names": unexpected,
        "mutation_suite_pass": pass_mutations,
        "note": "Does not certify a live authenticated Snapshot or production E2E.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if verdict else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python qa/nova_test_lab/replay_fixture.py PRIVATE_R115_FIXTURE.json")
    try:
        raise SystemExit(verify_fixture(sys.argv[1]))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"kind": "ACTUAL_R115_CORE_REPLAY", "status": "BLOCKED",
                          "error_type": type(exc).__name__,
                          "note": "Fixture not disclosed; check the private input locally."}))
        raise SystemExit(2)
