"""Public, non-sensitive Card 3 release gate.

Usage (from repository root): python qa/INC051_release_gate.py
Private beta end-to-end offline suite: python qa/INC051_release_gate.py --full
The full option REQUIRES the private fixture locally and NEVER uploads it.
This is not a replacement for a real authenticated staging/Android E2E gate.
"""
from pathlib import Path
import runpy,json,copy,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
app=ROOT/'the_lab_app.py'
assert app.is_file(),'Missing the_lab_app.py'
compile(app.read_bytes(),str(app),'exec')
m=runpy.run_path(str(ROOT/'qa/_load_fix.py'))['mod']
checks=[]
def check(name,ok):
    checks.append({'name':name,'pass':bool(ok)})
    if not ok:print('FAIL',name)
check('runtime_release_family','R196.9.106' in m.APP_VERSION)
check('single_workout_panel',m.HOME_PAGE.count('r1969104-single-workout')==1)
check('no_duplicate_explainer','YOUR WORKOUT EXPLAINED' not in m.HOME_PAGE and 'qdetail.main_set|e' not in m.HOME_PAGE)
check('valid_final_jinja',bool(m.app.jinja_env.parse(m.HOME_PAGE)))
check('clear_empty_direction',m._nova_r196975_quality_direction({'goal_key':'POWER_20','action':'TRAIN'},{}).get('referenced_canonical_template_id') is None)
check('no_template_without_current_science',m._nova_r1969104_canonical_card3({'nova_decision':{'action':'TRAIN','goal_key':'POWER_20'}}).get('workout_id') is None)
check('no_unsanctioned_fueling',m._nova_inc051_fuel_for_canonical_card3({'coach_clock':{'rhythm':{'recent':{'median_duration_min':45}}}},{'verified_offer':False,'verified_future_plan':False}) is None)
check('owner_needed_offline',m._nova_inc051_verified_owner_id() is None)
context={'nova_decision':{'action':'TRAIN','goal_key':'POWER_20'},
 'coach_clock':{'next_slots':[{'duration_hint_min':48.4,'source':'RHYTHM'}]},
 'adaptive_roadmap':{'goal_key':'POWER_20','quality_window':{'state':'WATCH','preferred_iso':'2026-11-03','headline':'old'},'scientific_progression':{'dimension':'TIME_AT_PRESSURE'}},
 'training_state':{'state':'WATCH','why':'old'}}
d=m._nova_inc051_context_digest(context)
changed=copy.deepcopy(context);changed['adaptive_roadmap']['quality_window']['headline']='new UI wording';changed['training_state']['why']='new UI wording'
check('pure_display_reword_not_invalidate',d==m._nova_inc051_context_digest(changed))
changed=copy.deepcopy(context);changed['coach_clock']['next_slots'][0]['duration_hint_min']=75
check('actual_slot_duration_invalidates',d!=m._nova_inc051_context_digest(changed))
changed=copy.deepcopy(context);changed['nova_decision']['goal_key']='POWER_5'
check('scientific_goal_invalidates',d!=m._nova_inc051_context_digest(changed))
changed=copy.deepcopy(context);changed['training_state']['state']='RECOVERY HOLD'
check('recovery_state_invalidates',d!=m._nova_inc051_context_digest(changed))
plan={'schema':m.INC050_SCHEMA,'workout_id':'FAKE_TEST_ONLY','owner_scope':m._nova_inc050_owner_scope('A'),
      'status':'CONDITIONAL_NOT_CLEARED','compiled_workout_digest':'test'}
a=m._nova_inc051_plan_seal(plan,'A')
check('seal_deterministic',bool(a and a==m._nova_inc051_plan_seal(plan,'A')))
check('different_owner_different_seal',a!=m._nova_inc051_plan_seal(plan,'B'))
plan['workout_id']='tampered'
check('modified_workout_invalidates',a!=m._nova_inc051_plan_seal(plan,'A'))
check('uncompiled_plan_cannot_be_sealed_into_snapshot',not m._nova_inc051_attest_future_snapshot({'future_quality_plan':copy.deepcopy(plan),'future_quality_owner_scope':m._nova_inc050_owner_scope('A')},'A'))
DTM=ROOT/'qa/CARD3_CONTRACT_051.md'
if DTM.is_file():
  dtm=DTM.read_text()
  check('normative_dtm_inc051','Card 3: source-of-truth' in dtm and 'future_conditional' in dtm and 'required' in dtm)
else:
  check('normative_dtm_inc051',False)
report={'scope':'public smoke without private user fixture or actual Flask/DB',
 'checks':len(checks),'passed':sum(c['pass'] for c in checks),
 'failed':sum(not c['pass'] for c in checks),'results':checks}
(ROOT/'qa/INC051_public_gate_report.json').write_text(json.dumps(report,indent=2))
print('INC051 PUBLIC CONTRACT GATE',report['passed'],'/',report['checks'])
if report['failed']:sys.exit(1)
if '--full' in sys.argv:
  private=ROOT/'evidenze/the_lab_beta_qa_880de0cbd6ee_20261031_1435.md'
  if not private.is_file():
    raise SystemExit('NO-GO FULL GATE: private beta regression fixture unavailable locally; NEVER upload to public GitHub')
  for name in ('INC049_contract_proof.py','INC049_acceptance.py','INC049_multiathlete_future.py',
               'INC050_acceptance.py','INC050_future_matrix.py','INC051_firewall_acceptance.py'):
    print('RUN',name,flush=True)
    subprocess.run([sys.executable,str(ROOT/'qa'/name)],cwd=ROOT,check=True)
  print('INC051 FULL OFFLINE CONTRACT GATE PASS (NOT Flask/auth/DB/Android staging)')
