import copy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from qa_stub_import import load

app = load(Path(__file__).resolve().parents[4] / 'the_lab_app.py')
date = '2026-11-07'
now = datetime.fromisoformat(date + 'T20:00:00+01:00')
cases = [(0, 0, True), (0, 1, True), (-10, -10, True), (10, 10, True),
         (-11, 0, False), (11, 0, False), (0, -11, False), (0, 11, False)]
for pattern in ('STANDARD', 'SUSTAINED'):
    wid, template = next((k, v) for k, v in app._R19696_LIBRARY_INDEX.items()
                         if v.get('pattern') == pattern and v.get('reps', 0) > 1
                         and v.get('work_s', 0) > 10 and v.get('recovery_s', 0) > 10)
    intent = dict(kind='PLAN', scope='ONCE', local_date=date, saved_at_utc=date+'T17:00:00+01:00',
                  workout_id=wid, goal_key=template['goal'], minutes=90, daypart='EVENING')
    source = 'ICU_INTERVALS_CANONICAL'
    with patch.object(app, '_r142_intents', return_value=[intent]):
        for dw, dr, expected in cases:
            block = dict(quality_relevant=True, activity_id='QA1', date=date, time='18:00', duration_min=60,
                         activity_truth=dict(status='RESOLVED', source=source),
                         repeatability=dict(source=source, reps=template['reps'],
                                            interval_secs=template['work_s']+dw,
                                            recovery_secs=template['recovery_s']+dr))
            result = app._r145_quality_intent_observation('OWNER', [block], now)
            assert (result['state'] == 'OBSERVED_AFTER_SAVED_AVAILABILITY') == expected, result
            assert result['execution_authorized'] is False and result['adherence_created'] is False
            print(pattern, dw, dr, result['state'], 'PASS')
print('16/16 PASS')
