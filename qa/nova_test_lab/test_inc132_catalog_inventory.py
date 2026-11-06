"""Tests only the real TEST source catalog mechanics, not physiological validity."""
import unittest
from pathlib import Path
from inc132_catalog_inventory import catalog,EXISTING_GOALS,RESEARCH_GOALS

SOURCE=Path(__file__).resolve().parents[2]/"the_lab_app.py"

class TestCatalogInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=catalog(SOURCE)
    def test_seven_real_tempo_templates(self):
        self.assertEqual(len(self.audit["rows"]),7)
    def test_four_existing_goal_profiles(self):
        self.assertEqual(set(self.audit["counts"]),EXISTING_GOALS)
    def test_three_unvalidated_goal_profiles_not_falsely_added(self):
        self.assertEqual(set(self.audit["research_only_goals"]),RESEARCH_GOALS)
    def test_no_executable_sessions(self):
        self.assertFalse(self.audit["can_execute"])
        self.assertFalse(self.audit["runtime_imported"])
        self.assertFalse(self.audit["dose_validated"])
    def test_unique_template_identity(self):
        self.assertEqual(len({r["workout_id"] for r in self.audit["rows"]}),7)
    def test_structural_variety_not_seven_identical_templates(self):
        self.assertGreaterEqual(len({r["total_work_seconds"] for r in self.audit["rows"]}),3)
    def test_no_fake_individualized_watts(self):
        self.assertTrue(all("personalized_watts" not in r for r in self.audit["rows"]))

if __name__=="__main__": unittest.main()
