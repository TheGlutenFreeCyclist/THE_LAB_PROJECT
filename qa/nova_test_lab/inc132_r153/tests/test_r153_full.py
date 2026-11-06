#!/usr/bin/env python3
"""INC132 R153: executable deterministic QA, no production access or private data.

Runs original R150 science/issuer and R153 candidate methods from full monolith,
plus real Jinja render and optional Chromium responsive checks. Not authenticated
Flask or private raw-fixture replay; do not count as final product release gates.
"""
import ast
import hashlib
import math
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from qa_stub_import import load

ROOT=Path(__file__).resolve().parent
BASE=Path(os.getenv('INC132_R150',ROOT/'R150_BASELINE/the_lab_app.py'))
DTM=Path(os.getenv('INC132_DTM',ROOT/'DTM/NOVA_DOCUMENTO_TECNICO_MECCANICO_v1.0.75.md'))
CANDIDATE=Path(os.getenv('INC132_CANDIDATE',ROOT/'r153_candidate_test_only.py'))
EXPECTED_BASE='6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
EXPECTED_DTM='eda8ab935d66ef27c1b8fbf1fb298d1d78d3bafc9e32c0c6044128cd2d119304'
AS_OF='2026-11-06'

RECENT={'available':True,'status':'NO VALIDATED ANCHOR','prescription_watts':None,
 'current_rolling_ftp':274,'current_rolling_date':'2026-10-20','anchor_watts':None,'anchor_date':None}
OLD={'available':True,'status':'RETEST DUE','prescription_watts':None,
 'current_rolling_ftp':None,'current_rolling_date':None,'anchor_watts':266,'anchor_date':'2025-06-01'}
DUAL_SOURCE_SYNTH={'available':True,'status':'RETEST DUE','prescription_watts':None,
 'current_rolling_ftp':280,'current_rolling_date':'2026-11-02',
 'anchor_watts':265,'anchor_date':'2026-05-10'}
INVALID={'current_rolling_ftp':float('nan'),'current_rolling_date':'2026-10-20'}

class R153QA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=load(CANDIDATE)
  cls.tpl=next(x for x in cls.m._NOVA_WORKOUT_LIBRARY if x.get('id')=='P5_TEMPO_2X15')

 def test_01_immutable_inputs_and_compiled_full_monolith(self):
  self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),EXPECTED_BASE)
  self.assertEqual((DTM.read_text().strip() if DTM.suffix=='.sha256'
   else hashlib.sha256(DTM.read_bytes()).hexdigest()),EXPECTED_DTM)
  compile(CANDIDATE.read_text(encoding='utf-8'),str(CANDIDATE),'exec')
  self.assertIn('R196.9.153',self.m.APP_VERSION)
  self.assertGreater(len(self.m.app.view_functions),60)

 def test_02_science_issuer_and_auth_gate_AST_unchanged(self):
  r150=ast.parse(BASE.read_text(encoding='utf-8'))
  r153=ast.parse(CANDIDATE.read_text(encoding='utf-8'))
  for name in ('_nova_inc083_science_replay','_nova_inc056_plan_result',
               '_nova_r196956_build_offer','_nova_inc051_verified_owner_id',
               '_nova_inc075_valid_compiled_duration'):
   original=[ast.dump(n,include_attributes=False) for n in r150.body if isinstance(n,ast.FunctionDef) and n.name==name]
   candidate=[ast.dump(n,include_attributes=False) for n in r153.body if isinstance(n,ast.FunctionDef) and n.name==name]
   self.assertTrue(original,name)
   self.assertEqual(original,candidate,name)

 def test_03_recent_ftp_without_formal_test_remains_reference(self):
  ref=self.m._nova_power_coaching_reference(RECENT,AS_OF)
  self.assertEqual(ref['watts'],274)
  self.assertEqual(ref['origin'],'INTERVALS_ROLLING_FTP')
  self.assertFalse(ref['needs_check'])
  pub=self.m._inc132_r153_public_ftp(RECENT,AS_OF)
  self.assertEqual(pub['state'],'AVAILABLE')
  self.assertFalse(pub['verification_suggested'])
  self.assertEqual(pub['execution_clearance'],'SEPARATE')

 def test_04_523_day_old_reference_nonblocking_suggestion(self):
  ref=self.m._nova_power_coaching_reference(OLD,AS_OF)
  self.assertEqual(ref['watts'],266)
  self.assertEqual(ref['age_days'],523)
  self.assertTrue(ref['stale'])
  self.assertTrue(ref['needs_check'])
  pub=self.m._inc132_r153_public_ftp(OLD,AS_OF)
  self.assertTrue(pub['verification_suggested'])
  self.assertIn('when practical',self.m.ftp_anchor_text(OLD))

 def test_05_original_real_library_tempo_compiles_provisional_range(self):
  for f,lo,hi in ((RECENT,220,240),(OLD,215,235),(DUAL_SOURCE_SYNTH,225,245)):
   band=self.m._v1943_band(self.tpl,ftp_anchor=f,as_of_date=AS_OF,dimension='SPECIFIC_DOSE')
   self.assertEqual((band['low_watts'],band['high_watts']),(lo,hi))
   self.assertEqual(band['state'],'PRESCRIBED')
   self.assertEqual(band['power_target_mode'],'EXPLORATORY_RANGE')
   self.assertTrue(band['non_punitive'])
   self.assertIsNone(band['target_watts'])

 def test_06_science_issuer_rejects_unproven_numeric_dose(self):
  for f in (RECENT,OLD,DUAL_SOURCE_SYNTH):
   band=self.m._v1943_band(self.tpl,ftp_anchor=f,as_of_date=AS_OF,dimension='SPECIFIC_DOSE')
   proof=self.m._nova_inc083_science_replay(
     {'nova_workout_id':self.tpl['id'],'nova_prescription_dimension':'SPECIFIC_DOSE','power_prescription':band},
     {},f,{'scientific_progression':{'dimension':'SPECIFIC_DOSE'}},today=date(2026,11,6))
   self.assertIs(proof['accepted'],False)
   self.assertEqual(proof['reason'],'CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN')

 def test_07_invalid_nan_future_or_untrusted_reference_never_mints_watts(self):
  for f in (INVALID,{'anchor_watts':999999,'anchor_date':'2026-11-03'},
            {'current_rolling_ftp':250,'current_rolling_date':'2028-01-01'}):
   self.assertIsNone(self.m._nova_power_coaching_reference(f,AS_OF))
   band=self.m._v1943_band(self.tpl,ftp_anchor=f,as_of_date=AS_OF,dimension='SPECIFIC_DOSE')
   self.assertNotEqual(band['state'],'PRESCRIBED')
   self.assertIsNone(self.m._inc132_r153_public_ftp(f,AS_OF)['watts'])

 def test_08_hmac_owner_stamp_rejects_different_owner(self):
  m=self.m
  original_request=m.has_request_context
  original_owner=m._data_owner_user_id
  try:
   m.has_request_context=lambda:True
   m._data_owner_user_id=lambda *args,**kw:'owner-A'
   good=dict(RECENT,nova_inc132_owner_token=m._inc132_r153_scope_token('owner-A'))
   other=dict(RECENT,nova_inc132_owner_token=m._inc132_r153_scope_token('owner-B'))
   self.assertEqual(m._inc132_r153_public_ftp(good,AS_OF)['watts'],274)
   self.assertTrue(m._inc132_r153_public_ftp(good,AS_OF)['owner_attested'])
   self.assertIsNone(m._nova_power_coaching_reference(other,AS_OF))
   self.assertEqual(m._inc132_r153_public_ftp(other,AS_OF)['state'],'NOT_AVAILABLE')
  finally:
   m.has_request_context=original_request
   m._data_owner_user_id=original_owner

 def test_09_no_automatic_test_veto_in_public_text(self):
  for f in (RECENT,OLD,DUAL_SOURCE_SYNTH):
   s=self.m.ftp_anchor_text(f)
   self.assertNotIn('FTP_EXPLORATORY',s)
   self.assertNotIn('NO_VALIDATED_ANCHOR',s)
   self.assertNotIn('RETEST DUE',s)
   self.assertNotIn('REFRESH DUE',s)
   self.assertIn('not proof',s)

 def test_10_full_jinja_and_card3_template_contract(self):
  m=self.m
  m.app.jinja_env.parse(m.HOME_PAGE)
  self.assertEqual(m.HOME_PAGE.count('class="v4825-ftp-anchor inc132-ftp-panel"'),1)
  self.assertEqual(m.HOME_PAGE.count('id="inc132-card3-mirror-style"'),1)
  self.assertNotIn('nova-card3-grey-placeholder',m.HOME_PAGE)
  self.assertEqual(m.HOME_PAGE.count('class="r1969102-canonical-copy r1969104-single-workout"'),1)
  self.assertIn('Same canonical workout as Card',m.HOME_PAGE)

 def test_11_actual_snapshot_UI_sidecar_from_demo_source(self):
  m=self.m
  data=m._v4891_prepare_snapshot_for_ui(m.build_preview_data())
  self.assertIn('nova_inc132_ftp_reference',data)
  self.assertEqual(data['nova_inc132_ftp_reference']['execution_clearance'],'SEPARATE')
  self.assertNotIn('raw_ftp_exploratory',data)

 def test_12_card3_demo_is_present_but_not_certified(self):
  m=self.m
  data=m._v4891_prepare_snapshot_for_ui(m.build_preview_data())
  m.request.endpoint='preview'
  kwargs=dict(days=m.DAYS_BACK,season_days=m.SEASON_DAYS_BACK,data=data,error=None,
    css=m.BASE_CSS,logo=m.LOGO_B64,brand_wordmark=m.BRAND_WORDMARK_B64,favicon=m.FAVICON_B64,
    notes=[],chat_answer=None,chat_error=None,feelings=[],latest_feeling=None,
    app_version=m.APP_VERSION,clock_preview=m.get_clock_preview(),
    is_preview=True,report_mode=False,report_meta=None,download_mode=False,
    latest_report_meta=None,chat_context_meta=None)
  kwargs.update(m.inject_v10_memory_context())
  html=m.app.jinja_env.from_string(m.HOME_PAGE).render(**kwargs)
  from html.parser import HTMLParser
  class CardProbe(HTMLParser):
   def __init__(self):super().__init__();self.card3=0;self.canonical=0
   def handle_starttag(self,tag,attrs):
    if tag != 'article' and tag != 'div':return
    a=dict(attrs);classes=(a.get('class') or '').split()
    self.card3+=int('v1962-quality-card' in classes)
    self.canonical+=int('r1969104-single-workout' in classes)
  probe=CardProbe();probe.feed(html)
  self.assertEqual(probe.card3,1,'Card3 is an actual rendered card, not just a template string')
  self.assertIn('QUALITY STRUCTURE ONLY',html)
  self.assertEqual(probe.canonical,0,'Demo has no verified personal dose; do not claim issuer clearance')

 def test_13_source_tamper_prevention(self):
  from build_r153_candidate import build
  r152=ROOT/'build_r152_bi_candidate.py'
  adapter=ROOT/'inc132_card3_mirror.py'
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'baseline.py';a.write_bytes(BASE.read_bytes()+b'\n# tampered\n')
   with self.assertRaisesRegex(ValueError,'R150_SOURCE_SHA_MISMATCH'):
    build(a,DTM,adapter,r152,Path(td)/'out.py')

if __name__=='__main__':unittest.main(verbosity=2)
