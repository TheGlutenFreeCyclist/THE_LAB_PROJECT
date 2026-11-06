"""INC132 C2: check actual R150 native science on all seven TEMPO entries.

Empty ledger is intentionally NEVER a physiological validation. This diagnoses
the fail-closed boundary; it cannot license Card2 Z3 for any athlete/goal.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
            "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key]=""
os.environ["PRODUCT_SECURITY_STRICT"]="0"
os.environ["THE_LAB_TEST_LAB_MODE"]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

import the_lab_app as nova
from inc132_catalog_inventory import catalog


def run():
    catalog_audit = catalog(Path(nova.__file__))
    if catalog_audit["status"] != "MECHANICS_ONLY":
        raise AssertionError("RESEARCH_CATALOG_STATUS_PROMOTED")
    tested=[]
    for item in catalog_audit["rows"]:
        wid=item["workout_id"]
        tpl=nova._R19696_LIBRARY_INDEX.get(wid)
        if not isinstance(tpl,dict):
            raise AssertionError("TEMPO_NOT_IN_NATIVE_LIBRARY_"+wid)
        dim=list(tpl.get("dimensions") or ())
        if not dim:
            raise AssertionError("TEMPO_NO_DIMENSIONS_"+wid)
        dimension=dim[0]
        band=nova._v1943_band(tpl,evidence_ledger={},
            ftp_anchor=None,as_of_date="2026-11-06",dimension=dimension)
        if not isinstance(band,dict):
            raise AssertionError("NATIVE_BAND_SCHEMA_CHANGED_"+wid)
        proof=nova._nova_inc083_science_replay(
            {"nova_workout_id":wid,"nova_prescription_dimension":dimension,
             "power_prescription":band},
            {}, None, {"scientific_progression":{"dimension":dimension}},
            today=date(2026,11,6))
        if (band.get("state")=="PRESCRIBED" or proof.get("accepted") is True):
            raise AssertionError("EMPTY_LEDGER_GRANTED_TEMPO_HARD_"+wid)
        tested.append({"id":wid,"goal":item["goal"],"empty_evidence_denied":True})
    if len(tested)!=7 or len(set(x["id"] for x in tested))!=7:
        raise AssertionError("CATALOG_TEMPLATE_COUNT_DRIFT")
    result={"suite":"INC132_TEMPO_R150_NATIVE_EMPTY_EVIDENCE",
        "status":"PASS_NEGATIVE_DIAGNOSTIC","catalogue_rows":len(tested),
        "goal_profiles":sorted(catalog_audit["counts"]),
        "research_only_goals":catalog_audit["research_only_goals"],
        "empty_evidence_no_hard":True,
        "scientific_personalization":"NOT_VERIFIED",
        "card2_complete_quality":"RED",
        "authenticated_raw_provenance":"NOT_VERIFIED",
        "production":"NO_GO"}
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    try:raise SystemExit(run())
    except Exception as error:
        print(json.dumps({"suite":"INC132_TEMPO_R150_NATIVE_EMPTY_EVIDENCE",
            "status":"BLOCKED","safe_error_class":type(error).__name__,
            "production":"NO_GO"}))
        raise SystemExit(2)
