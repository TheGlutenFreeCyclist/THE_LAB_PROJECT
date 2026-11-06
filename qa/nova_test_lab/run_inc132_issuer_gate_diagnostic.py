"""INC132 gate-level explanation for the original R150 synthetic issuer replay.

No assert that a fabricated DEVICE_LAPS marker proves genuine device provenance.
We report explicit BLOCKED states instead of inventing complete science. Real
legacy R115 core, original selector/compilation and final R136 issuer are used.
"""
import copy
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

for name in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
             "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
             "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
             "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[name]=""
os.environ["PRODUCT_SECURITY_STRICT"]="0"
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import the_lab_app as nova
from test_core_replay import empty_evidence_fixture
from test_inc108_origins import original_repetition_fixture

NOW=datetime(2026,11,3,9,0,tzinfo=ZoneInfo("Europe/Rome"))
FAKE_OWNER="inc109-only-synthetic-owner"
FAKE_SECRET="inc109-laboratory-only-signing-key-not-usable-on-production"

def public_reason(val):
    if isinstance(val,str) and len(val)<=130 and val.replace("_","").replace("-","").isalnum():
        return val
    return "UNCLASSIFIED_OR_ABSENT"

def run():
    global current_phase
    current_phase='BASE_FIXTURE'
    base=empty_evidence_fixture()
    data=copy.deepcopy(base["core_inputs"])
    evidence,_=original_repetition_fixture()
    data["evidence_ledger"]=evidence
    data["coach_clock"]={
        "iso":NOW.isoformat(),"time_period":"MORNING",
        "next_slots":[{"date":"2026-11-04","label":"Synthetic evening available", "start_minute":1110,
                       "duration_hint_min":75,"restriction":"NONE",
                       "is_planned_training":False,"is_race":False,
                       "period":"EVENING","window":"EVENING"}],
    }
    data["training_direction"]={"primary_goal":"POWER_5"}
    current_phase="BUILD_REPLAY_FIXTURE"
    base=nova._v115_build_nova_replay_fixture(now_local=NOW,core_inputs=data)
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()),patch.object(nova,"SECRET_KEY",FAKE_SECRET):
        current_phase="R115_REPLAY_CORE"
        actual=nova._v115_replay_nova_core(base)
        view=nova._v115_replay_expected(actual)
        rows=copy.deepcopy(actual.get("next_sessions") or [])
        core_data=base["core_inputs"]
        kwargs={
            "evidence_ledger":copy.deepcopy(core_data.get("evidence_ledger") or {}),
            "power_model":copy.deepcopy(core_data.get("power_model") or {}),
            "ftp_anchor":copy.deepcopy(core_data.get("ftp_anchor") or {}),
            "aerobic_metabolic_range":copy.deepcopy(core_data.get("aerobic_metabolic_range") or {}),
            "training_definitions":copy.deepcopy(core_data.get("training_definitions") or {}),
            "compile_arguments":{
                "recent_activities":copy.deepcopy(core_data.get("recent_activities") or []),
                "undefined_training_intent":copy.deepcopy(core_data.get("undefined_training_intent") or {}),
                "coaching_contract":copy.deepcopy(core_data.get("coaching_contract") or {}),
                "strength_pattern":copy.deepcopy(core_data.get("strength_pattern") or {}),
                "training_rhythm":copy.deepcopy(core_data.get("training_rhythm") or {}),
                "execution_model":copy.deepcopy(core_data.get("execution_model") or {}),
                "planning_context":copy.deepcopy(core_data.get("planning_context") or {}),
                "training_state":copy.deepcopy(core_data.get("training_state") or {})
            },
            "planning_context":copy.deepcopy(core_data.get("planning_context") or {}),
            "training_state":copy.deepcopy(core_data.get("training_state") or {})
        }
        current_phase="FINAL_R136_ISSUER"
        offer,audit=nova._nova_r196956_build_offer(
            rows,copy.deepcopy(actual.get("nova_prescription") or {}),{},
            copy.deepcopy(actual.get("nova_decision") or {}),
            copy.deepcopy(actual.get("coach_clock") or {}),
            copy.deepcopy(actual.get("adaptive_roadmap") or {}),
            copy.deepcopy(actual.get("microcycle_ledger") or {}),
            FAKE_OWNER,**kwargs)
        signed=bool(isinstance(offer,dict) and nova._nova_inc076_seal_ok(
            offer,audit,FAKE_OWNER))
        scheduled=bool((offer or {}).get("suggested_start_confirmed"))
    current_phase="VERDICT"
    res={
        "suite":"INC109_PUBLIC_SYNTHETIC_FULL_PIPELINE",
        "status":"PASS" if not scheduled else "FAIL",
        "science_authority":"PASS" if view.get("authority_final_pass") else "NOT_VERIFIED",
        "hard_session_count":view.get("hard_session_count"),
        "final_offer":"SIGNED_SYNTHETIC_ONLY" if signed else "NOT_VERIFIED",
        "final_audit_state":public_reason((audit or {}).get("state")),
        "final_audit_reason":public_reason((audit or {}).get("reason")),
        "not_automatically_calendarized":not scheduled,
        "device_origin_authenticated":False,
        "neon_app_persistence":"NOT_VERIFIED",
        "new_snapshots":0,
    }
    attempts=(audit or {}).get("slot_attempts") if isinstance(audit,dict) else None
    if not isinstance(attempts,list): attempts=[]
    res.update({
        "suite":"INC132_R150_SYNTHETIC_GATE_DIAGNOSTIC",
        "scenario":"SYNTHETIC_POWER5_NO_REAL_PROVENANCE",
        "decision_action":public_reason((actual.get("nova_decision") or {}).get("action")),
        "decision_goal":public_reason((actual.get("nova_decision") or {}).get("goal_key")),
        "prescription_status":public_reason((actual.get("nova_prescription") or {}).get("status")),
        "prescription_rejection":public_reason((actual.get("nova_prescription") or {}).get("fail_closed_reason")),
        "slot_attempt_count":len(attempts),
        "slot_reasons":[public_reason(a.get("reason")) if isinstance(a,dict) else "MALFORMED"
                        for a in attempts[:8]],
        "offer_exists":isinstance(offer,dict),
        "issuer_verified":signed,
        "no_real_data":True,
        "can_execute":False
    })
    # A false-positive signed offer, even with a PASS workflow, must never be
    # reported as a production authorization. The legacy probe's no-auto-schedule
    # test remains the sole binary gate for these synthetic inputs.
    print(json.dumps(res,sort_keys=True))
    return 0 if not scheduled else 1

if __name__=="__main__":
    current_phase="ENTRY"
    try:raise SystemExit(run())
    except Exception as exc:
        import re
        key=(exc.args[0] if type(exc) is KeyError and len(exc.args)==1 else None)
        safe_key=key if isinstance(key,str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{1,63}",key) else "REDACTED"
        print(json.dumps({"suite":"INC109_PUBLIC_SYNTHETIC_FULL_PIPELINE",
                          "status":"BLOCKED","phase":current_phase,
                          "missing_contract_field":safe_key,
                          "exception_class":type(exc).__name__}))
        raise SystemExit(2)
