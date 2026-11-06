"""INC132 TEST-only Tempo/Z3 structural adapter from the ACTUAL R150 catalog.

This is a precompiler for a future branch of the SINGLE canonical producer.
It does NOT select a workout, validate a dose, authenticate the source,
sign an issuer, prescribe, plan, set priority or expose cards in the app.
"""
from datetime import date
import math
from inc132_catalog_inventory import catalog
from inc132_candidate_gate import _watts

def _valid_day(value,today):
    try: return isinstance(value,str) and date.fromisoformat(value)>=today
    except (TypeError,ValueError):return False

def _interval(lo,hi):
    a,b=_watts(lo),_watts(hi)
    if a is None or b is None or a>b:return None
    x,y=math.ceil(a),math.floor(b)
    if x>y:return None
    return dict(watts_low=x,watts_high=y)

def precompile_tempo_from_test_catalog(source,goal,workout_id,athlete,owner,today):
    """Reject unsupported goals or stale/unattested physiology, always inert."""
    base=dict(schema="INC132-TEMPO-STRUCTURE-RESEARCH-1",
        status="BLOCKED",goal=goal,workout_id=None,blocks=[],
        can_execute=False,can_schedule=False,can_sign=False,
        recommended_priority=None,issuer_signature=None,
        fuel=None,ledger_write=False,card_id=None)
    audit=catalog(source)
    rows={x["workout_id"]:x for x in audit["rows"]}
    blockers=[]
    if not isinstance(athlete,dict) or athlete.get("owner_id")!=owner or not owner:
        blockers.append("OWNER_IDENTITY_UNATTESTED")
        athlete={}
    if goal in audit["research_only_goals"]:
        blockers.append("GOAL_TEMPO_DOSE_RESEARCH_ONLY")
    row=rows.get(workout_id)
    if not row or row["goal"]!=goal:
        blockers.append("CANONICAL_TEMPO_TEMPLATE_NOT_FOUND")
    if athlete.get("source_verified") is not True or not _valid_day(athlete.get("valid_through"),today):
        blockers.append("SOURCE_NOT_FRESH_OR_UNVERIFIED")
    if athlete.get("hard_load_reviewed") is not True:
        blockers.append("HARD_EXPOSURE_NOT_REVIEWED")
    if athlete.get("injury") in ("NO_TRAINING","NO_INTENSITY"):
        blockers.append("INJURY_RESTRICTION")
    band=_interval(athlete.get("tempo_z3_lower_watts"),athlete.get("tempo_z3_upper_watts"))
    if athlete.get("tempo_zone_verified") is not True or band is None:
        blockers.append("INDIVIDUAL_Z3_BAND_UNVERIFIED")
    recovery=_interval(athlete.get("easy_recovery_lower_watts"),athlete.get("easy_recovery_upper_watts"))
    if recovery is None or (band and recovery["watts_high"]>=band["watts_low"]):
        blockers.append("PERSONAL_RECOVERY_BAND_UNVERIFIED")
    if blockers:return dict(base,blockers=tuple(blockers))
    blocks=[]
    for i in range(row["reps"]):
        blocks.append(dict(domain="TEMPO_Z3_HARD",seconds=row["work_seconds"],
                           block_index=i+1,**band))
        if i<row["reps"]-1:
            blocks.append(dict(domain="RECOVERY_EASY",seconds=row["recovery_seconds"],
                               block_index=i+1,**recovery))
    return dict(base,status="STRUCTURE_SCREENED_ONLY",workout_id=workout_id,
        blocks=blocks,blocker_count=0,blockers=(),
        work_seconds=row["total_work_seconds"],
        interval_seconds=sum(x["seconds"] for x in blocks),
        provenance="SYNTHETIC_FIELDS_ONLY_NOT_A_REAL_ISSUER",
        scientific_status="DOSE_NOT_VALIDATED_FOR_ATHLETE",
        can_execute=False,can_schedule=False,can_sign=False)
