"""Experimental synthetic R115 replay probe. Never touches external integrations.

Output contains only error class and the final traceback frames for a *synthetic*
case. NOT part of the required release gate until a valid fixture is proven.
"""
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
for key in ["DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY", "ICU_ATHLETE_ID",
            "GARMIN_EMAIL", "GARMIN_PASSWORD", "ANTHROPIC_API_KEY",
            "THE_LAB_STANDARD_AI_API_KEY", "THE_LAB_PLATFORM_AI_API_KEY"]:
    os.environ[key]=""
os.environ["PRODUCT_SECURITY_STRICT"]="0"
os.environ["SESSION_COOKIE_SECURE"]="0"
import the_lab_app as nova

def main():
    fields = (
        "metrics", "season_stats", "training_state", "training_direction",
        "training_rhythm", "coach_clock", "planning_context", "power_achievements",
        "power_model", "ftp_anchor", "performance_evidence", "adaptive_roadmap_base",
        "strength_pattern", "microcycle_ledger_base", "evidence_ledger",
        "session_progression", "aerobic_metabolic_range", "training_definitions",
        "undefined_training_intent", "coaching_contract", "execution_model",
        "feeling_trend", "race_repeatability", "vo2_trend", "metabolic_context",
        )
    data={k:{} for k in fields}
    data.update(training_direction={"primary_goal":"POWER_5"},
                previous_training_blocks=[],recent_activities=[],snapshot_question=None)
    fixture=nova._v115_build_nova_replay_fixture(
        now_local=datetime(2026,11,3,9,0,tzinfo=ZoneInfo("Europe/Rome")),
        core_inputs=data)
    try:
        result=nova._v115_replay_nova_core(fixture)
        assert isinstance(result,dict)
        print(json.dumps({"probe":"R115_FULL_CORE","status":"PASS",
                          "keys":len(result),
                          "summary":nova._v115_replay_expected(result)}))
        return 0
    except Exception as exc:
        print(json.dumps({"probe":"R115_FULL_CORE","status":"NEEDS_REALISTIC_SYNTHETIC_FIXTURE",
                          "error_type":type(exc).__name__,
                          "last_frames":[{"function":x.name,"line":x.lineno}
                                         for x in traceback.extract_tb(exc.__traceback__)[-5:]]}))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
