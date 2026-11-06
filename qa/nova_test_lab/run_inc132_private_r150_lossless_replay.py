#!/usr/bin/env python3
"""INC132 R150 TEST: privacy-preserving replay of existing authorized LAB fixtures.

Reads only NOVA SCIENCE TEST LAB through nova_r139_qa_reader. Requires an
already-configured private Actions secret. No live providers, new Snapshot,
production app/database access, writes, private logs, raw artifacts, or HMAC
shortcut. Each lossless JSON is an R115 recorded input, NOT raw FIT bytes.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
R150_SHA256 = "6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73"
ALLOWED = {
    "personal-r135-lossless-2026-11-03": "bd1516c66d54f6d637863e7c07b542ba",
    "personal-r136-last-ca-lossless": "6f98d1c7553270622810c23fd3d37bc9",
}
READER = "nova_r139_qa_reader"
DATABASE = "nova_lab"
MAX_LOCAL_FIXTURE = 900000


def emit(status, **data):
    print(json.dumps({"suite":"INC132_R150_PRIVATE_REPLAY",
                      "status":status,"release":"NO_GO", **data}, sort_keys=True))
    return 0 if status=="TEST_EXECUTED" else (1 if status=="SCIENTIFIC_DRIFT" else 2)


def verify_fixture(fixture, nova):
    if (not isinstance(fixture, dict) or fixture.get("schema") != nova.R115_REPLAY_SCHEMA
        or not isinstance(fixture.get("core_inputs"), dict)
        or not isinstance(fixture.get("expected"), dict)
        or not fixture["expected"]):
        raise ValueError("FIXTURE_SCHEMA_OR_EXPECTED_INVALID")
    actual_fp = nova._v115_replay_fingerprint(fixture["core_inputs"])
    if fixture.get("input_fingerprint") != actual_fp:
        raise ValueError("FINGERPRINT_MISMATCH")
    clock = datetime.fromisoformat(fixture["generated_at_local"])
    # Suppress any unexpected private diagnostics written by old app internals.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        with patch.object(nova,"get_rome_now",return_value=clock):
            result = nova._v115_replay_nova_core(fixture)
            view = nova._v115_replay_expected(result)
            mutations = nova._v115_replay_mutation_suite(fixture)
    mismatched = sorted(k for k, value in fixture["expected"].items()
                        if view.get(k) != value)
    # Privacy-safe R135/R136 -> R150 diagnostic: categories only. Never log
    # watt values, workout/plan IDs, athlete identifiers or fixture payloads.
    old_hard = fixture["expected"].get("hard_session_count")
    new_hard = view.get("hard_session_count")
    old_hard_ok = type(old_hard) is int and old_hard >= 0
    new_hard_ok = type(new_hard) is int and new_hard >= 0
    replay = result.get("r115_replay") if isinstance(result, dict) else {}
    replay = replay if isinstance(replay, dict) else {}
    raw_r27 = str(replay.get("native_r27_gate_state") or "")
    r27_category = raw_r27 if raw_r27 in {
        "R27_COACH_TEST_SAFETY_BLOCKED",
        "R27_COACH_TEST_PENDING_CANONICAL_COMPILER",
        "R27_COMPILED_SLOT_MISSING",
        "R27_COMPILED_AVAILABILITY_MISMATCH",
        "R27_MULTIPLE_HARD_EXPOSURES",
        "R27_MAXIMAL_NOT_READY",
        "R27_CANONICAL_PLAN_COMPILED",
        "FINAL_COMPILATION_REJECTED",
    } else ("NOT_APPLICABLE" if not raw_r27 else "OTHER_R27_STATE")
    tests = mutations.get("tests") if isinstance(mutations, dict) else None
    tests = tests if isinstance(tests, list) else []
    base_tests = [x for x in tests if isinstance(x, dict) and x.get("name") == "BASELINE_IDENTITY"]
    other_failed = sum(1 for x in tests if isinstance(x, dict)
                       and x.get("name") != "BASELINE_IDENTITY" and x.get("pass") is not True)
    realistic = mutations.get("realistic_completion_suite") if isinstance(mutations, dict) else {}
    realistic = realistic if isinstance(realistic, dict) else {}
    realistic_state = str(realistic.get("state") or "")
    realistic_state_class = (realistic_state if realistic_state in {
        "SKIPPED_WRONG_GOAL", "SKIPPED_WRONG_PHASE"}
        else ("EVALUATED" if realistic.get("scenarios") else "NOT_APPLICABLE"))
    realistic_scenarios = realistic.get("scenarios") if isinstance(realistic.get("scenarios"), list) else []
    pres = result.get("nova_prescription") if isinstance(result, dict) else {}
    pres = pres if isinstance(pres, dict) else {}
    compiled_hard = pres.get("hard_prescription_available") is True
    requested_hard = pres.get("requested_hard_prescription_available") is True
    hard_loss_stage = ("NO_HARD_REQUESTED" if not requested_hard
        else "COMPILE_REJECTED_HARD" if not compiled_hard
        else "DOWNSTREAM_REMOVED_HARD" if new_hard_ok and new_hard == 0
        else "HARD_STILL_PRESENT")
    # Compare expected canonical keys only, never print private values/workout IDs.
    return {
        "r27_gate_state_class": r27_category,
        "r27_gate_applied": bool(replay.get("native_r27_gate_applied")),
        "legacy_hard_present": bool(old_hard > 0) if old_hard_ok else None,
        "r150_hard_present": bool(new_hard > 0) if new_hard_ok else None,
        "hard_count_changed": old_hard != new_hard,
        "hard_loss_stage": hard_loss_stage,
        "prescription_status_class": str(pres.get("status")) if pres.get("status") in {"PRESCRIBED","BLOCKED","EASY_ONLY","HOLD"} else "OTHER",
        "execution_status_class": str(pres.get("execution_status")) if pres.get("execution_status") in {"READY","EASY_ONLY","BLOCKED_BY_FINAL_SAFETY_GATE"} else "OTHER",
        "authority_final_pass": result.get("authority_final_pass") is True,
        "mutation_baseline_identity_pass": (base_tests[0].get("pass") is True) if base_tests else None,
        "mutation_other_failed_count": other_failed,
        "mutation_realistic_completion_applicable": realistic.get("applicable") is not False if realistic else None,
        "mutation_realistic_completion_state_class": realistic_state_class,
        "mutation_realistic_completion_pass": realistic.get("pass") if type(realistic.get("pass")) is bool else None,
        "mutation_realistic_failed_case_count": sum(1 for x in realistic_scenarios if isinstance(x, dict) and x.get("pass") is not True),
        "expected_invariant_count":len(fixture["expected"]),
        "expected_invariant_drift_count":len(mismatched),
        "expected_invariant_drift_names":mismatched,
        "mutation_pass":bool(isinstance(mutations,dict) and mutations.get("pass") is True),
        "core_result_present":isinstance(result,dict),
        "card3_future_complete_and_attested":"NOT_VERIFIED",
        "card2_integrative_complete_and_attested":"NOT_VERIFIED",
        "raw_fit_byte_provenance":"NOT_VERIFIED"
    }


def run():
    if hashlib.sha256((ROOT/"the_lab_app.py").read_bytes()).hexdigest() != R150_SHA256:
        return emit("BLOCKED",reason="R150_SOURCE_INTEGRITY_CHANGED")
    dsn = os.getenv("NOVA_TEST_LAB_DATABASE_URL") or ""
    if not dsn:
        return emit("BLOCKED",reason="TEST_LAB_READ_ONLY_DSN_NOT_CONFIGURED")

    # Force all live integrations off before importing NOVA.
    for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
                "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
                "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
                "THE_LAB_PLATFORM_AI_API_KEY"):
        os.environ[key]=""
    os.environ["THE_LAB_TEST_LAB_MODE"]="1"
    os.environ["PRODUCT_SECURITY_STRICT"]="0"
    os.environ["SESSION_COOKIE_SECURE"]="0"

    import psycopg2
    from psycopg2.extensions import parse_dsn
    # Only safe classifications may enter public logs. Never echo a DSN/host/password.
    parsed = parse_dsn(dsn)
    if parsed.get("user") != READER or parsed.get("dbname") != DATABASE:
        return emit("BLOCKED",reason="CI_SECRET_POINTS_TO_WRONG_READER_OR_DATABASE")
    sys.path.insert(0,str(ROOT))
    import the_lab_app as nova

    out={}
    try:
        # Neon proxy accepts a normal TLS startup, but rejects libpq startup
        # options. Establish TLS first, then mark every transaction READ ONLY.
        db_connection = psycopg2.connect(
            dsn, sslmode="require", connect_timeout=12,
            application_name="inc132-private-r150-test-only")
        db_connection.set_session(readonly=True, autocommit=False)
    except psycopg2.OperationalError as exc:
        s = str(exc).lower()  # deliberately NOT printed
        category = ("AUTH_REJECTED" if "password authentication failed" in s
          else "DNS_FAILED" if "translate host" in s or "name resolution" in s
          else "TIMEOUT_OR_NETWORK" if "timeout" in s or "timed out" in s or "network is unreachable" in s
          else "CONNECTION_REFUSED" if "connection refused" in s
          else "TLS_FAILURE" if "ssl" in s or "certificate" in s
          else "OTHER_DB_CONNECT_FAILURE")
        return emit("BLOCKED",reason=category)
    with db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT current_user,current_database(),
                current_setting('transaction_read_only'),
                has_table_privilege(current_user,'science_lab.fixtures','SELECT'),
                has_table_privilege(current_user,'science_lab.fixtures','INSERT'),
                has_table_privilege(current_user,'science_lab.fixtures','UPDATE'),
                has_table_privilege(current_user,'science_lab.fixtures','DELETE')""")
            ident=cur.fetchone()
            if (not ident or ident[0]!=READER or ident[1]!=DATABASE
                or ident[2]!="on" or ident[3] is not True
                or any(ident[i] is True for i in (4,5,6))):
                return emit("BLOCKED",reason="READ_ONLY_LAB_IDENTITY_UNVERIFIED")
            cur.execute("""SELECT maximum_fixture_read_bytes,
                  no_automatic_snapshot,no_external_api_calls
                  FROM science_lab.usage_policy WHERE singleton=true""")
            policy=cur.fetchone()
            if (not policy or policy[0]<MAX_LOCAL_FIXTURE or policy[1] is not True
                or policy[2] is not True):
                return emit("BLOCKED",reason="LAB_POLICY_MISMATCH")
            for fixture_id, expected_md5 in ALLOWED.items():
                cur.execute("""SELECT fixture_json::text,md5(fixture_json::text),
                    octet_length(fixture_json::text)
                    FROM science_lab.fixtures WHERE fixture_id=%s
                    AND source_kind='personal'
                    AND consent_scope='owner_authorized' AND is_active=true""",
                    (fixture_id,))
                row=cur.fetchone()
                if (row is None or row[1]!=expected_md5
                    or not (0<row[2]<MAX_LOCAL_FIXTURE)):
                    return emit("BLOCKED",reason="PINNED_PRIVATE_FIXTURE_CHANGED")
                fixture=json.loads(row[0])
                out[fixture_id]=verify_fixture(fixture,nova)
                # A mutable JSON reference is never written to disk.
                del fixture, row

    scientific_ok=all(
        v["core_result_present"] and v["expected_invariant_drift_count"]==0
        and v["mutation_pass"] for v in out.values())
    return emit("TEST_EXECUTED" if scientific_ok else "SCIENTIFIC_DRIFT",
        active_lossless_fixtures=len(out),
        scientific_regression_gate="PASS" if scientific_ok else "FAIL",
        source_r150_verified=True,reader_role_verified=True,
        source_payloads_exported=False,
        fixture_replay_summaries=list(out.values()),
        owner_authenticated_future_quality="NOT_VERIFIED",
        card3_bh001="RED",
        card2_bh004="RED")


if __name__=="__main__":
    try:raise SystemExit(run())
    except Exception as exc:
        # No exception message, trace or private data in public CI logs.
        print(json.dumps({"suite":"INC132_R150_PRIVATE_REPLAY",
            "status":"BLOCKED","error_class":type(exc).__name__,
            "release":"NO_GO"}))
        raise SystemExit(2)
