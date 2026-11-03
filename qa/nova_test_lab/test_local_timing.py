"""LAB-R01/R02: real preview Coach Clock at local time boundaries.

These tests detect date inversion, invalid local ISO days and past-day slots,
not whether a specific athlete's preferred quality is assigned to X vs Y.
That requires a verified athlete availability contract and private replay.
"""
import os
import unittest
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo
for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
            "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key]=""

import the_lab_app as nova

ROME=ZoneInfo("Europe/Rome")
TIMES=(
    datetime(2026,11,3,6,30,tzinfo=ROME),  # AM, before possible second ride
    datetime(2026,11,3,18,30,tzinfo=ROME), # PM, after possible first ride
    datetime(2026,10,25,0,30,tzinfo=ROME), # DST fall-back boundary
    datetime(2026,10,25,3,30,tzinfo=ROME), # after fall-back
)


class CoachClockLocalBoundaryTests(unittest.TestCase):
    def test_preview_clock_dates_are_local_ordered_not_backdated(self):
        for now in TIMES:
            with self.subTest(now=now.isoformat()):
                with patch.object(nova,"get_rome_now",return_value=now):
                    data=nova.build_preview_data()
                clock=data.get("coach_clock") or {}
                slots=clock.get("next_slots") or []
                self.assertTrue(slots,"Coach Clock returned no opportunities")
                dates=[s.get("date") for s in slots if isinstance(s,dict) and s.get("date")]
                self.assertTrue(dates,"Coach Clock has no dated opportunities")
                self.assertEqual(dates,sorted(dates),"Chronology was inverted")
                for raw in dates:
                    day=date.fromisoformat(raw)
                    self.assertGreaterEqual(day,now.date(),"A new slot is in the past")
                sessions=data.get("next_sessions") or []
                self.assertTrue(sessions,"No chronological training context")
                session_dates=[s.get("date") for s in sessions
                               if isinstance(s,dict) and s.get("date")]
                self.assertEqual(session_dates,sorted(session_dates))


if __name__=="__main__":
    unittest.main(verbosity=2)
