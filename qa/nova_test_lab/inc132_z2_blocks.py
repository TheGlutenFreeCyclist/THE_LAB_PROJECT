"""INC132 Card1 Z2 structural block precompiler. TEST research only.

Receives only screening from inc132_candidate_gate.study, never trusts a
frontend band, emits no issuer signature, no workout authority and no schedule.
Unvalidated LT1 or exercise injury -> no watt blocks.
"""
import math
from inc132_candidate_gate import study

def _number(x,low,high):
    if isinstance(x,bool):return None
    try:
        f=float(x)
        if math.isfinite(f) and low<=f<=high:return f
    except (ValueError,TypeError,OverflowError):
        pass
    return None

def _range(lo,hi):
    if isinstance(lo,int) and isinstance(hi,int) and lo<=hi and lo>=40:
        return {"watts_low":lo,"watts_high":hi}
    return None

def compile_study_z2(goal,athlete,owner,today,mode):
    """Build study blocks only; not a workout, not a recommendation."""
    candidate=study(goal,"Z2",athlete,owner,today,mode)
    reasons=list(candidate["blockers"])
    if reasons:
        return {"status":"BLOCKED","blockers":tuple(reasons),"blocks":[],
                "can_execute":False,"can_schedule":False,"canonical_workout_id":None}
    low,hi=candidate["potential_power_watts"]
    phases=candidate["phases"]
    has_recovery=any(kind=="BELOW_Z2" for kind,_ in phases)
    has_cadence=mode=="CADENCE_VARIATION"
    if mode=="PROGRESSIVE" and hi-low<2:
        reasons.append("Z2_BAND_TOO_NARROW_FOR_PROGRESSIVE")
    recovery=None
    if has_recovery:
        rlo=_number(athlete.get("recovery_lower_watts"),40,1500)
        rhi=_number(athlete.get("recovery_upper_watts"),40,1500)
        if rlo is None or rhi is None or rlo>rhi or rhi>=low:
            reasons.append("BELOW_Z2_RECOVERY_NOT_ATTESTED")
        else:
            recovery=_range(math.ceil(rlo),math.floor(rhi))
            if recovery is None or recovery["watts_high"]>=low:
                reasons.append("BELOW_Z2_RECOVERY_NOT_ATTESTED")
    rpm=None
    if has_cadence:
        rpm=_number(athlete.get("habitual_cadence_rpm"),70,105)
        if (rpm is None or athlete.get("cadence_source_verified") is not True
                or rpm-5<65 or rpm+5>110):
            reasons.append("HABITUAL_CADENCE_NOT_ATTESTED")
    if reasons:
        return {"status":"BLOCKED","blockers":tuple(reasons),"blocks":[],
                "can_execute":False,"can_schedule":False,"canonical_workout_id":None}
    span=hi-low+1
    first=low+span//3-1
    second=low+2*span//3-1
    def band(kind):
        if kind=="BELOW_Z2":return dict(recovery)
        if kind=="Z2_LOWER":return _range(low,first)
        if kind=="Z2_MIDDLE":return _range(first+1,second)
        if kind=="Z2_UPPER_BELOW_LT1":return _range(second+1,hi)
        return _range(low,hi)
    result=[]
    for kind,seconds in phases:
        item=band(kind)
        if not item:raise AssertionError("Z2_INTERNAL_PHASE_RANGE")
        item.update(domain="EASY_BELOW_LT1",purpose=kind,seconds=seconds)
        if has_cadence and kind in ("Z2_COMFORTABLY_HIGHER","Z2_COMFORTABLY_LOWER"):
            item["cadence_cue_rpm"]=int(round(rpm+(5 if kind=="Z2_COMFORTABLY_HIGHER" else -5)))
        elif has_cadence:
            item["cadence_cue_rpm"]=int(round(rpm))
        result.append(item)
    return {"schema":"INC132-Z2-STUDY-BLOCKS-1","status":"STRUCTURE_SCREENED_ONLY",
        "intensity_class":"EASY","goal":goal,"mode":mode,"blocks":result,
        "total_seconds":sum(b["seconds"] for b in result),
        "lt1_ceiling_watts":athlete["lt1_ceiling_watts"],
        "cadence_note":"Comfortable variation only; no low-cadence strength claim",
        "source":"VERIFIED_SYNTHETIC_EVIDENCE_ONLY","blockers":(),
        "can_execute":False,"can_schedule":False,"recommended_priority":None,
        "canonical_workout_id":None,"fueling":None,"ledger_write":False}
