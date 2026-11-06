#!/usr/bin/env python3
"""Privacy-safe INC132 real-fixture audit: research only, never an issuer."""
import argparse
import collections
import datetime as dt
import json
import math
from pathlib import Path

TRUSTED = frozenset(("DEVICE_LAPS", "ICU_INTERVALS_CANONICAL"))
GOALS = ("POWER_1", "SPRINTER", "ENDURANCE_BASE")


def _finite(x, lo, hi):
    if type(x) not in (int, float):
        return False
    try:
        return math.isfinite(float(x)) and lo <= x <= hi
    except (OverflowError, ValueError):
        return False


def _date(x):
    if type(x) is not str or len(x) != 10:
        return None
    try:
        d = dt.date.fromisoformat(x)
        return d if d.isoformat() == x else None
    except ValueError:
        return None


def audit(snapshot):
    """Count only resolved independent observations; never authorize workouts."""
    core = snapshot.get("core_inputs", {}) if isinstance(snapshot, dict) else {}
    core = core if isinstance(core, dict) else {}
    led = core.get("evidence_ledger") or {}
    led = led if isinstance(led, dict) else {}
    repeat = led.get("repeatability") or {}
    reps = repeat.get("events") or [] if isinstance(repeat, dict) else []
    rows = led.get("events") or []
    if not isinstance(reps, list) or not isinstance(rows, list):
        reps, rows = [], []
    rc = collections.Counter(str(x.get("activity_id")) for x in reps
                             if isinstance(x, dict) and x.get("activity_id"))
    ec = collections.Counter(str(x.get("activity_id")) for x in rows
                             if isinstance(x, dict) and x.get("activity_id"))
    idx = {str(x["activity_id"]): x for x in rows if isinstance(x, dict)
           and x.get("activity_id") and ec[str(x["activity_id"])] == 1}
    verified = []
    for r in reps:
        if not isinstance(r, dict):
            continue
        aid = str(r.get("activity_id") or "")
        row = idx.get(aid)
        src = r.get("activity_truth_source")
        if (not aid or rc[aid] != 1 or not row
            or src not in TRUSTED or r.get("strong") is not True
            or r.get("activity_truth_status") != "RESOLVED"
            or row.get("activity_truth_source") != src
            or row.get("activity_truth_status") != "RESOLVED"
            or row.get("event_kind") != "TRAINING"
            or not _date(r.get("date")) or row.get("date") != r["date"]
            or row.get("repeatability") != r):
            continue
        verified.append(r)
    as_of = _date(str(snapshot.get("generated_at_local") or "")[:10]) if isinstance(snapshot, dict) else None
    as_of = as_of or dt.date.today()
    p1 = sum(_finite(r.get("interval_secs"), 45, 75)
             and r.get("pattern") not in ("MICRO_30_15", "SPRINT_CLUSTER") for r in verified)
    sprint = sum(_finite(r.get("interval_secs"), 5, 30)
                 and r.get("pattern") == "SPRINT" for r in verified)
    tempo = []
    for r in verified:
        if (type(r.get("reps")) is not int or not 2 <= r["reps"] <= 3
            or not _finite(r.get("interval_secs"), 600, 1200)
            or not _finite(r.get("recovery_secs"), 180, 600)
            or r.get("recovery_observation_complete") is not True
            or r.get("recovery_pair_count") != r.get("recovery_pair_expected")
            or r.get("recovery_pair_expected") != r["reps"] - 1
            or not _finite(r.get("ftp"), 80, 600)
            or not _finite(r.get("avg_watts"), 70, 600)
            or not .80 <= r["avg_watts"] / r["ftp"] <= .88):
            continue
        day = _date(r["date"])
        if day and 0 <= (as_of - day).days <= 42:
            tempo.append(r)
    protocols = collections.defaultdict(set)
    for r in tempo:
        protocols[(r["reps"], round(r["interval_secs"]), round(r["recovery_secs"]))].add(r["date"])
    scope = _date(led.get("scope_start"))
    endurance = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        aid = str(row.get("activity_id") or "")
        day = _date(row.get("date"))
        if (aid and ec[aid] == 1 and day and scope and scope <= day <= as_of
            and row.get("event_kind") == "TRAINING"
            and row.get("family") == "Endurance / Z2"
            and row.get("quality_relevant") is False
            and row.get("activity_truth_status") == "RESOLVED"
            and row.get("activity_truth_source") in TRUSTED
            and _finite(row.get("duration_min"), 1, 1440)):
            endurance += 1
    return {
        "schema": "INC132-THREE-GOAL-FIXTURE-AUDIT-1",
        "source": "PRIVATE_REAL_FIXTURE_READ_ONLY",
        "verified_repeat_sessions": len(verified),
        "power1_45_75s_candidates": p1,
        "sprinter_5_30s_candidates": sprint,
        "resolved_endurance_z2_sessions": endurance,
        "verified_tempo_600_1200s_sessions": len(tempo),
        "replicated_exact_tempo_protocol": any(len(days) >= 2 for days in protocols.values()),
        "goal_status": {key: "RESEARCH_ONLY_NOT_ISSUABLE" for key in GOALS},
        "scientific_review_required": True,
        "execution_authorized": False,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fixture", type=Path, help="Local authorized JSON; never commit")
    ap.add_argument("--out", type=Path, help="Private sanitized JSON output")
    args = ap.parse_args()
    output = json.dumps(audit(json.loads(args.fixture.read_text(encoding="utf-8"))),
                        indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
