"""LAB-G07 — seven-goal science matrix on the real R136 R115 producer.

Purpose: prove that empty scientific evidence cannot authorize a hard workout.
This is a safety baseline, not a validated prescription for an evidenced athlete.
"""
import copy
import os
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
            "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"

import the_lab_app as nova
from test_core_replay import empty_evidence_fixture

GOALS=("POWER_5","POWER_20","POWER_1","TIME_TRIAL","VO2MAX","SPRINTER","ENDURANCE_BASE")


class SevenGoalEmptyEvidenceSafety(unittest.TestCase):
    def test_all_goals_do_not_issue_evidence_free_hard_work(self):
        base=empty_evidence_fixture()
        for goal in GOALS:
            with self.subTest(goal=goal):
                ctx=copy.deepcopy(base["core_inputs"])
                ctx.setdefault("training_direction",{})["primary_goal"]=goal
                fixture=nova._v115_build_nova_replay_fixture(
                    now_local=datetime(2026,11,3,9,0,tzinfo=ZoneInfo("Europe/Rome")),
                    core_inputs=ctx,
                )
                output=nova._v115_replay_nova_core(fixture)
                view=nova._v115_replay_expected(output)
                self.assertFalse(view.get("authority_final_pass"),
                                 f"{goal}: hard authority with no evidence")
                self.assertFalse(view.get("workout_ids"),
                                 f"{goal}: workout IDs without evidence")
                self.assertEqual(view.get("hard_session_count"),0,
                                 f"{goal}: hard sessions from empty evidence")


if __name__=="__main__":
    unittest.main(verbosity=2)
