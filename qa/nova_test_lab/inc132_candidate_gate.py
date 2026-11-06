"""INC132 research gate on the TEST branch only. No app imports, no prescribing."""
from datetime import date
import math

GOALS = ("POWER_5","VO2MAX","POWER_1","SPRINTER","POWER_20","TIME_TRIAL","ENDURANCE_BASE")
TEMPO = {
 "POWER_5":("P5_TEMPO_2X12",2,720,300,True),
 "VO2MAX":("V2_TEMPO_2X15",2,900,300,True),
 "POWER_1":("INC132_STUDY_P1_TEMPO_2X12",2,720,300,False),
 "SPRINTER":("INC132_STUDY_SPR_TEMPO_2X12",2,720,300,False),
 "POWER_20":("P20_TEMPO_3X10",3,600,240,True),
 "TIME_TRIAL":("TT_TEMPO_3X10",3,600,240,True),
 "ENDURANCE_BASE":("INC132_STUDY_END_TEMPO_2X15",2,900,300,False),
}
Z2_STUDY_FORMATS = {
 "STEADY":(("Z2",2400),),
 "INTERVAL":(("Z2",720),("BELOW_Z2",180),("Z2",720),("BELOW_Z2",180),("Z2",720)),
 "PROGRESSIVE":(("Z2_LOWER",900),("Z2_MIDDLE",900),("Z2_UPPER_BELOW_LT1",900)),
 "CADENCE_VARIATION":(("Z2_COMFORTABLE",600),("Z2_COMFORTABLY_HIGHER",300),("Z2_COMFORTABLE",600),("Z2_COMFORTABLY_LOWER",300),("Z2_COMFORTABLE",600)),
}
SCIENCE_PMIDS=("40010355","39888556","28095074","42828469")

def _watts(x):
    try:
        if isinstance(x,bool): return None
        y=float(x)
        return y if math.isfinite(y) and 40<=y<=1500 else None
    except (TypeError,ValueError,OverflowError):
        return None

def study(goal, kind, athlete, owner, today, mode="STEADY"):
    """Never returns executable sessions, fueling, calendars or priorities."""
    if goal not in GOALS or kind not in ("Z2","TEMPO_Z3"):
        raise ValueError("INVALID_RESEARCH_INPUT")
    if kind=="Z2" and mode not in Z2_STUDY_FORMATS:
        raise ValueError("INVALID_Z2_FORMAT")
    fail=[]
    if not owner or athlete.get("owner_id")!=owner: fail.append("OWNER_MISMATCH")
    if athlete.get("source_verified") is not True: fail.append("UNVERIFIED_SOURCE")
    try:
        if date.fromisoformat(str(athlete["valid_through"]))<today: fail.append("STALE_SOURCE")
    except (KeyError,ValueError,TypeError):fail.append("NO_VALIDITY_DATE")
    if athlete.get("injury") in ("NO_TRAINING","NO_INTENSITY"):fail.append("INJURY_RESTRICTION")
    if kind=="TEMPO_Z3":
        workout,reps,work,rest,exists=TEMPO[goal]
        phases=tuple([("TEMPO_Z3",work),("RECOVERY",rest)]*(reps-1)+[("TEMPO_Z3",work)])
        ftp=_watts(athlete.get("ftp_watts"))
        if not ftp or athlete.get("ftp_status") not in ("VALID","TEST SUPPORTED"):
            fail.append("NO_ATTESTED_FTP")
        if athlete.get("hard_load_reviewed") is not True:fail.append("HARD_LOAD_NOT_REVIEWED")
        if not exists:fail.append("UNVALIDATED_GOAL_DOSE")
        power=(round(ftp*.80),round(ftp*.88)) if ftp else None
        intensity="HARD"
    else:
        workout="INC132_RESEARCH_Z2_"+mode
        phases=Z2_STUDY_FORMATS[mode]
        low=_watts(athlete.get("z2_lower_watts"))
        ceiling=_watts(athlete.get("lt1_ceiling_watts"))
        if low is None or ceiling is None or low>=ceiling or athlete.get("lt1_verified") is not True:
            fail.append("LT1_RANGE_NOT_ATTESTED")
        power=(round(low),round(ceiling)) if low and ceiling and low<ceiling else None
        intensity="EASY"
    return {
        "schema":"INC132-TEST-ONLY-1","goal":goal,"research_id":workout,
        "intensity":intensity,"phases":phases,"potential_power_watts":power if not fail else None,
        "blockers":tuple(fail),"study_screened":not bool(fail),
        "existing_inc038_template_screened":kind=="TEMPO_Z3" and TEMPO[goal][4] and not bool(fail),
        "executable":False,"scheduled":False,"recommended_priority":None,
        "fueling":None,"canonical_workout_id":None,"ledger_write":False,
        "science_pmids":SCIENCE_PMIDS
    }
