"""Eight isolated synthetic safety checks. No private fixtures in GitHub."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "goal_fixture_audit.py"
spec = importlib.util.spec_from_file_location("goal_fixture_audit", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def snap(events=(), repeats=(), scope="2026-10-01"):
    return {"core_inputs": {"evidence_ledger": {
        "events": list(events), "repeatability": {"events": list(repeats)},
        "scope_start": scope}}}


def pair(aid="A", seconds=600., watts=230., ftp=270.,
         when="2026-10-15", pattern=None):
    r = {"activity_id": aid, "date": when, "strong": True,
         "activity_truth_status": "RESOLVED",
         "activity_truth_source": "ICU_INTERVALS_CANONICAL",
         "interval_secs": seconds, "reps": 3, "recovery_secs": 300.,
         "recovery_pair_expected": 2, "recovery_pair_count": 2,
         "recovery_observation_complete": True,
         "avg_watts": watts, "ftp": ftp, "pattern": pattern}
    e = {"activity_id": aid, "date": when,
         "activity_truth_status": "RESOLVED",
         "activity_truth_source": "ICU_INTERVALS_CANONICAL",
         "event_kind": "TRAINING", "family": "Threshold",
         "quality_relevant": True, "duration_min": 60., "repeatability": r}
    return e, r


class GateTest(unittest.TestCase):
    def test_empty(self):
        r = mod.audit({})
        self.assertFalse(r["execution_authorized"])
        self.assertEqual(r["verified_repeat_sessions"], 0)
        self.assertEqual(len(r["goal_status"]), 3)

    def test_repeats_never_authorize_by_themselves(self):
        e, r = pair()
        e2, r2 = pair("B", when="2026-10-21")
        x = mod.audit(snap([e,e2], [r,r2]))
        self.assertTrue(x["replicated_exact_tempo_protocol"])
        self.assertFalse(x["execution_authorized"])

    def test_threshold_not_tempo(self):
        e,r = pair(watts=310.)
        self.assertEqual(mod.audit(snap([e],[r]))["verified_tempo_600_1200s_sessions"], 0)

    def test_duplicate_fails(self):
        e,r = pair()
        self.assertEqual(mod.audit(snap([e],[r,r]))["verified_repeat_sessions"], 0)

    def test_unsupported_source_fails(self):
        e,r = pair()
        r["activity_truth_source"] = "RAW_FALLBACK"
        self.assertEqual(mod.audit(snap([e],[r]))["verified_repeat_sessions"], 0)

    def test_no_orphan(self):
        _,r = pair()
        self.assertEqual(mod.audit(snap([],[r]))["verified_repeat_sessions"], 0)

    def test_micro_not_sprint_or_power1(self):
        e,r = pair(seconds=30., pattern="MICRO_30_15")
        x = mod.audit(snap([e],[r]))
        self.assertEqual(x["power1_45_75s_candidates"], 0)
        self.assertEqual(x["sprinter_5_30s_candidates"], 0)

    def test_endurance_native_only(self):
        e,_ = pair()
        e.pop("repeatability")
        e.update(family="Endurance / Z2", quality_relevant=False, duration_min=100.)
        self.assertEqual(mod.audit(snap([e]))["resolved_endurance_z2_sessions"], 1)
        e["activity_truth_status"] = "RAW_FALLBACK"
        self.assertEqual(mod.audit(snap([e]))["resolved_endurance_z2_sessions"], 0)
        self.assertNotIn("activity_id", mod.audit(snap([e])))


if __name__ == "__main__":
    unittest.main()
