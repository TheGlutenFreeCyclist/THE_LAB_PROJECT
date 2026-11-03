"""INC105 independent coach oracle for availability vs X/Y.

The oracle is NOT a replacement for Nova's decision engine. It marks an
expected day ahead of replay, using only approved synthetic evidence. A Card 3
UNSCHEDULED quality must NEVER inherit the oracle date as a booked workout.
"""
from datetime import date, datetime, timedelta
import unittest
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Rome")

def oracle_day(opportunities, *, last_hard_end=None, min_hard_gap_hours=36):
    """Earliest eligible opportunity after athlete availability and recovery.

    Inputs must state actual daypart availability and hard-session completion;
    unspecified availability never becomes consent to schedule.
    """
    allowed = []
    for s in opportunities:
        when = datetime.fromisoformat(s["at"])
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("local_offset_required")
        if s.get("available") is not True or s.get("blocked") is True:
            continue
        if s.get("medical_or_recovery_hold") is True:
            continue
        if s.get("completed_hard_today") is True:
            continue
        if last_hard_end is not None:
            if (when - last_hard_end).total_seconds() < min_hard_gap_hours * 3600:
                continue
        allowed.append((when, s))
    if not allowed:
        return None
    explicit = [item for item in allowed if item[1].get("athlete_explicit") is True]
    pool = explicit if explicit else allowed
    pool.sort(key=lambda item: item[0])
    return pool[0][0].date().isoformat()

def preserve_unscheduled_card3(card):
    """An advisor day never writes or backfills a Card 3 date."""
    return {"date": card.get("date"), "scheduled": bool(card.get("is_scheduled"))}


class Inc105CoachAvailabilityOracle(unittest.TestCase):
    def test_x_available_y_unavailable(self):
        last = datetime(2026, 11, 2, 9, 0, tzinfo=TZ)
        slots = [
            {"at":"2026-11-04T18:30:00+01:00","available":True,
             "athlete_explicit":True,"morning_easy_done":True},
            {"at":"2026-11-05T18:30:00+01:00","available":False,"blocked":True},
        ]
        self.assertEqual(oracle_day(slots,last_hard_end=last), "2026-11-04")

    def test_x_recovery_blocked_y_valid(self):
        hard = datetime(2026,11,4,7,0,tzinfo=TZ)
        slots = [
            {"at":"2026-11-04T18:30:00+01:00","available":True,
             "completed_hard_today":True},
            {"at":"2026-11-05T19:00:00+01:00","available":True},
        ]
        self.assertEqual(oracle_day(slots,last_hard_end=hard), "2026-11-05")

    def test_two_sessions_count_alone_does_not_veto_easy_then_quality(self):
        # A 06:30 easy ride is NOT proof the day is complete; the athlete
        # explicitly confirms the 18:30 window, with recovery still eligible.
        slots = [{"at":"2026-11-04T18:30:00+01:00","available":True,
                  "morning_easy_done":True,"today_activity_count":1}]
        self.assertEqual(oracle_day(slots), "2026-11-04")
        blocked = [{**slots[0],"medical_or_recovery_hold":True}]
        self.assertIsNone(oracle_day(blocked))

    def test_explicit_athlete_availability_beats_weekday_habit(self):
        slots=[
            {"at":"2026-11-04T18:30:00+01:00","available":True,
             "habitual_hard_day":True},
            {"at":"2026-11-05T18:30:00+01:00","available":True,
             "athlete_explicit":True},
        ]
        self.assertEqual(oracle_day(slots), "2026-11-05")

    def test_no_availability_no_fabricated_quality_day(self):
        self.assertIsNone(oracle_day([{"at":"2026-11-04T18:30:00+01:00"}]))

    def test_dst_offset_and_no_backdating(self):
        # No naive local times during fall-back ambiguity.
        d = oracle_day([{"at":"2026-10-25T02:30:00+01:00",
                         "available":True}])
        self.assertEqual(d,"2026-10-25")
        with self.assertRaises(ValueError):
            oracle_day([{"at":"2026-10-25T02:30:00","available":True}])

    def test_no_implicit_card3_calendar_write(self):
        card={"date":None,"is_scheduled":False,"workout_id":"SYNTHETIC"}
        self.assertEqual(preserve_unscheduled_card3(card),
                         {"date":None,"scheduled":False})


if __name__ == "__main__":
    unittest.main(verbosity=2)
