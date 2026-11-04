#!/usr/bin/env python3
"""Private, read-only R136 POWER_5 CA replay on exact R139.

Run ONLY with a read-only DSN for NOVA SCIENCE TEST LAB:
NOVA_TEST_LAB_DATABASE_URL=... python qa/nova_test_lab/run_personal_r136_r139_replay.py

No credentials, raw athlete data, or replay outputs are stored in GitHub.
"""
import hashlib, json, os, sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = "b16d99be3181d6423457c0b0a1f681315f279b1b0b99eb62f8913c747dd67871"
FIXTURE_ID = "personal-r136-last-ca-lossless"
FIXTURE_MD5 = "6f98d1c7553270622810c23fd3d37bc9"
FINGERPRINT = "b113f0515f2897bbb7e1"
REJECTED = "P5X_2X420_R300"
CARD3 = "P5_5X3_EASYREC"

def emit(status, **fields):
    print(json.dumps(dict(gate="R136_OWNER_5MIN_ON_R140", status=status, **fields),
                     ensure_ascii=False, default=str))
    return 0 if status == "PASS_PRIVATE_QUALITY_PRODUCER" else (1 if status == "FAIL" else 2)

def main():
    dsn = os.environ.get("NOVA_TEST_LAB_DATABASE_URL", "")
    if not dsn:
        return emit("BLOCKED", reason="TEST_LAB_DSN_MISSING")
    if hashlib.sha256((ROOT / "the_lab_app.py").read_bytes()).hexdigest() != SOURCE_SHA:
        return emit("BLOCKED", reason="WRONG_R139_SOURCE")
    # Never inherit production credentials when importing the actual Flask app.
    for key in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
                "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
                "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
                "THE_LAB_PLATFORM_AI_API_KEY"):
        os.environ[key] = ""
    os.environ["PRODUCT_SECURITY_STRICT"] = "0"
    os.environ["SESSION_COOKIE_SECURE"] = "0"
    os.environ["THE_LAB_TEST_LAB_MODE"] = "1"
    sys.path.insert(0, str(ROOT))
    try:
        import psycopg2
        with psycopg2.connect(dsn, connect_timeout=10,
                              options="-c default_transaction_read_only=on") as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT current_user,current_database(),
                       has_table_privilege(current_user,'science_lab.fixtures','SELECT'),
                       has_table_privilege(current_user,'science_lab.fixtures','INSERT'),
                       has_table_privilege(current_user,'science_lab.fixtures','UPDATE'),
                       has_table_privilege(current_user,'science_lab.fixtures','DELETE')""")
                identity = cur.fetchone()
                if (not identity or identity[0] != 'nova_r139_qa_reader'
                    or identity[1] != 'nova_lab' or identity[2] is not True
                    or any(identity[i] is True for i in (3,4,5))):
                    return emit("BLOCKED",reason="TEST_LAB_ROLE_MUST_BE_SCOPED_READ_ONLY")
                cur.execute("""SELECT fixture_json::text,md5(fixture_json::text)
                       FROM science_lab.fixtures
                       WHERE fixture_id=%s AND source_kind='personal'
                         AND consent_scope='owner_authorized' AND is_active=TRUE""",
                            (FIXTURE_ID,))
                row = cur.fetchone()
        if row is None or row[1] != FIXTURE_MD5:
            return emit("BLOCKED", reason="SOURCE_FIXTURE_MD5_NOT_ATTESTED")
        fixture = json.loads(row[0])
        if (fixture.get("schema") != "V4.8.91-R115-NOVA-REPLAY-1"
            or fixture.get("input_fingerprint") != FINGERPRINT
            or fixture.get("core_inputs",{}).get("training_direction",{}).get("primary_goal") != "POWER_5"
            or REJECTED not in fixture.get("expected",{}).get("workout_ids",[])
            or not str(fixture.get("generated_at_local") or "").startswith("2026-11-03T19:46:40")):
            return emit("BLOCKED", reason="REAL_CA_IDENTITY_MISMATCH")
        import the_lab_app as nova
        snapshot_clock = datetime.fromisoformat(fixture["generated_at_local"])
        with patch.object(nova, "get_rome_now", return_value=snapshot_clock):
            result = nova._v115_replay_nova_core(fixture)
        prescription = result.get("nova_prescription") or {}
        hard = [s for s in (result.get("next_sessions") or [])
                if isinstance(s,dict) and (str(s.get("intensity") or "").upper().split(" ",1)[0] == "HARD"
                     or str(s.get("intensity_class") or "").lower() in ("tempo","threshold","vo2"))]
        ids = [s.get("nova_workout_id") for s in hard if s.get("nova_workout_id")]
        unexpected = REJECTED == prescription.get("workout_id") or REJECTED in ids
        planned = prescription.get("inc120_planned_quality") or {}
        # A science-withheld HARD must leave a concrete non-executable quality
        # plan; simply suppressing the wrong 2x7 is not sufficient.
        quality_plan_ok = bool(
            isinstance(planned, dict)
            and planned.get("schema") == "NOVA-R196.9.140-CARD3-QUALITY-PLACEMENT-1"
            and planned.get("status") == "DEFERRED_NOT_CLEARED"
            and planned.get("workout_id") in nova._R19696_LIBRARY_INDEX
            and planned.get("workout_id") != REJECTED
            and planned.get("structure")
            and planned.get("execution_authorized") is False
            and planned.get("personalized_watts") is None
            and planned.get("fueling") is None
            and planned.get("adds_calendar_event") is False)
        # Evaluate the real Flask UI projection of the PRIVATE R136 replay;
        # no network calls, writes, screenshots or athlete values leave the job.
        # The real HMAC owner/browser E2E remains a separate gate.
        with nova.app.test_request_context("/"):
            with patch.object(nova, "_nova_inc051_verified_owner_id", return_value=None):
                rendered = nova._v4891_prepare_snapshot_for_ui(result)
        card3 = rendered.get("nova_card3_workout_view") or {}
        quality_visible = bool(
            isinstance(card3, dict)
            and card3.get("planned_quality") is True
            and card3.get("workout_id") == planned.get("workout_id")
            and card3.get("structure")
            and card3.get("execution_authorized_by_preview") is False
            and card3.get("personalized_watts") is None
            and rendered.get("inc120_quality_placement") == "CARD3_PLANNED_UNCLEARED"
            and rendered.get("inc120_quality_duplicate_card") is None)
        output = dict(fingerprint=FINGERPRINT, source_version="R196.9.136",
                      tested_version="R196.9.140", original_card3=CARD3,
                      selected_id=prescription.get("workout_id"),
                      producer_status=prescription.get("status"), output_hard_ids=ids,
                      quality_plan_ok=quality_plan_ok,
                      private_ca_card3_projection_ok=quality_visible,
                      quality_plan_id=planned.get("workout_id"),
                      inc111_rejected_candidate_ids=[x.get("workout_id") for x in (prescription.get("inc111_rejected_candidates") or []) if isinstance(x,dict)],
                      issuer_hmac_authenticated=False, no_db_writes=True,
                      no_external_provider_calls=True)
        return emit("FAIL" if unexpected or not quality_plan_ok or not quality_visible else "PASS_PRIVATE_QUALITY_PRODUCER", **output)
    except Exception as e:
        # Do not print exception messages; database driver messages may include secrets.
        return emit("BLOCKED", reason="EXCEPTION_"+type(e).__name__)

if __name__ == "__main__":
    sys.exit(main())
