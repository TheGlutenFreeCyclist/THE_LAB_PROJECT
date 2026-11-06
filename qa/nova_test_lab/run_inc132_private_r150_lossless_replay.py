#!/usr/bin/env python3
"""INC132 R150 TEST: privacy-preserving replay of existing authorized LAB fixtures.

Reads only NOVA SCIENCE TEST LAB through nova_r139_qa_reader. Requires an
already-configured private Actions secret. No live providers, new Snapshot,
production app/database access, writes, private logs, raw artifacts, or HMAC
shortcut. Each lossless JSON is an R115 recorded input, NOT raw FIT bytes.
"""
import contextlib
import copy
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


def _inc132_safe_code(value):
    """Only published code-shaped enums, never free text / IDs / watt values."""
    import re
    val = value if isinstance(value, str) else ""
    return val if re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", val) else "UNCLASSIFIED"


def _inc132_stage_summary(row):
    if not isinstance(row, dict):
        return {"status": "NON_DICT"}
    review = row.get("inc111_rejected_candidates")
    review = review if isinstance(review, list) else []
    counts = {}
    for item in review:
        reason = _inc132_safe_code(item.get("reason")) if isinstance(item, dict) else "UNCLASSIFIED"
        counts[reason] = counts.get(reason, 0) + 1
    library = row.get("workout_library") or {}
    library = library if isinstance(library, dict) else {}
    raw = next((x for x in (row.get("raw_sessions") or [])
                if isinstance(x, dict) and str(x.get("intensity") or "").upper().startswith("HARD")), {})
    band = raw.get("_tl_v1943_power_band") or {}
    band = band if isinstance(band, dict) else {}
    cc = row.get("coach_compiler_contract") or {}
    cc = cc if isinstance(cc, dict) else {}
    return {
        "status": _inc132_safe_code(row.get("status")),
        "hard": row.get("hard_prescription_available") is True,
        "requested_hard": row.get("requested_hard_prescription_available") is True,
        "raw_hard_count": sum(1 for x in (row.get("raw_sessions") or [])
            if isinstance(x, dict) and str(x.get("intensity") or "").upper().startswith("HARD")),
        "closed_reason": _inc132_safe_code(row.get("fail_closed_reason")),
        "workout_library_reason": _inc132_safe_code(library.get("reason")),
        "numeric_band_state": _inc132_safe_code(band.get("state")),
        "numeric_band_source": _inc132_safe_code(band.get("source")),
        "numeric_repeatability_state": _inc132_safe_code(band.get("repeatability_state")),
        "numeric_band_has_activity_binding": bool(band.get("activity_id")),
        "numeric_band_recovery_comparable": band.get("recovery_duration_comparable") is True,
        "inc111_rejected_count": len(review),
        "inc111_rejected_reason_counts": counts,
        "compiler_state": _inc132_safe_code(cc.get("state")),
    }


def _inc132_alternative_numeric_scan(fixture, result, nova, clock):
    """Aggregate ORIGINAL catalog/model/replay only; no IDs, doses or timing.
    It cannot prove owner/RAW provenance or issue any workout. Diagnostic only.
    """
    inputs = fixture.get("core_inputs") or {}
    decision = result.get("nova_decision") or {}
    roadmap = result.get("adaptive_roadmap") or {}
    sci = roadmap.get("scientific_progression") or {}
    goal = str(decision.get("goal_key") or "")
    dim = str(sci.get("dimension") or decision.get("dimension") or "")
    ledger = inputs.get("evidence_ledger") or {}
    ftp = inputs.get("ftp_anchor") or {}
    rawclock = inputs.get("coach_clock") or {}
    slots = rawclock.get("next_slots") or []
    slots = slots if isinstance(slots, list) else []
    limits = []
    for slot in slots:
        if not isinstance(slot, dict) or slot.get("is_race") is True:
            continue
        if str(slot.get("restriction") or "NONE").upper() != "NONE":
            continue
        val = nova._nova_quality_slot_declared_seconds(slot)
        if type(val) in (int, float) and val > 0:
            limits.append(val)
    templates = [t for t in nova._NOVA_WORKOUT_LIBRARY
                 if isinstance(t, dict) and t.get("goal") == goal
                 and dim in set(t.get("dimensions") or ())
                 and not t.get("adaptive_only")]
    if len(templates) > 250:
        raise ValueError("CATALOGUE_SCAN_SIZE_UNEXPECTED")
    tally = {"goal_dimension_catalogue_count": len(templates),
             "eligible_declared_slot_count": len(limits),
             "numeric_bands_prescribed": 0,
             "bands_with_repeated_work_source": 0,
             "original_science_replay_accepted": 0,
             "replay_accepted_and_declared_time_feasible": 0,
             "original_science_replay_checked": 0,
             "science_model_exceptions": 0,
             "unassessable_template_duration": 0,
             "native_unscheduled_compiled": 0,
             "native_unscheduled_withheld": 0,
             "native_compiler_errors": 0,
             "native_compiler_invented_booking": 0}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        with patch.object(nova, "get_rome_now", return_value=clock):
            for t in templates:
                try:
                    band = nova._v1943_band(t,
                        evidence_ledger=ledger, ftp_anchor=ftp,
                        as_of_date=clock.date().isoformat(), dimension=dim)
                    if not isinstance(band, dict) or band.get("state") != "PRESCRIBED":
                        continue
                    tally["numeric_bands_prescribed"] += 1
                    if band.get("source") != "COMPARABLE_VERIFIED_REPEATED_WORK":
                        continue
                    tally["bands_with_repeated_work_source"] += 1
                    tally["original_science_replay_checked"] += 1
                    science = nova._nova_inc083_science_replay(
                        {"nova_workout_id": t.get("id"),
                         "nova_prescription_dimension": dim,
                         "power_prescription": band},
                        ledger, ftp, {"scientific_progression": {"dimension": dim}},
                        today=clock.date())
                    if not isinstance(science, dict) or science.get("accepted") is not True:
                        continue
                    tally["original_science_replay_accepted"] += 1
                    # The original INC091 native compiler has NO calendar slot
                    # and no owner authentication here. Count numeric-only
                    # completeness, never issue a quality or save the result.
                    try:
                        native = nova._nova_inc091_compile_native(
                            t, {"goal_key": goal, "dimension": dim,
                                "workout_id": t.get("id")},
                            ledger, ftp, roadmap, power_model=inputs.get("power_model") or {})
                        if not isinstance(native, dict):
                            tally["native_unscheduled_withheld"] += 1
                        elif native.get("is_scheduled") is not False or native.get("date") is not None:
                            tally["native_compiler_invented_booking"] += 1
                        elif (native.get("nova_prescription_authority") is False
                              and (native.get("power_prescription") or {}).get("source")
                                  == "COMPARABLE_VERIFIED_REPEATED_WORK"
                              and (native.get("session_composition") or {}).get("total_seconds")):
                            tally["native_unscheduled_compiled"] += 1
                        else:
                            tally["native_unscheduled_withheld"] += 1
                    except (TypeError, ValueError, KeyError, ArithmeticError, OverflowError,
                            IndexError, AttributeError, RecursionError):
                        tally["native_compiler_errors"] += 1
                    required = nova._nova_quality_template_required_seconds(t, dim)
                    if type(required) not in (int, float):
                        tally["unassessable_template_duration"] += 1
                    elif any(required <= limit for limit in limits):
                        tally["replay_accepted_and_declared_time_feasible"] += 1
                except (TypeError, ValueError, KeyError, ArithmeticError, OverflowError,
                        IndexError, AttributeError, RecursionError):
                    tally["science_model_exceptions"] += 1
    tally["interpretation"] = (
        "POTENTIAL_SELECTION_GAP" if tally["replay_accepted_and_declared_time_feasible"]
        else "ORIGINAL_REPLAYED_BUT_NO_DECLARED_SLOT" if tally["original_science_replay_accepted"]
        else "NO_ORIGINAL_REPLAY_APPROVED_NUMERIC_CANDIDATE")
    # Deliberately NO owner, NO Flask request and NO raw receipt. The live
    # future authority may provide only a planning explanation, never a sealed
    # or compiled athlete-facing prescription based on replayed JSON alone.
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(nova, "get_rome_now", return_value=clock):
                future = nova._nova_inc050_future_quality(
                    None,
                    copy.deepcopy(result.get("nova_decision") or {}),
                    copy.deepcopy(rawclock),
                    copy.deepcopy(roadmap),
                    copy.deepcopy(result.get("microcycle_ledger") or {}),
                    evidence_ledger=copy.deepcopy(ledger),
                    power_model=copy.deepcopy(inputs.get("power_model") or {}),
                    ftp_anchor=copy.deepcopy(ftp),
                    training_definitions=copy.deepcopy(inputs.get("training_definitions") or {}),
                    planning_context=copy.deepcopy(inputs.get("planning_context") or {}),
                    training_state=copy.deepcopy(inputs.get("training_state") or {}),
                    active_offer=None)
        future = future if isinstance(future, dict) else {}
        tally["unowned_future_planner_status"] = _inc132_safe_code(future.get("status"))
        tally["unowned_future_reason_codes"] = [
            _inc132_safe_code(x) for x in (future.get("reason_codes") or [])[:5]
            if isinstance(x, str)]
        preflight = future.get("inc088_selector_preflight") or {}
        preflight = preflight if isinstance(preflight, dict) else {}
        tally["unowned_future_selector_state"] = _inc132_safe_code(preflight.get("state"))
        tally["unowned_future_selector_reason"] = _inc132_safe_code(preflight.get("reason"))
        tally["unowned_future_selector_calls"] = (
            preflight.get("selector_calls") if type(preflight.get("selector_calls")) is int else None)
        rejected = preflight.get("rejected") or []
        rejected = rejected if isinstance(rejected, list) else []
        reason_counts = {}
        for rej in rejected:
            code = _inc132_safe_code(rej.get("reason")) if isinstance(rej, dict) else "UNCLASSIFIED"
            reason_counts[code] = reason_counts.get(code, 0) + 1
        tally["unowned_future_rejection_reason_counts"] = reason_counts
        tally["unowned_future_origin_state"] = _inc132_safe_code(
            (future.get("inc091_integrity") or {}).get("state"))
        tally["unowned_future_has_compiled_workout"] = isinstance(future.get("workout"), dict)
        if (future.get("status") in {"COMPILED_UNSCHEDULED", "OFFERED"}
            or future.get("execution_authorized") is True
            or isinstance(future.get("workout"), dict)):
            raise AssertionError("UNAUTHENTICATED_FUTURE_WORKOUT_ACCEPTED")
    except AssertionError:
        raise
    except (TypeError, ValueError, KeyError, ArithmeticError, OverflowError,
            IndexError, AttributeError, RecursionError):
        tally["unowned_future_planner_status"] = "DIAGNOSTIC_EXCEPTION"
        tally["unowned_future_origin_state"] = "NOT_VERIFIED"
        tally["unowned_future_has_compiled_workout"] = False
    tally["raw_fit_owner_provenance"] = "NOT_VERIFIED"
    return tally


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
    # Snapshot the ORIGINAL function boundaries, never substitute a producer,
    # scientific decision, compiler, fake owner, or fabricated FIT receipt.
    monitored = ("_INC111_PRODUCER_BEFORE", "build_nova_prescription",
                 "_v196920_guard_native_r27", "compile_nova_prescription",
                 "_v1953_adapt_prescription")
    originals = {name: getattr(nova, name) for name in monitored}
    stages = {}
    upstream = {"calls": 0, "hard_candidates": 0, "statuses": {},
                "closed_reasons": {}, "hard_candidate_band_classes": []}

    def spy(name, original):
        def wrapped(*args, **kwargs):
            if name == "compile_nova_prescription" and args:
                stages["compiler_input"] = _inc132_stage_summary(args[0])
            response = original(*args, **kwargs)
            row = response[0] if name == "_v196920_guard_native_r27" and isinstance(response, tuple) else response
            summary = _inc132_stage_summary(row)
            if name == "_INC111_PRODUCER_BEFORE":
                upstream["calls"] += 1
                upstream["hard_candidates"] += int(summary["hard"])
                if summary["hard"] and len(upstream["hard_candidate_band_classes"]) < 5:
                    upstream["hard_candidate_band_classes"].append({
                        k: summary[k] for k in (
                            "numeric_band_state", "numeric_band_source",
                            "numeric_repeatability_state", "numeric_band_has_activity_binding",
                            "numeric_band_recovery_comparable")})
                state = summary["status"]
                upstream["statuses"][state] = upstream["statuses"].get(state, 0) + 1
                cause = summary["closed_reason"]
                upstream["closed_reasons"][cause] = upstream["closed_reasons"].get(cause, 0) + 1
            else:
                stages[name] = summary
            return response
        return wrapped

    # All private input/output and legacy diagnostics stay in memory only.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        with patch.object(nova, "get_rome_now", return_value=clock):
            with contextlib.ExitStack() as stack:
                for name, original in originals.items():
                    stack.enter_context(patch.object(nova, name, spy(name, original)))
                result = nova._v115_replay_nova_core(fixture)
            view = nova._v115_replay_expected(result)
            mutations = nova._v115_replay_mutation_suite(fixture)
    alternatives = _inc132_alternative_numeric_scan(fixture, result, nova, clock)
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
        "stage_trace": stages,
        "upstream_producer_observations": upstream,
        "original_catalogue_alternative_scan": alternatives,
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
