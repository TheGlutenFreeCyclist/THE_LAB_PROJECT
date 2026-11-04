"""R196.9.143: UI-only refactor + R142 training/storing regression tests.

CI runs on the exact, SHA256-verified producer. External IO disabled by workflow.
"""
from __future__ import annotations
import copy
import hashlib
import json
import random
import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import the_lab_app as n

TARGET_SHA='7fa531e1439816d112054e3cba9fbc1bf27ccecf4d56141c28326db65529f3fb'
NOW=datetime(2026,11,4,15,0,tzinfo=n.ROME_TZ)
WORKOUT='P5_5X3_EASYREC'

def intent(kind='PLAN',scope='ONCE',minutes=75,day='2026-11-04',part='EVENING'):
    return {'schema':n.R142_AVAILABILITY_SCHEMA,'kind':kind,'scope':scope,
            'workout_id':WORKOUT,'goal_key':'POWER_5','minutes':minutes,
            'local_date':day if scope=='ONCE' else None,
            'daypart':part if scope=='ONCE' else None,
            'saved_at_utc':'2026-11-04T13:00:00Z'}

def ui(card=3,active=True,feedback=None,latest=None,usual=None,preview=False):
    d={'nova_r142_plan_ui':{'workout_id':WORKOUT,'card':card,
                            'required_minutes':73.0,'learned_minutes':60.5}}
    state={'active':active,'workout_id':WORKOUT,'token':'1'*64,
           'feedback':feedback,'latest_intent':latest,'usual_limit':usual}
    return n.app.jinja_env.from_string(n._R143_PANEL).render(
        data=d,nova_r142_state=state,is_preview=preview,qa_mode=False,
        download_mode=False,today_iso='2026-11-04',
        csrf_token=lambda:'fixture-csrf',
        url_for=lambda name:'/quality/intent/clear-usual' if 'clear' in name else '/quality/intent')

class R143UIAndR142Training(unittest.TestCase):
    def test_00_committed_byte_identity_and_parse(self):
        self.assertEqual(hashlib.sha256(Path(n.__file__).read_bytes()).hexdigest(), TARGET_SHA)
        self.assertIn('R196.9.143',n.APP_VERSION)
        n.app.jinja_env.parse(n.HOME_PAGE)

    def test_01_single_compact_entry_in_both_possible_slots(self):
        self.assertEqual(n.HOME_PAGE.count('class="r143-open-dialog"'),2)
        self.assertEqual(n.HOME_PAGE.count('id="r143-quality-dialog"'),2)
        self.assertEqual(n.HOME_PAGE.count('nova-card3-grey-placeholder'),1)
        self.assertEqual(n.HOME_PAGE.count('class="r142-quality-planning"'),0)
        self.assertEqual(n.HOME_PAGE.count('r142-quality-actions'),0)
        self.assertEqual(n.HOME_PAGE.count('function syncMode()'),1)

    def test_02_render_one_button_two_routes_and_csrf(self):
        html=ui()
        self.assertEqual(html.count('data-r143-open'),1)
        self.assertEqual(html.count('<dialog'),1)
        self.assertEqual(html.count('method="post"'),2)
        self.assertEqual(html.count('name="csrf_token"'),2)
        self.assertEqual(html.count('name="offer_binding"'),2)
        self.assertIn('name="intent_kind" value="PLAN"',html)
        self.assertIn('name="intent_kind" value="TOO_LONG"',html)
        self.assertIn('name="scope" value="ONCE"',html)
        self.assertIn('value="2026-11-04"',html)
        self.assertIn('<option value="EVENING" selected>',html)
        self.assertEqual(html.count('Why easy endurance today?'),0)
        self.assertNotIn('r142-quality-reason',html)
        self.assertIn('not permission to perform a hard session',html)

    def test_03_grey_card_keeps_single_external_entry(self):
        for index in (1,2):
            html=ui(card=index)
            self.assertEqual(html.count('data-r143-open'),1)
            self.assertIn(f'already displayed in Card {index}',html)
            self.assertIn('Card 3 remains inactive',html)

    def test_04_hidden_on_preview_and_missing_binding(self):
        self.assertEqual(ui(preview=True).strip(),'')
        self.assertEqual(ui(active=False).strip(),'')

    def test_05_status_saved_and_revoke_action_in_dialog_only(self):
        html=ui(feedback='Availability saved.',latest=intent(),usual=intent('TOO_LONG','USUAL',60))
        self.assertIn('Availability saved.',html)
        self.assertIn('action="/quality/intent/clear-usual"',html)
        self.assertEqual(html.count('name="csrf_token"'),3)
        self.assertIn('Remove my usual duration limit',html)
        self.assertNotIn('Latest request: ',html)

    def test_06_native_dialog_closable_and_accessible(self):
        s=n._R143_SCRIPT
        self.assertIn('showModal()',s)
        self.assertIn("dlg.addEventListener('close'",s)
        self.assertIn('open.focus()',s)
        self.assertIn('syncScope()',s)
        self.assertIn('querySelectorAll(\'input,select,button\')',s)
        self.assertIn('aria-haspopup="dialog"',n._R143_PANEL)
        self.assertIn('aria-labelledby="r143-dialog-title"',n._R143_PANEL)
        self.assertIn('r143-quality-dialog::backdrop',n._R143_STYLE)
        self.assertIn('@media(max-width:620px)',n._R143_STYLE)

    def test_07_old_easy_card_reasons_preserved(self):
        self.assertIn('Why easy endurance today?',n.HOME_PAGE)
        self.assertEqual(n.HOME_PAGE.count('r142-quality-card-reason'),1)
        self.assertIn('Open Card 3 · plan your next quality',n.HOME_PAGE)
        self.assertIn('not is_quality_slot and s',n.HOME_PAGE)

    def test_08_original_canonical_template_preserved(self):
        w=n._R19696_LIBRARY_INDEX[WORKOUT]
        self.assertEqual(n._nova_quality_template_required_seconds(w,'DURABILITY')/60,73)
        self.assertEqual(n._nova_quality_template_required_seconds(w,'REPEATABILITY')/60,55)

    def test_09_once_intent_never_expands_two_slots(self):
        clock={'next_slots':[{'date':'2026-11-04','start_minute':18*60,'duration_hint_min':60.5,'restriction':'NONE'},
                             {'date':'2026-11-04','start_minute':19*60,'duration_hint_min':60.5,'restriction':'NONE'},
                             {'date':'2026-11-05','start_minute':18*60,'duration_hint_min':60.5,'restriction':'NONE'}]}
        original=copy.deepcopy(clock)
        out=n._r142_adjust_slots(clock,[intent()],NOW)
        self.assertEqual([e['duration_hint_min'] for e in out['next_slots']],[75.,60.5,60.5])
        self.assertFalse(out['r142_availability_intent_audit']['issued_quality_by_intent'])
        self.assertTrue(out['r142_availability_intent_audit']['rhythm_learning_unchanged'])
        self.assertEqual(clock,original)

    def test_10_usual_limits_never_override_restrictions_or_calendar(self):
        clock={'next_slots':[{'date':'2026-11-04','start_minute':18*60,'duration_hint_min':75,'restriction':'NONE'},
                             {'date':'2026-11-04','start_minute':19*60,'duration_hint_min':60,'restriction':'NO_INTENSITY'},
                             {'date':'2026-11-05','start_minute':18*60,'duration_hint_min':100,'restriction':'NONE','is_planned_training':True}]}
        out=n._r142_adjust_slots(clock,[intent('TOO_LONG','USUAL',55)],NOW)
        self.assertEqual([s['duration_hint_min'] for s in out['next_slots']],[55.,60.,100.])

    def test_11_no_health_read_or_new_scientific_selector(self):
        code=Path(n.__file__).read_text()
        extension=code.split('# INC123 / R196.9.143')[1]
        self.assertNotIn('build_training_rhythm(',extension)
        self.assertNotIn('build_coach_clock(',extension)
        self.assertNotIn('build_nova_prescription(',extension)
        self.assertNotIn('get(\'nova_health\')',extension)
        self.assertNotIn('execution_authorized=',extension)

    def test_12_25k_seeded_fuzzed_slot_evaluations(self):
        rng=random.Random(143123)
        clock={'next_slots':[{'date':f'2026-11-{day:02d}','start_minute':hr*60,
                              'duration_hint_min':60.5,'restriction':'NONE' if day!=7 else 'NO_INTENSITY'}
                              for day in range(4,12) for hr in (7,12,18)]}
        baseline=copy.deepcopy(clock)
        for idx in range(25000):
            day=f'2026-11-{4+idx%8:02d}'
            part=('MORNING','AFTERNOON','EVENING')[idx%3]
            rule=intent(kind='TOO_LONG' if idx%3 else 'PLAN',
                        scope='USUAL' if idx%6==0 else 'ONCE',
                        minutes=rng.randint(15,360),day=day,part=part)
            out=n._r142_adjust_slots(clock,[rule],NOW)
            self.assertEqual(clock,baseline)
            self.assertFalse(out['r142_availability_intent_audit']['issued_quality_by_intent'])
            self.assertEqual(len(out['next_slots']),len(clock['next_slots']))
            self.assertFalse(any(s.get('execution_authorized') for s in out['next_slots']))
            self.assertTrue(all(s['duration_hint_min']==60.5 for s in out['next_slots'] if s['restriction']=='NO_INTENSITY'))
            if rule['scope']=='ONCE':
                self.assertLessEqual(len(out['r142_availability_intent_audit']['slots_adjusted']),1)

    def test_13_15k_sqlite_writes_across_100_users(self):
        conn=sqlite3.connect(':memory:')
        conn.row_factory=sqlite3.Row
        conn.execute('CREATE TABLE planning_items(id TEXT PRIMARY KEY,user_id TEXT,created_at_utc TEXT,kind TEXT,title TEXT,note TEXT,start_date TEXT,end_date TEXT,restriction_type TEXT,active INTEGER)')
        def db(owner,sql,params=(),fetch=False):
            cur=conn.execute(sql,params)
            if fetch:return [dict(x) for x in cur.fetchall()]
            conn.commit()
            return []
        try:
            with (patch.object(n,'_data_execute',side_effect=db),
                  patch.object(n,'_owner_personal_data_enabled',return_value=False)):
                for i in range(15000):
                    owner=f'user-{i%100:03d}'
                    obj=intent('TOO_LONG','USUAL',15+i%345) if i%2 else intent('PLAN','ONCE',15+i%345)
                    n._r142_write_intent(owner,obj)
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM planning_items').fetchone()[0],100)
                self.assertEqual(conn.execute('SELECT COUNT(DISTINCT user_id) FROM planning_items').fetchone()[0],100)
                for i in range(100):
                    self.assertEqual(len(n._r142_intents(f'user-{i:03d}')),1)
                self.assertEqual(n._r142_intents('user-unrelated'),[])
        finally:
            conn.close()

    def test_14_real_flask_POST_plan_once_and_too_long_usual(self):
        if not hasattr(n.app,'test_request_context'):
            self.skipTest('Local Flask stub; real Flask POST executed in GitHub Actions')
        report={'generated_at_utc':'2026-11-04T12:00:00Z','data':{
            'nova_decision':{'goal_key':'POWER_5'},
            'nova_card3_workout_view':{'workout_id':WORKOUT}}}
        with patch.object(n,'_v4891_prepare_snapshot_for_ui',side_effect=lambda d:d):
            token=n._r142_report_binding(report,'owner')
        saved=[]
        with (patch.object(n,'require_login',return_value=True),
              patch.object(n,'load_latest_report',return_value=report),
              patch.object(n,'get_active_training_strategy_plan',return_value={'primary_goal':'POWER_5'}),
              patch.object(n,'_v4891_prepare_snapshot_for_ui',side_effect=lambda d:d),
              patch.object(n,'_R142_PLANNING_ITEMS_BEFORE',return_value=[]),
              patch.object(n,'_r142_write_intent',side_effect=lambda owner,obj:saved.append(obj)),
              patch.object(n,'get_rome_now',return_value=NOW)):
            scenarios=[{'intent_kind':'PLAN','scope':'ONCE','minutes':'75','local_date':'2026-11-04','daypart':'EVENING'},
                       {'intent_kind':'TOO_LONG','scope':'USUAL','minutes':'60'}]
            for form in scenarios:
                form['offer_binding']=token['token']
                with n.app.test_request_context('/quality/intent',method='POST',data=form):
                    n.session['user_id']='owner'
                    response=n.r142_quality_intent()
                    self.assertEqual(response.status_code,303)
                    self.assertIn('/last-report',response.location)
            self.assertEqual([x['kind'] for x in saved],['PLAN','TOO_LONG'])
            self.assertEqual(saved[0]['daypart'],'EVENING')
            self.assertEqual(saved[0]['local_date'],'2026-11-04')
            self.assertEqual(saved[1]['scope'],'USUAL')
            self.assertIsNone(saved[1]['local_date'])
            self.assertTrue(all(x['not_an_execution_authorization'] for x in saved))

if __name__=='__main__':
    import time
    start=time.monotonic()
    result=unittest.main(verbosity=2,exit=False).result
    print('R143_QA_VERDICT',json.dumps({'tests':result.testsRun,'failures':len(result.failures),
          'errors':len(result.errors),'duration_s':round(time.monotonic()-start,2)},sort_keys=True))
    if not result.wasSuccessful():raise SystemExit(1)
