"""R146 synthetic regression: no credentials or live owner payloads."""
import ast
import datetime
import hashlib
import random
from pathlib import Path
from zoneinfo import ZoneInfo
from jinja2 import Environment

TARGET = 'f9ad64dc7770ed3ad21b165e0b7bcdf1645da4d6db5bf772385396d92023142c'
raw = Path('the_lab_app.py').read_bytes()
assert hashlib.sha256(raw).hexdigest() == TARGET
root = ast.parse(raw.decode('utf-8'))

def fn(name):
    matches = [node for node in root.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert matches, name
    return matches[-1]

ns = {'date': datetime.date, 'datetime': datetime.datetime,
      'ROME_TZ': ZoneInfo('Europe/Rome'),
      'R145_INTENT_OBSERVATION_SCHEMA': 'NOVA-R196.9.145-INTENT-OBSERVATION-1',
      '_NOVA_WORKOUT_LIBRARY': ({'id': 'P5_5X3_EASYREC', 'goal': 'POWER_5',
                                  'pattern': 'STANDARD', 'reps': 5,
                                  'work_s': 180, 'recovery_s': 300},),
      'get_rome_now': lambda: datetime.datetime(2026, 11, 4, 19, 50,
                                                tzinfo=ZoneInfo('Europe/Rome'))}
for name in ('_v139_parse_local_dt', '_v139_activity_dt', '_r142_slot_daypart',
             '_r145_quality_intent_observation'):
    exec(compile(ast.Module(body=[fn(name)], type_ignores=[]), 'R145-source', 'exec'), ns)

intent = {'kind': 'PLAN', 'scope': 'ONCE', 'daypart': 'EVENING',
          'local_date': '2026-11-04', 'workout_id': 'P5_5X3_EASYREC',
          'goal_key': 'POWER_5', 'minutes': 73,
          'saved_at_utc': '2026-11-04T16:00:34Z'}
rep = {'activity_truth_status': 'RESOLVED',
       'activity_truth_source': 'ICU_INTERVALS_CANONICAL',
       'reps': 5, 'interval_secs': 180, 'recovery_secs': 300}
block = {'date': '2026-11-04', 'time': '05:20 PM',
         'activity_id': 'synthetic-activity', 'event_kind': 'TRAINING',
         'duration_min': 73, 'repeatability': rep}
ns['_r142_intents'] = lambda owner: [dict(intent)]
check = ns['_r145_quality_intent_observation']
match = check('synthetic-owner', [block])
assert match['state'] == 'OBSERVED_AFTER_SAVED_AVAILABILITY', match
assert match['observed_duration_min'] == 73 and match['observed_local_time'] == '17:20'
assert match['observed_reps'] == 5 and match['observed_interval_seconds'] == 180
assert match['observational_only'] and match['not_a_nova_prescription']
assert match['execution_authorized'] is False and match['adherence_created'] is False
print('PASS matching 73-min observed quality; NO retrospective clearance')

# Actual CA normalization: block.repeatability.source has canonical provenance,
# while latest_activity_feedback carries VERIFIED for the SAME activity.
real_block = {**block, 'quality_relevant': True,
              'repeatability': {'source': 'ICU_INTERVALS_CANONICAL',
                                'reps': 5, 'interval_secs': 180,
                                'recovery_secs': 300}}
attested = {'activity_id': 'synthetic-activity', 'structure_status': 'VERIFIED'}
reconciled = check('synthetic-owner', [real_block], latest_feedback=attested)
assert reconciled['state'] == 'OBSERVED_AFTER_SAVED_AVAILABILITY', reconciled
assert reconciled['observed_duration_min'] == 73
assert check('synthetic-owner', [real_block])['state'] == 'NO_VERIFIED_OBSERVED_MATCH'
assert check('synthetic-owner', [real_block], latest_feedback={**attested, 'activity_id': 'different-id'})['state'] == 'NO_VERIFIED_OBSERVED_MATCH'
assert check('synthetic-owner', [real_block], latest_feedback={**attested, 'structure_status': 'UNVERIFIED'})['state'] == 'NO_VERIFIED_OBSERVED_MATCH'
assert check('synthetic-owner', [{**real_block, 'quality_relevant': False}], latest_feedback=attested)['state'] == 'NO_VERIFIED_OBSERVED_MATCH'
print('PASS real CA-shaped canonical observation + exact attestation, four false-link guards')

cases = [
    {'time': '04:50 PM'}, {'date': '2026-11-03'},
    {'time': '04:20 PM'}, {'activity_id': ''},
    {'duration_min': 74}, {'duration_min': 'broken'},
    {'repeatability': {**rep, 'reps': 4}},
    {'repeatability': {**rep, 'reps': 'bad'}},
    {'repeatability': {**rep, 'interval_secs': 240}},
    {'repeatability': {**rep, 'recovery_secs': 240}},
    {'repeatability': {**rep, 'activity_truth_status': 'UNVERIFIED'}},
    {'repeatability': {**rep, 'activity_truth_source': 'AUTO_INFERRED'}},
    {'repeatability': []}, {'event_kind': 'RACE'},
]
for variant in cases:
    result = check('synthetic-owner', [{**block, **variant}])
    assert result['state'] == 'NO_VERIFIED_OBSERVED_MATCH', variant
print('PASS', len(cases), 'strict mismatch cases')

for change in ({'minutes': 60}, {'daypart': 'AFTERNOON'},
               {'saved_at_utc': '2026-11-04T17:00:34Z'}, {'goal_key': 'SPRINTER'}):
    ns['_r142_intents'] = lambda owner, change=change: [{**intent, **change}]
    assert check('synthetic-owner', [block])['state'] == 'NO_VERIFIED_OBSERVED_MATCH'
ns['_r142_intents'] = lambda owner: [dict(intent)]
assert check('', [block])['state'] == 'NO_RECENT_INTENT'
ns['_r142_intents'] = lambda owner: (_ for _ in ()).throw(RuntimeError('test unavailable'))
assert check('synthetic-owner', [block])['state'] == 'INTENT_READ_UNAVAILABLE'
ns['_r142_intents'] = lambda owner: [dict(intent)]
print('PASS scope, timing, goal, declared minutes, read-fault boundaries')

random.seed(125)
for _ in range(3000):
    variant = {**block, 'duration_min': random.randint(20,100),
               'repeatability': {**rep, 'reps': random.randint(2,8),
                                 'interval_secs': random.choice([60,120,180,240,300]),
                                 'recovery_secs': random.choice([120,180,240,300,360])}}
    result = check('synthetic-owner', [variant])
    assert result['execution_authorized'] is False and result['adherence_created'] is False
    if result['state'] == 'OBSERVED_AFTER_SAVED_AVAILABILITY':
        assert variant['duration_min'] <= 73.5
        assert variant['repeatability']['reps'] == 5
        assert variant['repeatability']['interval_secs'] == 180
        assert variant['repeatability']['recovery_secs'] == 300
print('PASS 3000 synthetic activity/availability fuzz cases')

panel_nodes = [n for n in root.body if isinstance(n, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == '_R143_PANEL' for t in n.targets)]
assert len(panel_nodes) == 1
panel = ast.literal_eval(panel_nodes[0].value)
env = Environment(autoescape=True)
env.parse(panel)
html = env.from_string(panel).render(data={
    'quality_intent_reconciliation': match,
    'nova_r142_plan_ui': {'workout_id': 'P5_5X3_EASYREC',
                          'required_minutes': 73, 'learned_minutes': 60.5, 'card': 3}},
    nova_r142_state={'active': True, 'workout_id': 'P5_5X3_EASYREC', 'token': 'synthetic'},
    is_preview=False, qa_mode=False, download_mode=False,
    url_for=lambda name: '/mock/' + name, csrf_token=lambda: 'synthetic')
assert 'Your 73.0 min quality was recorded on 2026-11-04 at 17:20' in html
assert 'not Nova execution clearance' in html
assert '📅' in html
print('PASS rendered Jinja notice and calendar')
print('R146 synthetic LAB PASS')
