"""Scoped Card2 first-dose regressions; no private athlete data or server bypass."""
import copy, os, sys, unittest
from pathlib import Path
from unittest.mock import patch

QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
from qa_stub_import import load
SRC=Path(os.environ.get('INC132_CARD2_CANDIDATE', str(QA.parents[3]/'the_lab_app.py')))

class FirstDoseCard2(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=load(SRC)
 def anchor(self,owner='OWNER',ftp=274,when='2026-10-30'):
  m=self.m
  return {'available':True,'current_rolling_ftp':ftp,'current_rolling_date':when,
          'nova_inc132_owner_token':m._inc132_r153_scope_token(owner)}
 def road(self,dim):return {'scientific_progression':{'dimension':dim}}
 def dim(self,goal):
  return {'POWER_5':'SPECIFIC_DOSE','VO2MAX':'SPECIFIC_DOSE',
    'POWER_20':'TIME_AT_PRESSURE','TIME_TRIAL':'TIME_AT_PRESSURE',
    'POWER_1':'SPECIFIC_DOSE','SPRINTER':'SPECIFIC_DOSE',
    'ENDURANCE_BASE':'AEROBIC_VOLUME'}[goal]
 def plan(self,goal,dim):return {'schema':self.m.INC091_SCHEMA,'status':'COMPILED_UNSCHEDULED',
    'goal_key':goal,'dimension':dim,'workout_id':goal+'_CARD3','inc132_dual_schema':self.m.INC132_DUAL_SCHEMA}
 def test_all_seven_goals_first_dose_complete(self):
  m=self.m
  for goal in sorted(m._INC132_CARD2_FIRST_GOALS):
   with self.subTest(goal=goal):
    dim=self.dim(goal);ft=self.anchor()
    x,why=m._inc132_build_integrative(goal,dim,{},ft,self.road(dim),None,'OWNER')
    self.assertIsInstance(x,dict,why)
    self.assertEqual(x['dose_kind'],'FIRST_TEMPO_FTP_ADVISORY')
    self.assertEqual(x['duration_minutes'],50)
    self.assertEqual(x['workout']['session_composition']['total_seconds'],3000)
    self.assertNotEqual(x['workout_id'],goal+'_CARD3')
    self.assertFalse(x['execution_authorized']);self.assertTrue(x['not_issued'])
    plan=self.plan(goal,dim);plan['inc132_integrative']=x
    data={'ftp_anchor':ft,'adaptive_roadmap':self.road(dim),'evidence_ledger':{}}
    self.assertTrue(m._inc132_validate_integrative(data,plan,'OWNER'))
 def test_other_owner_no_workout(self):
  m=self.m
  self.assertIsNone(m._inc132_card2_first_build('POWER_5','SPECIFIC_DOSE',self.anchor('SOMEONE'), 'OWNER'))
 def test_unstamped_no_card2(self):
  a=self.anchor();a.pop('nova_inc132_owner_token')
  self.assertIsNone(self.m._inc132_card2_first_build('POWER_5','SPECIFIC_DOSE',a,'OWNER'))
 def test_invalid_ftp(self):
  for v in [float('nan'),float('inf'),-3,0,700,None,True]:
   with self.subTest(v=v):
    self.assertIsNone(self.m._inc132_card2_first_build('POWER_5','SPECIFIC_DOSE',self.anchor(ftp=v),'OWNER'))
 def test_future_ftp_rejected(self):
  self.assertIsNone(self.m._inc132_card2_first_build('POWER_5','SPECIFIC_DOSE',self.anchor(when='2030-01-01'),'OWNER'))
 def test_rolling_ftp_wins_when_formal_estimate_same_day(self):
  a=self.anchor(ftp=320,when='2026-11-04')
  a.update(anchor_watts=326,anchor_date='2026-11-04')
  c=self.m._inc132_card2_first_build('POWER_20','TIME_AT_PRESSURE',a,'OWNER')
  self.assertEqual(c['workout']['power_prescription']['ftp_watts'],320)
  self.assertEqual((c['workout']['power_prescription']['low_watts'],
                    c['workout']['power_prescription']['high_watts']),(255,270))
 def test_tampered_watts_and_owner_rejected(self):
  m=self.m;dim='SPECIFIC_DOSE';ft=self.anchor()
  x=m._inc132_card2_first_build('POWER_5',dim,ft,'OWNER')
  p=self.plan('POWER_5',dim);p['inc132_integrative']=x
  data={'ftp_anchor':ft,'evidence_ledger':{},'adaptive_roadmap':self.road(dim)}
  for attr,value in [('low_watts',999),('high_watts',999)]:
   y=copy.deepcopy(x);y['workout']['power_prescription'][attr]=value
   p['inc132_integrative']=y
   self.assertFalse(m._inc132_validate_integrative(data,p,'OWNER'))
  p['inc132_integrative']=x;self.assertFalse(m._inc132_validate_integrative(data,p,'OTHER_OWNER'))
 def test_card3_unmodified_wrapper(self):
  m=self.m;dim='SPECIFIC_DOSE';ft=self.anchor()
  original=self.plan('POWER_5',dim);original.pop('inc132_dual_schema')
  with patch.object(m,'_INC132_DUAL_BEFORE_FUTURE',return_value=original):
   plan=m._nova_inc050_future_quality('OWNER',{}, {},self.road(dim),{},evidence_ledger={},ftp_anchor=ft)
  self.assertEqual(plan['workout_id'],original['workout_id'])
  self.assertEqual(plan['status'],original['status'])
  self.assertEqual(plan['inc132_integrative_state'],'CARD2_FIRST_DOSE_FTP_ADVISORY_UNSCHEDULED')
  self.assertTrue(m._inc132_validate_integrative({'ftp_anchor':ft},plan,'OWNER'))
 def test_no_issuer_weakening(self):
  m=self.m
  tpl=next(x for x in m._NOVA_WORKOUT_LIBRARY if x.get('id')=='P5_TEMPO_2X12')
  ft=self.anchor();band=m._v1943_band(tpl,evidence_ledger={},ftp_anchor=ft,
     as_of_date='2026-11-07',dimension='SPECIFIC_DOSE')
  proof=m._nova_inc083_science_replay({'nova_workout_id':tpl['id'],
    'nova_prescription_dimension':'SPECIFIC_DOSE','power_prescription':band},
      {},ft,self.road('SPECIFIC_DOSE'))
  self.assertFalse(proof.get('accepted'))
 def test_missing_card3_preserved(self):
  m=self.m;dim='SPECIFIC_DOSE';original={'schema':m.INC056_SCHEMA,'status':'PLANNING_BLOCKED','goal_key':'POWER_5','dimension':dim,'workout_id':None}
  with patch.object(m,'_INC132_DUAL_BEFORE_FUTURE',return_value=original):
   out=m._nova_inc050_future_quality('OWNER',{}, {},self.road(dim),{},evidence_ledger={},ftp_anchor=self.anchor())
  self.assertEqual(out['status'],'PLANNING_BLOCKED');self.assertNotIn('inc132_integrative',out)
 def test_no_catalog_mutation(self):
  m=self.m
  for goal in ('POWER_1','SPRINTER','ENDURANCE_BASE'):
   self.assertFalse(any(row.get('goal')==goal and row.get('work_domain')=='TEMPO_Z3' for row in m._NOVA_WORKOUT_LIBRARY))
 def test_snapshot_attests_fueling_and_exposes_card2(self):
  m=self.m;dim='SPECIFIC_DOSE';ft=self.anchor()
  x=m._inc132_card2_first_build('POWER_5',dim,ft,'OWNER')
  p=self.plan('POWER_5',dim);p['inc132_integrative']=x
  d={'ftp_anchor':ft,'evidence_ledger':{},'adaptive_roadmap':self.road(dim),
     'future_quality_plan':p,'metabolic_context':{},
     'nova_card3_workout_view':{'verified_future_plan':True,
       'workout_id':'POWER_5_CARD3','title':'Existing Card3'},
     'quality_direction_fuel':{'workout_id':'POWER_5_CARD3'}}
  with patch.object(m,'_INC132_DUAL_BEFORE_ATTEST',side_effect=lambda d,u:d):
   m._nova_inc051_attest_future_snapshot(d,'OWNER')
  self.assertEqual(d['future_quality_plan']['inc132_recommended_priority'],'CARD3')
  self.assertIn('fueling',d['future_quality_plan']['inc132_integrative'])
  with patch.object(m,'_INC132_DUAL_BEFORE_UI',side_effect=lambda obj:obj),\
       patch.object(m,'_nova_inc051_verified_owner_id',return_value='OWNER'),\
       patch.object(m,'_nova_inc091_eligible',return_value=True):
   out=m._v4891_prepare_snapshot_for_ui(d)
  self.assertIsNotNone(out['inc132_dual_quality'])
  q=out['inc132_dual_quality']
  self.assertEqual(q['quality_specific']['workout_id'],'POWER_5_CARD3')
  self.assertEqual(q['quality_integrative']['workout_id'],x['workout_id'])
  self.assertTrue(q['quality_integrative']['first_exposure'])
  self.assertTrue(q['quality_integrative']['fueling']['display'])
  self.assertFalse(q['calendar_commitment'])
 def test_ui_only_card2_label(self):
  m=self.m
  self.assertIn('zi.dose_label',m.HOME_PAGE)
  self.assertEqual(m.HOME_PAGE.count('v1962-quality-card'),4)  # preserved Card3 markup references

if __name__=='__main__':unittest.main()
