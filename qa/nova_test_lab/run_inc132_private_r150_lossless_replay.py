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
    return 0 if status in ("TEST_EXECUTED",) else 2


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
    # Compare expected canonical keys only, never print private values/workout IDs.
    return {
        "expected_invariant_count":len(fixture["expected"]),
        "expected_invariant_drift_count":len(mismatched),
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

    return emit("TEST_EXECUTED",
        active_lossless_fixtures=len(out),
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
