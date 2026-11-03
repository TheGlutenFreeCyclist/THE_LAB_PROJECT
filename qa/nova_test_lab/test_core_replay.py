"""Mandatory full-core R115 synthetic replay on the ACTUAL NOVA module.

An empty scientific evidence base MUST NOT authorize a hard quality.
This proves real producer execution and its fail-closed baseline, not the
correctness of a fully evidenced POWER_5 or POWER_20 prescription.
"""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
import the_lab_app as nova


def empty_evidence_fixture():
    mapping = (
        "metrics", "season_stats", "training_state", "training_direction",
        "training_rhythm", "coach_clock", "planning_context", "power_achievements",
        "power_model", "ftp_anchor", "performance_evidence", "adaptive_roadmap_base",
        "strength_pattern", "microcycle_ledger_base", "evidence_ledger",
        "session_progression", "aerobic_metabolic_range", "training_definitions",
        "undefined_training_intent", "coaching_contract", "execution_model",
        "feeling_trend", "race_repeatability", "vo2_trend", "metabolic_context",
    )
    ctx = {name: {} for name in mapping}
    ctx["training_direction"] = {"primary_goal": "POWER_5"}
    ctx.update(previous_training_blocks=[], recent_activities=[], snapshot_question=None)
    return nova._v115_build_nova_replay_fixture(
        now_local=datetime(2026, 11, 3, 9, 0, tzinfo=ZoneInfo("Europe/Rome")),
        core_inputs=ctx,
    )


class RealCoreReplayTests(unittest.TestCase):
    def test_power5_empty_evidence_does_not_issue_quality(self):
        fixture = empty_evidence_fixture()
        result = nova._v115_replay_nova_core(fixture)
        self.assertIsInstance(result, dict)
        view = nova._v115_replay_expected(result)
        self.assertEqual(view["roadmap_stage_code"], "BUILD")
        self.assertEqual(view["decision_dimension"], "SPECIFIC_DOSE")
        self.assertEqual(view["hard_session_count"], 0)
        self.assertEqual(view["workout_ids"], [])
        self.assertFalse(view["authority_final_pass"])

    def test_power5_core_replay_is_deterministic(self):
        fixture = empty_evidence_fixture()
        first = nova._v115_replay_expected(nova._v115_replay_nova_core(fixture))
        second = nova._v115_replay_expected(nova._v115_replay_nova_core(fixture))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
