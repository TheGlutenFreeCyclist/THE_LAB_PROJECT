"""INC132 Fase 4: real R150 scientific numeric replay vs authenticated provenance.

This test intentionally HAS a positive synthetic *numeric* path, NOT a
positive authenticated quality. Do not replace the live owner/request gate with
a mock, a fabricated DEVICE_LAPS marker, or a test HMAC. No DB/calendar access.
"""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

for name in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
             "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
             "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
             "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[name] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["THE_LAB_TEST_LAB_MODE"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import the_lab_app as nova
from test_inc108_origins import original_repetition_fixture, replay, WID, DIM

EXPECTED_R150 = "6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73"
SYNTHETIC_OWNER = "inc132-phase4-not-a-real-owner"


def run():
    # Independently check the original source, NOT the .pyc or a claimed version.
    source_sha = hashlib.sha256(
        Path(nova.__file__).read_bytes()).hexdigest()
    if source_sha != EXPECTED_R150:
        raise AssertionError("R150_SOURCE_BASELINE_CHANGED")

    # Valid synthetic repeat data can validate the science formula numerically.
    # The event's DEVICE_LAPS string remains untrusted, not a device receipt.
    ledger, _ = original_repetition_fixture()
    good_band, good_proof = replay(ledger)
    if (good_band.get("state") != "PRESCRIBED"
        or good_proof.get("accepted") is not True):
        raise AssertionError("SYNTHETIC_NUMERIC_POSITIVE_REGRESSION")

    bad_band, bad_proof = replay({"repeatability": {"events": []}})
    if bad_proof.get("accepted") is True:
        raise AssertionError("EMPTY_EVIDENCE_GRANTED_NUMERIC_DOSE")

    # Exact root cause observed in two authorized private R135/R136 replays:
    # an exploratory FTP-derived candidate is NOT a verified repetition dose.
    # The synthetic control MUST reject it even if the numeric fields remain.
    exploratory = copy.deepcopy(good_band)
    exploratory["source"] = "INTERVALS_DATED_FTP_EXPLORATORY"
    exploratory["repeatability_state"] = "NOT_VERIFIED_FOR_THIS_WORKOUT"
    exploratory["activity_id"] = None
    exploratory["recovery_duration_comparable"] = False
    unproven = nova._nova_inc083_science_replay(
        {"nova_workout_id": WID, "nova_prescription_dimension": DIM,
         "power_prescription": exploratory},
        ledger, None, {"scientific_progression": {"dimension": DIM}})
    if (unproven.get("accepted") is True
        or unproven.get("reason") != "CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN"):
        raise AssertionError("EXPLORATORY_FTP_WATTS_WRONGLY_AUTHORIZED")

    # Replaying a modified power result must not silently accept a new W range.
    altered = copy.deepcopy(good_band)
    altered["high_watts"] += 15
    tampered = nova._nova_inc083_science_replay(
        {"nova_workout_id": WID, "nova_prescription_dimension": DIM,
         "power_prescription": altered},
        ledger, None, {"scientific_progression": {"dimension": DIM}})
    if tampered.get("accepted") is True:
        raise AssertionError("TAMPERED_BAND_ACCEPTED")

    # A synthetic event must not get live provenance outside an authenticated
    # Flask /analyze request; do not patch current_user or request.endpoint.
    truth = nova._nova_inc091_truth(ledger, good_band, SYNTHETIC_OWNER)
    if truth is not None:
        raise AssertionError("UNAUTHENTICATED_PROVENANCE_ACCEPTED")

    # Compile isolated mechanical/numeric content as an observation only.
    # Even a successful native compiler is NOT an attested or issued offer.
    template = nova._R19696_LIBRARY_INDEX[WID]
    unsigned_plan = {"goal_key": "POWER_5", "dimension": DIM, "workout_id": WID}
    native_state = "NOT_PROVEN"
    try:
        workout = nova._nova_inc091_compile_native(
            template, unsigned_plan, ledger, None,
            {"scientific_progression": {"dimension": DIM}},
            power_model={})
        if isinstance(workout, dict):
            if (workout.get("is_scheduled") is not False
                or workout.get("date") is not None):
                raise AssertionError("NATIVE_COMPILER_INVENTED_BOOKING")
            native_state = "NUMERIC_COMPILED_NOT_AUTHENTICATED"
        else:
            native_state = "NATIVE_COMPILER_WITHHELD"
    except (TypeError, ValueError, KeyError, IndexError, AttributeError,
            ArithmeticError, OverflowError) as exc:
        native_state = "NATIVE_COMPILER_BLOCKED_" + type(exc).__name__

    if native_state != "NUMERIC_COMPILED_NOT_AUTHENTICATED":
        raise AssertionError("ORIGINAL_NATIVE_COMPILER_NUMERIC_POSITIVE_NOT_PROVEN")

    # R150 INC121 duplicate placeholder is documented as a BH-001 conflict;
    # detecting it is a RED product observation, not a passing UI acceptance.
    legacy_placeholder = "nova-card3-grey-placeholder" in nova.HOME_PAGE
    result = {
        "suite": "INC132_PHASE4_SCIENCE_VS_AUTH_DIAGNOSTIC",
        "status": "DIAGNOSTIC_PASS",
        "baseline_sha256_verified": True,
        "synthetic_numeric_positive": True,
        "empty_evidence_numeric_denied": True,
        "tampered_watts_denied": True,
        "exploratory_ftp_numeric_source_denied": True,
        "unauthenticated_provenance_denied": True,
        "native_compiler_observation": native_state,
        "live_raw_fit_byte_receipt": "NOT_VERIFIED",
        "live_authenticated_quality_full": "NOT_VERIFIED",
        "day_of_clearance": "NOT_TESTED_HERE_EXISTING_GATE_PRESERVED",
        "card3_bh001": "RED" if legacy_placeholder else "NOT_VERIFIED",
        "card2_runtime": "NOT_IMPLEMENTED",
        "production": "NO_GO",
        "calendar_writes": 0,
        "database_writes": 0,
    }
    print(json.dumps(result, sort_keys=True))
    if not legacy_placeholder:
        raise AssertionError("EXPECTED_R150_LEGACY_UI_BASELINE_CHANGED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        print(json.dumps({
            "suite": "INC132_PHASE4_SCIENCE_VS_AUTH_DIAGNOSTIC",
            "status": "BLOCKED",
            "error_type": type(exc).__name__,
            "production": "NO_GO"}))
        raise SystemExit(2)
