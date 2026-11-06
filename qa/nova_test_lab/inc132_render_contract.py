"""INC132 acceptance seam for QA only. NOT loaded by NOVA app.
Mock issuer booleans do not verify real signatures, physiology or doses.
No training is executable/schedulable here. Production integration NO-GO.
"""
from collections.abc import Mapping
import math

TEMPO_IDS = {
    "P5_TEMPO_2X12":"POWER_5", "P5_TEMPO_2X15":"POWER_5",
    "V2_TEMPO_2X15":"VO2MAX",
    "P20_TEMPO_3X10":"POWER_20", "P20_TEMPO_2X20":"POWER_20",
    "TT_TEMPO_3X10":"TIME_TRIAL", "TT_TEMPO_2X20":"TIME_TRIAL",
}
GOALS = {"POWER_5","POWER_20","POWER_1","SPRINTER","VO2MAX","TIME_TRIAL","ENDURANCE_BASE"}

def _complete(row):
    if not isinstance(row,Mapping): return False
    blocks=row.get("blocks")
    return (all(row.get(k) is True for k in ("compiled","issuer_verified","dose_attested","fueling_attested"))
            and all(isinstance(row.get(k),str) and row[k].strip() for k in ("workout_id","plan_id"))
            and isinstance(blocks,list) and bool(blocks)
            and all(isinstance(b,Mapping) and isinstance(b.get("seconds"),(int,float))
                    and not isinstance(b.get("seconds"),bool) and math.isfinite(b["seconds"])
                    and b["seconds"]>0 and isinstance(b.get("domain"),str) and bool(b["domain"]) for b in blocks))

def project(contract,viewer_owner,live_snapshot_id,live_digest):
    """Return fail-closed structural preview of a trusted MOCK payload.
    Never selects priority itself. Does not write, schedule or approve quality.
    """
    e=[]
    owner=contract.get("owner_id")
    snapshot=contract.get("snapshot_id")
    digest=contract.get("decision_digest")
    c1,c2,c3=(contract.get("card"+str(i)) for i in (1,2,3))
    goal=contract.get("goal")
    injury=contract.get("injury")
    if not owner or viewer_owner!=owner: e.append("OWNER_SCOPE_FAIL")
    if not snapshot or not digest: e.append("SNAPSHOT_MISSING")
    if contract.get("issuer_signature_verified") is not True: e.append("ISSUER_MISSING")
    if goal not in GOALS: e.append("GOAL_INVALID")
    if not isinstance(c1,Mapping) or c1.get("role")!="CARD1" or c1.get("intensity_class") not in ("EASY","RECOVERY"):
        e.append("CARD1_BAD")
    if not _complete(c3) or c3.get("role")!="CARD3" or c3.get("goal")!=goal:
        e.append("CARD3_MISSING")
    if isinstance(c2,Mapping):
        if not _complete(c2) or c2.get("role")!="CARD2" or c2.get("domain")!="TEMPO_Z3" or c2.get("intensity_class")!="HARD":
            e.append("CARD2_BAD")
        if TEMPO_IDS.get(c2.get("workout_id"))!=goal or c2.get("goal")!=goal:
            e.append("CARD2_DOSE_UNVALIDATED")
        if isinstance(c3,Mapping) and (c2.get("workout_id")==c3.get("workout_id") or c2.get("plan_id")==c3.get("plan_id")):
            e.append("DUPLICATE_ID")
    elif c2 is None:
        if contract.get("card2_blocked_reason") not in ("GOAL_DOSE_UNVALIDATED","NO_CANDIDATE_ATTESTED","POWER_UNCALIBRATED","INJURY_RESTRICTION"):
            e.append("C2_REASON_MISSING")
    else: e.append("CARD2_BAD")
    for name,c in (("CARD1",c1),("CARD2",c2),("CARD3",c3)):
        if isinstance(c,Mapping) and (c.get("owner_id")!=owner or c.get("snapshot_id")!=snapshot):
            e.append(name+"_IDENTITY_MISMATCH")
    if injury in ("NO_TRAINING","NO_INTENSITY"):
        if c2 is not None or not isinstance(c3,Mapping) or c3.get("injury_safe_projection") is not True:
            e.append("INJURY_HARD_BLOCK")
    elif injury is not None: e.append("INJURY_UNKNOWN")
    pri=contract.get("recommended_priority")
    if pri not in ("CARD2","CARD3") or (pri=="CARD2" and not isinstance(c2,Mapping)):
        e.append("PRIORITY_INVALID")
    if not contract.get("priority_reason_code") or not contract.get("priority_evidence_ids"):
        e.append("WITNESS_MISSING")
    active=(owner==viewer_owner and snapshot==live_snapshot_id and digest==live_digest)
    return {
       "valid":not e,"errors":e,"card1":c1 if not e else None,
       "card2":c2 if not e else None,"card3":c3 if not e else None,
       "highlight":pri if not e and active and injury is None else None,
       "is_historical":not active,"can_execute":False,"can_schedule":False,
       "scope":"INC132_QA_MOCK_NOT_APP"
    }
