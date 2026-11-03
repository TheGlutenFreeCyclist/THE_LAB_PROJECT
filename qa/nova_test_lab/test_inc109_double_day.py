"""INC109: X/Y preference remains evidence-gated across two-a-day boundaries.

Never use a private athlete schedule in public CI. The native coach advisor is
read-only and cannot calendarize Card 3 on a single easy morning session.
"""
import copy
import os
import unittest
for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
            "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key]=""
from test_inc107_x_y_native import fixture as availability_fixture
from test_inc107_save_advisor import Inc107ActualAdvisorNonScheduling
import the_lab_app as nova


class Inc109XyDoubleDayBoundary(unittest.TestCase):
    def test_morning_easy_does_not_erase_explicit_x_evening(self):
        clock,road,dec=availability_fixture()
        clock.update(today_activity_count=1,am_done=True,pm_done=False,
                     today_activities_text="EASY aerobic morning only")
        original=copy.deepcopy(clock)
        match=nova._v154_explicit_quality_target(clock,road,dec)
        self.assertIsNotNone(match)
        self.assertEqual(match["index"],0)
        self.assertEqual(match["target_iso"][:10],"2026-11-04")
        self.assertEqual(clock,original)
        self.assertNotIn("calendar_event",clock)

    def test_two_sessions_without_established_load_not_falsely_completed(self):
        data=Inc107ActualAdvisorNonScheduling.baseline(2,ratio=.20)
        result=nova._nova_r196979_quality_day_advisor(data)
        self.assertFalse(result["day_complete"])
        self.assertTrue(result["session_count_is_never_a_veto"])
        self.assertFalse(result["changes_decision"])
        self.assertFalse(result["changes_prescription"])

    def test_two_sessions_and_significant_load_can_mark_day_complete(self):
        data=Inc107ActualAdvisorNonScheduling.baseline(2,ratio=.85)
        result=nova._nova_r196979_quality_day_advisor(data)
        self.assertTrue(result["day_complete"])
        self.assertFalse(result["changes_prescription"])
        self.assertFalse(result["changes_decision"])
        self.assertTrue(result["read_only"])

    def test_explicit_y_still_wins_when_x_is_blocked_after_easy_morning(self):
        clock,road,dec=availability_fixture(
            preferred="2026-11-05",blocked_x=True)
        clock.update(today_activity_count=1,am_done=True,pm_done=False)
        match=nova._v154_explicit_quality_target(clock,road,dec)
        self.assertIsNotNone(match)
        self.assertEqual(match["index"],1)
        self.assertEqual(match["target_iso"][:10],"2026-11-05")
        self.assertNotIn("calendar_event",clock)

    def test_a_blocked_day_cannot_be_overridden_by_high_double_propensity(self):
        clock,road,dec=availability_fixture(blocked_x=True)
        clock.update(today_activity_count=1,am_done=True,pm_done=False,
                     rhythm={"recent":{"double_day_pct":.95,"training_days":60}})
        self.assertIsNone(nova._v154_explicit_quality_target(clock,road,dec))
        self.assertNotIn("calendar_event",clock)

    def test_day_complete_heuristic_does_not_schedule_conditional_card(self):
        data=Inc107ActualAdvisorNonScheduling.baseline(2,ratio=.90)
        data["future_quality_plan"]={
            "status":"COMPILED_UNSCHEDULED","workout":{"date":None},
            "is_scheduled":False}
        before=copy.deepcopy(data)
        advised=nova._nova_r196979_quality_day_advisor(data)
        self.assertEqual(data,before)
        self.assertTrue(advised["day_complete"])
        self.assertNotIn("date",advised)
        self.assertFalse(advised["changes_prescription"])


if __name__=="__main__":
    unittest.main(verbosity=2)
