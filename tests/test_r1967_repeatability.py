"""R196.7 isolated policy tests; avoids importing the production Flask process."""
import ast
import math
import re
from pathlib import Path
import unittest

APP_SOURCE = Path(__file__).resolve().parents[1] / 'the_lab_app.py'
class R1967(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = APP_SOURCE.read_text(encoding='utf-8')
        cls.source = source
        tree = ast.parse(source)
        cls.band_fn = next(n for n in reversed(tree.body) if isinstance(n, ast.FunctionDef) and n.name == '_v1943_band')
        cls.view_fn = next(n for n in reversed(tree.body) if isinstance(n, ast.FunctionDef) and n.name == '_v1967_athlete_session_view')

    def env(self, base):
        def _finite(v, low=0, high=1e7):
            try:
                n=float(v)
                return n if math.isfinite(n) and low<=n<=high else None
            except (ValueError, TypeError, OverflowError): return None
        ns={'_r1967_band_before': lambda *a, **kw: dict(base),
            '_v1943_finite':_finite,'re':re,
            'R1967_SCHEMA':'V4.9.91-R196.7-REPEATABILITY-AND-ATHLETE-VIEW-1'}
        exec(compile(ast.Module(body=[self.band_fn,self.view_fn],type_ignores=[]),str(APP_SOURCE),'exec'),ns)
        return ns

    def base(self, secs=360, source='COMPARABLE_VERIFIED_REPEATED_WORK'):
        return dict(state='PRESCRIBED',source=source,confidence='HIGH',
            activity_id='observed',work_seconds=420,evidence_interval_seconds=secs,
            reps=2,target_watts=335,low_watts=315,high_watts=340)

    def event(self,secs=360,recovery=298,strong=True):
        return {'activity_id':'observed','reps':3,'interval_secs':secs,
                'recovery_secs':recovery,'strong':strong}

    def test_all_seven_goals_separate_single_pb_from_repeats(self):
        for goal in ('POWER_1','POWER_5','POWER_20','SPRINTER','VO2MAX','TIME_TRIAL','ENDURANCE_BASE'):
            with self.subTest(goal=goal):
                b=self.env(self.base())['_v1943_band']({'goal':goal,'recovery_s':300},
                     evidence_ledger={'repeatability':{'events':[self.event()]}})
                self.assertEqual(b['repeatability_state'],'NOT_VERIFIED_FOR_THIS_WORKOUT')
                self.assertTrue(b['exploratory'] and b['non_punitive'])
                self.assertFalse(b['observed_single_best_is_repeatability_proof'])

    def test_strict_same_duration_and_recovery(self):
        for secs,rec,expected in [(420,300,'VERIFIED_COMPARABLE_REPEATS'),
                                  (450,300,'SUPPORTED_BY_LONGER_REPEATS'),
                                  (420,600,'NOT_VERIFIED_FOR_THIS_WORKOUT'),
                                  (360,300,'NOT_VERIFIED_FOR_THIS_WORKOUT'),
                                  (420,None,'NOT_VERIFIED_FOR_THIS_WORKOUT')]:
            with self.subTest(secs=secs,recovery=rec):
                b=self.env(self.base(secs))['_v1943_band']({'recovery_s':300},
                   evidence_ledger={'repeatability':{'events':[self.event(secs,rec)]}})
                self.assertEqual(b['repeatability_state'],expected)
                if expected == 'NOT_VERIFIED_FOR_THIS_WORKOUT':
                    self.assertEqual(b['scoring_policy'],'STRUCTURE_ONLY_POWER_DESCRIPTIVE')

    def test_ftp_starter_does_not_certify_reps(self):
        b=self.env(self.base(source='VALID_FTP_STARTER_POLICY_NOT_OBSERVED_REPEATABILITY'))['_v1943_band']({})
        self.assertTrue(b['exploratory'] and b['non_punitive'])
        self.assertEqual(b['repeatability_state'],'NOT_VERIFIED_FOR_THIS_WORKOUT')

    def test_athlete_view_exposes_real_best_not_interpolation(self):
        ns=self.env(self.base())
        session={'main_set':'EXPLORATORY POWER TARGET: 315–340 W across 2 work intervals; there is no required midpoint or validated per-rep watt target. Repeatability at the exact work/recovery dose is not yet verified. Power shortfall must not count as failure, reduce adherence or block progression; assess structure and recovery separately. 20 min warm-up then 2×7 min, 5 min recovery. Observed recent 7-min best: 324 W; exploratory neighboring-duration interpolation: ~332 W (low confidence). The estimate indicates a possible direction to explore, not achieved capacity; none of these figures is a repeated-rep workout target or a post-workout grading threshold. Cool-down: 5 min very easy Z1.',
                 'why':'diagnostic','power_prescription':dict(self.base(),exploratory=True),
                 'power_evidence':{'duration_seconds':420,'observed_recent_watts':324,
                        'observed_recent_source':'DIRECT_42D_BEST_POWER_CURVE',
                        'exploratory_estimate_watts':332}}
        before=repr(session)
        result=ns['_v1967_athlete_session_view'](session)
        self.assertIn('315–340 W',result['band_label'])
        self.assertIn('324 W',result['reference_label'])
        self.assertNotIn('332 W',str(result))
        self.assertNotIn('335 W',str(result))
        self.assertIn('20 min warm-up',result['instructions'])
        self.assertIn('Cool-down',result['instructions'])
        self.assertEqual(repr(session),before)

    def test_model_only_estimate_not_best(self):
        ns=self.env(self.base())
        view=ns['_v1967_athlete_session_view']({'power_evidence':{'duration_seconds':420,
            'exploratory_estimate_watts':332}})
        self.assertIsNone(view['reference_label'])

    def test_ui_is_projection_not_canonical_mutation(self):
        self.assertIn('nova_athlete_view(s)',self.source)
        self.assertIn('data.nutrition_plan[si]',self.source)
        self.assertIn('if quality_already_shown',self.source)

if __name__=='__main__':
    unittest.main()
