"""INC132 read-only AST inventory of the actual TEST app.
No Flask import, database, owner data, athlete prescription, or producer patch.
"""
import ast
from collections import Counter
from pathlib import Path

EXISTING_GOALS={"POWER_5","POWER_20","VO2MAX","TIME_TRIAL"}
RESEARCH_GOALS={"POWER_1","SPRINTER","ENDURANCE_BASE"}

def catalog(path):
    root=ast.parse(Path(path).read_text(encoding="utf-8"),filename=str(path))
    anchors=[node.value for node in root.body if isinstance(node,ast.Assign)
             and any(isinstance(t,ast.Name) and t.id=="_INC038_COMPLEMENTARY" for t in node.targets)]
    if len(anchors)!=1: raise ValueError("INC038_ANCHOR_DRIFT")
    rows=ast.literal_eval(anchors[0]) # no arbitrary AST execution
    if not isinstance(rows,tuple) or len(rows)!=7: raise ValueError("INC038_EXPECTED_SEVEN")
    audit=[]
    for r in rows:
        if not isinstance(r,tuple) or len(r)!=8: raise ValueError("INC038_ROW_SHAPE")
        wid,goal,dims,reps,work,rest,priority,title=r
        if not (isinstance(wid,str) and wid.endswith(("2X12","2X15","3X10","2X20"))
                and goal in EXISTING_GOALS and isinstance(dims,tuple) and bool(dims)
                and isinstance(reps,int) and not isinstance(reps,bool)
                and isinstance(work,int) and isinstance(rest,int)
                and 2<=reps<=3 and 600<=work<=1200 and 0<rest<=600
                and isinstance(priority,int) and 0<=priority<=100
                and isinstance(title,str) and "Tempo" in title):
            raise ValueError("INC038_METADATA_DRIFT")
        audit.append({"workout_id":wid,"goal":goal,"work_seconds":work,"reps":reps,
                      "recovery_seconds":rest,"total_work_seconds":work*reps})
    ids={r["workout_id"] for r in audit}
    if len(ids)!=7 or {r["goal"] for r in audit}!=EXISTING_GOALS:
        raise ValueError("INC038_PROFILE_OR_DUPLICATE_DRIFT")
    return {"rows":audit,"counts":dict(Counter(r["goal"] for r in audit)),
            "research_only_goals":sorted(RESEARCH_GOALS),"runtime_imported":False,
            "can_execute":False,"dose_validated":False,"status":"MECHANICS_ONLY"}
