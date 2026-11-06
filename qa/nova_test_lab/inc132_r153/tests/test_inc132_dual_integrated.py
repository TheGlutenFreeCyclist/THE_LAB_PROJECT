"""INC132 R153 BH dual-quality engineering QA: synthetic truth only.

Synthetic positive science establishes that an already-repeated exact Tempo
workload can be compiled. The live origin check remains a separate Flask/server
boundary and is not mocked into a false E2E attestation claim.
"""
import ast, copy, hashlib, math, os, unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from qa_stub_import import load

HERE=Path(__file__).resolve().parent
CANDIDATE=Path(os.getenv('INC132_DUAL_CANDIDATE',HERE.parent/'implementation/the_lab_app_R153_DUAL_QA.py'))
BASELINE=HERE/'R150_BASELINE'/'the_lab_app.py'

class DualQualityQA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=load(CANDIDATE)
  cls.tpl=next(t for t in cls.m._NOVA_WORKOUT_LIBRARY if t['id']=='P5_TEMPO_2X12')

 def record(self,aid,date_str,avg_watts,ftp=250,**replace):
  r={'activity_id':aid,'date':date_str,'strong':True,
      'activity_truth_source':'DEVICE_LAPS','activity_truth_status':'RESOLVED',
      'recovery_observation_complete':True,'recovery_pair_count':1,
      'recovery_pair_expected':1,'reps':2,'interval_secs':720,
      'recovery_secs':300,'avg_watts':avg_watts,'ftp':ftp}
  r.update(replace)
  e={'activity_id':aid,'date':date_str,'event_kind':'TRAINING',
      'activity_truth_source':'DEVICE_LAPS','activity_truth_status':'RESOLVED',
      'repeatability':r,'goal_key':'POWER_5'}
  return r,e

 def ledger(self,**change):
  a,ea=self.record('verified-device-A','2026-11-01',205)
  b,eb=self.record('verified-device-B','2026-10-28',208)
  for key,value in change.items():
   if key.startswith('a_'):
    a[key[2:]]=value
   elif key.startswith('b_'):
    b[key[2:]]=value
  ea['repeatability']=a;eb['repeatability']=b
  return {'repeatability':{'events':[a,b]},'events':[ea,eb]}

 def band(self,ledger=None):
  return self.m._v1943_band(self.tpl,evidence_ledger=ledger or self.ledger(),
      ftp_anchor=None,as_of_date='2026-11-06',dimension='SPECIFIC_DOSE')

 def road(self):return {'scientific_progression':{'dimension':'SPECIFIC_DOSE'}}

 def witness(self,ledger,band):
  return self.m._nova_inc083_science_replay({'nova_workout_id':self.tpl['id'],
      'nova_prescription_dimension':'SPECIFIC_DOSE', 'power_prescription':band},
      ledger,None,self.road(),today=date(2026,11,6))

 def native(self,ledger=None):
  l=ledger or self.ledger()
  return self.m._nova_inc091_compile_native(self.tpl,
      {'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':self.tpl['id']},
      l,None,self.road())

 def truth_stub(self,ledger,band,owner,producer_request=True):
  # Server boundary SIMULATION. A mocked stamp is not authenticated E2E.
  return {'state':'SERVER_RESOLVED_TRUTH_REPLAYED',
       'activity_id':band['activity_id'],
       'owner_scope':self.m._nova_inc050_owner_scope(owner),
       'event_digest':hashlib.sha256(band['activity_id'].encode()).hexdigest()}

 def test_01_original_science_is_unchanged_except_tempo_wrapper(self):
  base=ast.parse(BASELINE.read_text())
  cand=ast.parse(CANDIDATE.read_text())
  def bodies(tree,name):
   return [ast.dump(n,include_attributes=False) for n in tree.body
     if isinstance(n,ast.FunctionDef) and n.name==name]
  for name in ('_nova_inc056_plan_result','_nova_r196956_build_offer',
                '_nova_inc051_verified_owner_id','_nova_inc075_valid_compiled_duration'):
   self.assertEqual(bodies(base,name),bodies(cand,name),name)
  orig=bodies(base,'_nova_inc083_science_replay');extended=bodies(cand,'_nova_inc083_science_replay')
  self.assertEqual(extended[:len(orig)],orig)
  self.assertEqual(len(extended),len(orig)+1)
  self.assertIn('_INC132_TEMPO_BEFORE_REPLAY',extended[-1])

 def test_02_replayed_two_exact_workouts_is_valid(self):
  ledger=self.ledger();band=self.band(ledger)
  self.assertEqual(band['source'],'COMPARABLE_VERIFIED_REPEATED_WORK')
  self.assertEqual((band['low_watts'],band['high_watts']),(200,210))
  self.assertEqual(band['workout_specific_proof'],'TWO_EXACT_VERIFIED_TEMPO_SESSIONS')
  self.assertIs(self.witness(ledger,band)['accepted'],True)

 def test_03_measured_tempo_without_ftp_still_works(self):
  b=self.band()
  self.assertEqual(b['source'],'COMPARABLE_VERIFIED_REPEATED_WORK')
  self.assertNotIn('ftp_watts',b)

 def test_04_native_compiler_actual_envelope(self):
  w=self.native();self.assertIsInstance(w,dict)
  self.assertTrue(self.m._nova_inc075_valid_compiled_duration(w))
  self.assertTrue(self.m._v19696_execution_contract(w).get('ready'))
  self.assertEqual(w['nova_workout_id'],self.tpl['id'])
  self.assertIsNone(w['date']);self.assertEqual(w['session_duration_feasibility']['state'],'UNASSESSED')

 def test_05_invalid_evidence_cases_rejected(self):
  cases=[
   {'b_activity_id':'verified-device-A'},
   {'b_date':'2026-11-01'},
   {'b_date':'2026-08-01'},
   {'b_date':'2026-11-08'},
   {'a_avg_watts':255},                 # threshold/Z4, not measured Tempo
   {'b_avg_watts':183},                 # outside 80–88% of verified session FTP
   {'a_ftp':float('nan')},
   {'b_strong':False},
   {'b_recovery_observation_complete':False},
   {'b_recovery_pair_count':0},
   {'b_interval_secs':600},
   {'a_activity_truth_status':'UNRESOLVED'},
   {'b_activity_truth_source':'MANUAL'},
  ]
  for changes in cases:
   with self.subTest(changes=changes):
    l=self.ledger(**changes)
    b=self.band(l)
    self.assertNotEqual(b.get('tempo_proof_schema'),self.m.INC132_TEMPO_SCHEMA)
    self.assertNotEqual(self.witness(l,b).get('accepted'),True)

 def test_06_repeated_row_not_mirrored_in_activity_ledger(self):
  ledger=self.ledger()
  ledger['events'][1]['repeatability']={'tampered':True}
  self.assertNotEqual(self.band(ledger).get('tempo_proof_schema'),self.m.INC132_TEMPO_SCHEMA)

 def test_07_forged_watt_band_fails_replay(self):
  ledger=self.ledger();band=self.band(ledger)
  for key,value in [('high_watts',244),('second_activity_id','third'),
                    ('observed_dose_digest','0'*64),('no_progression',False)]:
   other=dict(band,**{key:value})
   self.assertFalse(self.witness(ledger,other)['accepted'],key)

 def test_08_ftp_only_original_rejection_retained(self):
  anchor={'available':True,'current_rolling_ftp':274,'current_rolling_date':'2026-10-20'}
  b=self.m._v1943_band(self.tpl,evidence_ledger={},ftp_anchor=anchor,
      as_of_date='2026-11-06',dimension='SPECIFIC_DOSE')
  self.assertEqual(b['source'],'DATED_FTP_TEMPO_STARTER_NOT_REPEATABILITY')
  self.assertEqual(self.witness({},b)['reason'],'CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN')

 def test_09_no_cross_goal_library_mutation(self):
  for goal in self.m._INC132_RESEARCH_ONLY_GOALS:
   self.assertFalse(any(x.get('goal')==goal and x.get('work_domain')=='TEMPO_Z3'
       for x in self.m._NOVA_WORKOUT_LIBRARY))
  self.assertEqual(set(self.m._INC132_RESEARCH_ONLY_GOALS),{'POWER_1','SPRINTER','ENDURANCE_BASE'})

 def test_10_no_owner_trust_means_no_card2(self):
  c,why=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),
      None,self.road(),None,'OWNER')
  self.assertIsNone(c)
  self.assertEqual(why,'NO_EXACT_INDEPENDENT_TEMPO_DOSE_ATTESTED')

 def test_11_owner_bound_trust_allows_tempo_candidate(self):
  with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub):
   c,why=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),
       None,self.road(),None,'OWNER')
   self.assertEqual(why,'VERIFIED')
   self.assertTrue(c['not_issued'])
   self.assertFalse(c['execution_authorized'])
   self.assertTrue(c['no_calendar'])
   self.assertEqual(c['workout_id'],'P5_TEMPO_2X12')
   self.assertEqual(len(c['evidence_ids']),2)

 def test_12_c2_does_not_erase_card3_and_is_a_single_producer_extension(self):
  original={'schema':self.m.INC091_SCHEMA,'status':'COMPILED_UNSCHEDULED',
      'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'CARD3_OTHER'}
  with patch.object(self.m,'_INC132_DUAL_BEFORE_FUTURE',return_value=original),\
       patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub):
   plan=self.m._nova_inc050_future_quality('OWNER',{}, {},self.road(),{},
       evidence_ledger=self.ledger(),ftp_anchor=None)
  self.assertEqual(plan['workout_id'],'CARD3_OTHER')
  self.assertEqual(plan['inc132_integrative']['workout_id'],'P5_TEMPO_2X12')
  self.assertNotEqual(plan['inc132_integrative']['workout_id'],plan['workout_id'])

 def test_13_injury_stops_integrative(self):
  original={'schema':self.m.INC091_SCHEMA,'status':'COMPILED_UNSCHEDULED',
      'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'C3'}
  with patch.object(self.m,'_INC132_DUAL_BEFORE_FUTURE',return_value=original),\
       patch.object(self.m,'_nova_inc079_explicit_injury_restriction',return_value='NO INTENSITY'):
   plan=self.m._nova_inc050_future_quality('OWNER',{}, {},self.road(),{},evidence_ledger=self.ledger())
  self.assertNotIn('inc132_integrative',plan)

 def test_14_incomplete_card3_not_hidden_or_autocleared(self):
  original={'schema':self.m.INC056_SCHEMA,'status':'PLANNING_BLOCKED',
      'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':None}
  with patch.object(self.m,'_INC132_DUAL_BEFORE_FUTURE',return_value=original):
   plan=self.m._nova_inc050_future_quality('OWNER',{}, {},self.road(),{},evidence_ledger=self.ledger())
  self.assertIsNone(plan['workout_id']);self.assertNotIn('inc132_integrative',plan)

 def test_15_recommendation_always_exactly_one(self):
  with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub):
   c,why=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),None,self.road(),None,'OWNER')
   p={'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE', 'workout_id':'C3', 'inc132_integrative':c}
   d={'evidence_ledger':self.ledger(),'adaptive_roadmap':self.road(), 'ftp_anchor':None, 'metabolic_context':{}}
   self.assertTrue(self.m._inc132_validate_integrative(d,p,'OWNER'))
   a,r=self.m._inc132_priority(d,c,'OWNER')
   self.assertIn(a,('CARD2','CARD3'));self.assertTrue(r)
   d['evidence_ledger']['events'][0]['work_domain']='SPECIFIC'
   d['evidence_ledger']['events'][1]['work_domain']='SPECIFIC'
   # Priority never means a workout was scheduled or completed.
   a,r=self.m._inc132_priority(d,c,'OWNER')
   self.assertEqual(a,'CARD3')

 def test_16_wrong_owner_origin_receipt_rejected(self):
  with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub):
   c,_=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),None,self.road(),None,'OWNER')
   p={'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'C3','inc132_integrative':c, 'inc132_dual_schema':self.m.INC132_DUAL_SCHEMA}
   d={'evidence_ledger':self.ledger(),'adaptive_roadmap':self.road(),'ftp_anchor':None}
   self.assertFalse(self.m._inc132_validate_integrative(d,p,'SOMEONE_ELSE'))

 def test_17_demo_never_issues_unsealed_dual(self):
  self.assertIsNone(self.m._v4891_prepare_snapshot_for_ui(self.m.build_preview_data())['inc132_dual_quality'])

 def test_18_jinja_card2_3_valid_and_one_prioritized_border_source(self):
  self.m.app.jinja_env.parse(self.m.HOME_PAGE)
  self.assertEqual(self.m.HOME_PAGE.count('id="inc132-dual-quality-style"'),1)
  self.assertIn('dual.recommended_priority',self.m.HOME_PAGE)
  self.assertIn('loop.index == 2 and zi.complete',self.m.HOME_PAGE)
  self.assertIn('card3.verified_offer or card3.verified_future_plan',self.m.HOME_PAGE)

if __name__=='__main__':unittest.main(verbosity=2)

# Independent targeted additions, not overrides of legacy R153 regression tests.
def _inc132_added_test_19(self):
 with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub),\
      patch.object(self.m,'_INC132_DUAL_BEFORE_ATTEST',return_value=True):
  c,_=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),None,self.road(),None,'OWNER')
  p={'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'C3','inc132_integrative':c, 'inc132_dual_schema':self.m.INC132_DUAL_SCHEMA}
  d={'evidence_ledger':self.ledger(),'adaptive_roadmap':self.road(),
     'ftp_anchor':None,'metabolic_context':{},'future_quality_plan':p}
  self.assertTrue(self.m._nova_inc051_attest_future_snapshot(d,'OWNER'))
  self.assertIn('fueling',p['inc132_integrative'])
  self.assertEqual(p['inc132_integrative']['fueling']['workout_id'],c['workout_id'])
  self.assertEqual(p['inc132_recommended_priority'],'CARD3')
  self.assertFalse(p['inc132_integrative']['fueling']['execution_authorized'])

def _inc132_added_test_20(self):
 with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub),\
      patch.object(self.m,'_INC132_DUAL_BEFORE_ATTEST',return_value=True):
  c,_=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),None,self.road(),None,'OWNER')
  p={'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'C3','inc132_integrative':c, 'inc132_dual_schema':self.m.INC132_DUAL_SCHEMA}
  d={'evidence_ledger':self.ledger(),'adaptive_roadmap':self.road(),'ftp_anchor':None,
     'metabolic_context':{},'future_quality_plan':p,
     'nova_card3_workout_view':{'verified_future_plan':True,'workout_id':'C3','title':'Specific'},
     'quality_direction_fuel':{'workout_id':'C3'}}
  self.m._nova_inc051_attest_future_snapshot(d,'OWNER')
  with patch.object(self.m,'_INC132_DUAL_BEFORE_UI',side_effect=lambda x:x),\
       patch.object(self.m,'_nova_inc051_verified_owner_id',return_value='OWNER'),\
       patch.object(self.m,'_nova_inc091_eligible',return_value=True):
   out=self.m._v4891_prepare_snapshot_for_ui(d)
  dual=out['inc132_dual_quality'];self.assertIsNotNone(dual)
  self.assertEqual(dual['quality_integrative']['workout_id'],'P5_TEMPO_2X12')
  self.assertEqual(dual['quality_specific']['workout_id'],'C3')
  self.assertEqual(dual['recommended_priority'],'CARD3')
  self.assertFalse(dual['calendar_commitment'])

def _inc132_added_test_21(self):
 with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub),\
      patch.object(self.m,'_INC132_DUAL_BEFORE_ATTEST',return_value=True):
  c,_=self.m._inc132_build_integrative('POWER_5','SPECIFIC_DOSE',self.ledger(),None,self.road(),None,'OWNER')
  p={'goal_key':'POWER_5','dimension':'SPECIFIC_DOSE','workout_id':'C3','inc132_integrative':c, 'inc132_dual_schema':self.m.INC132_DUAL_SCHEMA}
  d={'evidence_ledger':self.ledger(),'adaptive_roadmap':self.road(),'ftp_anchor':None,
     'metabolic_context':{},'future_quality_plan':p}
  self.assertTrue(self.m._nova_inc051_attest_future_snapshot(d,'OWNER'))
  a=self.m._nova_inc051_plan_seal(p,'OWNER')
  self.assertIsInstance(a,str);self.assertEqual(len(a),64)
  p['authority_seal']=a
  self.assertEqual(self.m._nova_inc051_plan_seal(p,'OWNER'),a)
  p['inc132_integrative']['workout']['power_prescription']['high_watts']+=20
  self.assertNotEqual(self.m._nova_inc051_plan_seal(p,'OWNER'),a)

def _inc132_added_test_22(self):
 # UI path calls native raw truth replay in non-producer mode for viewing a
 # previously saved, owner-matched report; never relies on the browser stamp.
 ledger=self.ledger();band=self.band(ledger)
 flags=[]
 def capture(*args,**kwargs):
  flags.append(kwargs.get('producer_request',True))
  return self.truth_stub(*args,**kwargs)
 with patch.object(self.m,'_nova_inc091_truth',side_effect=capture):
  truth=self.m._inc132_tempo_server_truth(band,ledger,'OWNER',producer_request=False)
 self.assertIsNotNone(truth);self.assertEqual(flags,[False,False])

DualQualityQA.test_19_attested_fueling_and_single_priority=_inc132_added_test_19
DualQualityQA.test_20_attested_dual_view_contract=_inc132_added_test_20
DualQualityQA.test_21_original_hmac_seals_nested_integrative=_inc132_added_test_21
DualQualityQA.test_22_saved_report_owner_truth_recheck=_inc132_added_test_22

def _inc132_added_test_23(self):
    for val in (float('nan'),float('inf'),-float('inf')):
        for key in ('a_interval_secs','b_recovery_secs'):
            with self.subTest(value=str(val),field=key):
                self.assertIsNone(self.band(self.ledger(**{key:val})).get('tempo_proof_schema'))

def _inc132_added_test_24(self):
    l=self.ledger()
    # A conflicting second receipt with the same activity id invalidates that
    # activity entirely; it is NOT silently discarded as if harmless metadata.
    forged=copy.deepcopy(l['repeatability']['events'][0])
    forged['avg_watts']=228
    l['repeatability']['events'].append(forged)
    self.assertIsNone(self.band(l).get('tempo_proof_schema'))

def _inc132_added_test_25(self):
    l=self.ledger()
    # Two specific-family completed sessions with independent matching
    # repeat receipts and the real ledger field names (not fictitious labels).
    for name,day in [('specific-1','2026-11-05'),('specific-2','2026-11-04')]:
        repeated={'activity_id':name,'date':day,'strong':True,
          'reps':2,'interval_secs':300,'recovery_secs':180,
          'recovery_pair_count':1,'recovery_pair_expected':1,
          'recovery_observation_complete':True,
          'activity_truth_source':'DEVICE_LAPS','activity_truth_status':'RESOLVED'}
        l['repeatability']['events'].append(repeated)
        l['events'].append({'activity_id':name,'date':day,'event_kind':'TRAINING',
             'activity_truth_source':'DEVICE_LAPS','activity_truth_status':'RESOLVED',
             'family':'VO2max','quality_relevant':True,'repeatability':repeated})
    tempo={'goal_key':'POWER_5','evidence_ids':['verified-device-A','verified-device-B']}
    # Native server truth is intentionally mocked here; this is an owner-bound
    # unit test, not an authenticated live E2E claim.
    with patch.object(self.m,'_nova_inc091_truth',side_effect=self.truth_stub):
        recommended,reason=self.m._inc132_priority({'evidence_ledger':l},tempo,'OWNER')
        self.assertEqual(recommended,'CARD2')
        self.assertIn('TWO_DISTINCT_OWNER_VERIFIED',reason)
        l['events'].pop();l['repeatability']['events'].pop()
        self.assertEqual(self.m._inc132_priority({'evidence_ledger':l},tempo,'OWNER')[0],'CARD3')
        # Fully resolved Tempo activities can never inflate specific burden.
        l['events'].append(dict(l['events'][0],family='VO2max',quality_relevant=True))
        self.assertEqual(self.m._inc132_priority({'evidence_ledger':l},tempo,'OWNER')[0],'CARD3')


def _inc132_added_test_26(self):
    l=self.ledger()
    expected=self.band(l)
    for source in ['MANUAL','UNVERIFIED']:
        forged=copy.deepcopy(l)
        forged['events'][0]['activity_truth_source']=source
        self.assertIsNone(self.band(forged).get('tempo_proof_schema'))
    self.assertTrue(self.witness(l,expected)['accepted'])

DualQualityQA.test_23_rejects_nonfinite_protocol_durations=_inc132_added_test_23
DualQualityQA.test_24_conflicting_duplicate_receipt_fails_closed=_inc132_added_test_24
DualQualityQA.test_25_producer_prioritizes_two_verified_specific_not_tempo=_inc132_added_test_25
DualQualityQA.test_26_independent_event_sources_must_match=_inc132_added_test_26


def _inc132_added_test_27(self):
 for field in ('a_interval_secs','b_recovery_secs'):
  with self.subTest(field=field):
   band=self.band(self.ledger(**{field:10**10000}))
   self.assertIsNone(band.get('tempo_proof_schema'))

DualQualityQA.test_27_rejects_unbounded_seconds_without_crash=_inc132_added_test_27
