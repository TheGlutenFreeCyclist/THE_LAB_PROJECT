"""R196.8.2: badges demand verified laps; candidate safety stays visible."""
import ast
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "the_lab_app.py"

def wrappers():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    result = {}
    for name in ("_v492_attach_execution_quality", "_v1967_athlete_session_view"):
        result[name] = next(n for n in reversed(tree.body)
                            if isinstance(n, ast.FunctionDef) and n.name == name)
    return result

class ProvenanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fns = wrappers()

    def context(self):
        def earlier(blocks, ledger=None):
            for block in blocks:
                block["progression_badges"] = [{"label":"Excellent repeatability"}, {"label":"Other badge"}]
                block["execution_quality"] = {"degradation":{"label":"EXCELLENT", "cv_pct":0.1},
                                               "adherence":{"structure":{"state":"COMPLETE"}}}
            return blocks
        g = {"_r19682_attach_execution_before":earlier,
             "_r19682_athlete_view_before":lambda s:{"why":"Explore the range"},
             "R19682_SCHEMA":"R196.8.2"}
        mod = ast.Module(body=list(self.fns.values()), type_ignores=[])
        exec(compile(mod, str(APP), "exec"), g)
        return g

    def test_raw_fallback_is_never_awarded_excellent_badge(self):
        row = {"activity_truth":{"status":"RAW_FALLBACK","confidence":"LOW","source":"ICU_INTERVALS"},
               "repeatability":None}
        result = self.context()["_v492_attach_execution_quality"]([row])[0]
        self.assertEqual([b["label"] for b in result["progression_badges"]], ["Other badge"])
        self.assertEqual(result["execution_quality"]["degradation"]["label"], "UNVERIFIED INTERVAL BOUNDARIES")
        self.assertEqual(result["execution_quality"]["degradation"]["cv_pct"], 0.1)
        self.assertEqual(result["execution_quality"]["adherence"]["structure"]["state"], "COMPLETE")

    def test_resolved_canonical_repeats_keep_badge(self):
        row = {"activity_truth":{"status":"RESOLVED","confidence":"HIGH","source":"ICU_INTERVALS_CANONICAL"},
               "repeatability":{"source":"ICU_INTERVALS_CANONICAL","watts":[340,341,344]}}
        result = self.context()["_v492_attach_execution_quality"]([row])[0]
        self.assertEqual(result["progression_badges"][0]["label"], "Excellent repeatability")
        self.assertEqual(result["execution_quality"]["degradation"]["label"], "EXCELLENT")

    def test_missing_canonical_watts_not_certified(self):
        row = {"activity_truth":{"status":"RESOLVED","confidence":"HIGH","source":"DEVICE_LAPS"},
               "repeatability":{"source":"DEVICE_LAPS","watts":[340]}}
        result = self.context()["_v492_attach_execution_quality"]([row])[0]
        self.assertNotIn("Excellent repeatability", [b["label"] for b in result["progression_badges"]])

    def test_candidate_quality_retains_recovery_gate(self):
        view = self.context()["_v1967_athlete_session_view"]({"provisional_quality":True})
        self.assertIn("next recovery check", view["why"])
        self.assertIn("Explore the range", view["why"])

    def test_confirmed_easy_does_not_get_quality_gate(self):
        view = self.context()["_v1967_athlete_session_view"]({"provisional_quality":False})
        self.assertEqual(view["why"], "Explore the range")

if __name__ == "__main__":
    unittest.main()
