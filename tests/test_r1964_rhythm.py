"""R196.4: synthetic weekday-evidence regression; no athlete-identifiable data."""
import ast
import unittest
from datetime import date
from pathlib import Path

TREE = ast.parse((Path(__file__).resolve().parents[1] / "the_lab_app.py").read_text(encoding="utf-8"))
FN = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "_v1964_weekday_evidence")
ENV = {"date": date}
exec(compile(ast.Module(body=[FN], type_ignores=[]), "the_lab_app.py", "exec"), ENV)
evidence = ENV["_v1964_weekday_evidence"]


class WeekdayEvidenceTests(unittest.TestCase):
    def fixture(self):
        recent = {"start_date": "2026-09-24", "end_date": "2026-10-14",
                  "weekday_probability": {0: 1, 1: 1, 2: 1, 3: 0.667, 4: 0.333, 5: 1, 6: 1}}
        established = {"start_date": "2026-09-03", "end_date": "2026-10-14",
                       "weekday_probability": {0: 0.83, 1: 0.83, 2: 0.83, 3: 0.5, 4: 0.33, 5: 0.83, 6: 1}}
        season = {"start_date": "2026-04-19", "end_date": "2026-10-14",
                  "weekday_probability": {3: 0.3, 4: 0.1}}
        scores = {0: 0.73, 1: 0.81, 2: 0.85, 3: 0.54, 4: 0.20, 5: 0.90, 6: 0.95}
        return recent, established, season, scores

    def test_sixth_day_has_independent_evidence(self):
        recent, established, season, scores = self.fixture()
        previous_five = sorted(scores, key=lambda d: -scores[d])[:5]
        actual = evidence(recent, established, season, scores, "ADAPTING")
        self.assertNotIn(3, previous_five)
        self.assertTrue(actual[3]["supported"])
        self.assertEqual(actual[3]["recent_observed"], 2)
        self.assertEqual(actual[3]["reason"], "RECENT_REPEAT")

    def test_unobserved_friday_is_not_fabricated(self):
        r, e, s, scores = self.fixture()
        actual = evidence(r, e, s, scores, "ADAPTING")
        self.assertFalse(actual[4]["supported"])
        self.assertEqual(actual[4]["recent_observed"], 1)
        self.assertEqual(actual[4]["reason"], "INSUFFICIENT_WEEKDAY_EVIDENCE")

    def test_established_day_remains_supported(self):
        r, e, s, scores = self.fixture()
        r["weekday_probability"][3] = 0.0
        e["weekday_probability"][3] = 0.833
        self.assertEqual(evidence(r, e, s, scores, "STABLE")[3]["reason"], "ESTABLISHED_REPEAT")

    def test_learning_cannot_schedule_a_day(self):
        r, e, s, scores = self.fixture()
        actual = evidence(r, e, s, scores, "LEARNING")
        self.assertFalse(any(row["supported"] for row in actual.values()))

    def test_zero_observed_dates_fail_closed(self):
        r, e, s, scores = self.fixture()
        r.update(start_date="2026-10-14", end_date="2026-10-14")
        e.update(start_date="2026-10-14", end_date="2026-10-14")
        actual = evidence(r, e, s, scores, "TRACKING")
        self.assertFalse(any(row["supported"] for row in actual.values()))

    def test_no_observation_cannot_become_day_from_score(self):
        r, e, s, scores = self.fixture()
        r["weekday_probability"][4] = 0
        e["weekday_probability"][4] = 0
        scores[4] = 0.99
        self.assertFalse(evidence(r, e, s, scores, "STABLE")[4]["supported"])


if __name__ == "__main__":
    unittest.main()
