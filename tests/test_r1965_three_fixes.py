"""R196.5 regression tests: extracted pure-function contract checks, no personal data."""
import ast
import math
import unittest
from datetime import date,datetime,timedelta
from pathlib import Path
SRC=Path(__file__).resolve().parents[1].joinpath('the_lab_app.py').read_text()
T=ast.parse(SRC)
N={'_v1965_bounded','_v1965_number','_v1965_personal_deviation','compute_energy_bank','build_training_direction','_v1965_verified_quality_execution'}
F=[x for x in T.body if isinstance(x,ast.FunctionDef) and x.name in N and x.lineno>44600]
def base_energy(*a,**kw):return {'energy_spent':2,'energy_score':77}
def base_direction(*a,**kw):return {'adherence_score':82,'adherence_label':'GOOD ALIGNMENT','adherence_class':'good','headline':'Overall plan adherence is 82%.','journey_summary':'plan adherence','mesocycle_focus':'adherence window'}
E={'math':math,'date':date,'timedelta':timedelta,'get_rome_now':lambda:datetime(2026,10,16),'_v1965_energy_previous':base_energy,'_v1965_direction_previous':base_direction,'_v136_is_hard_summary':lambda x:bool(x.get('hard')),'_v153_is_training_plan':lambda x:bool(x.get('hard'))}
exec(compile(ast.Module(body=F,type_ignores=[]),'the_lab_app.py','exec'),E)
class ContractTests(unittest.TestCase):
    def energy(self,tsb,hours=7):
        return E['compute_energy_bank']('green','green',hours,metrics={'tsb':tsb,'ctl':100,'atl':85},sleep_quality=2,personal_baselines={'sleep':{'habitual_minutes':420},'resolved':{}},wellness=[])
    def test_energy_varies(self):
        self.assertNotEqual(self.energy(1)['energy_score'],self.energy(5)['energy_score'])
        self.assertNotEqual(self.energy(1,6.5)['energy_score'],self.energy(1,7.5)['energy_score'])
    def test_energy_bounds(self):
        for tsb in (-100,100,float('nan')):
            e=self.energy(tsb);self.assertTrue(5<=e['energy_score']<=100);self.assertTrue(math.isfinite(e['marker_x']))
    def test_legacy_strategy_score_not_execution(self):
        d=E['build_training_direction']([]);self.assertEqual(d['strategy_alignment_score'],82);self.assertNotIn('adherence',d['headline'].lower())
    def test_quality_links(self):
        rows=[{'hard':True,'date':'2026-10-13','nova_workout_id':'a','prescription_status':'FULFILLED','executed_activity_id':'X'},
              {'hard':True,'date':'2026-10-14','nova_workout_id':'b','prescription_status':'MISSED_UNEXECUTED'}]
        e=E['_v1965_verified_quality_execution']({'prescription_history':rows},'2026-09-01')
        self.assertEqual((e['score'],e['completed'],e['confirmed_missed']),(50,1,1))
    def test_unknown_is_unrated(self):
        r={'hard':True,'date':'2026-10-14','nova_workout_id':'a','prescription_status':'ACTIVE'}
        e=E['_v1965_verified_quality_execution']({'prescription_history':[r]},'2026-09-01')
        self.assertIsNone(e['score']);self.assertEqual(e['unresolved'],1)
    def test_no_plan_is_unrated(self):
        self.assertIsNone(E['_v1965_verified_quality_execution']({},None)['score'])
if __name__=='__main__': unittest.main()