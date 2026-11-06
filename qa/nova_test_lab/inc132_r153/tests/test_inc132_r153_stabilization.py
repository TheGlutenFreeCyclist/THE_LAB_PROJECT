"""INC132 R153: owner and persisted FTP RED→GREEN tests, synthetic only."""
import os
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from qa_stub_import import load

ROOT = Path(__file__).resolve().parent
CANDIDATE = Path(os.environ.get('INC132_CANDIDATE', ROOT.parent / 'source/the_lab_app_R153_GO_WORK.py'))
RECENT = {'available': True, 'status': 'RETEST DUE', 'current_rolling_ftp': 274,
          'current_rolling_date': '2026-10-20', 'anchor_watts': None, 'anchor_date': None}

class StabilizationQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load(CANDIDATE)

    @contextmanager
    def context(self, owner='owner-A', request=False):
        m = self.mod
        memory = {}
        changes = []
        names = ('_persist_interval_metric_points', '_stored_interval_metric_points',
                 '_persist_ftp_anchor_events', '_data_owner_user_id', 'has_request_context')
        originals = {k: getattr(m, k) for k in names}
        def persist(metric, points, source, user_id=None):
            assert user_id is not None
            for day, value in points:
                memory[(str(user_id), str(metric), str(day))] = (value, source)
                changes.append((str(user_id), metric, day, value))
            return len(points)
        def stored(metric, user_id=None):
            return [{'date': day, 'value': val, 'source': source}
                    for (u, key, day), (val, source) in sorted(memory.items())
                    if key == metric and u == str(user_id)]
        def owner_resolve(user_id=None):
            return str(user_id) if user_id is not None else owner
        try:
            m._persist_interval_metric_points = persist
            m._stored_interval_metric_points = stored
            m._persist_ftp_anchor_events = lambda *args, **kw: 0
            m._data_owner_user_id = owner_resolve
            m.has_request_context = lambda: request
            yield memory, changes
        finally:
            for key, val in originals.items():
                setattr(m, key, val)

    def now(self):
        return datetime(2026, 11, 6, tzinfo=self.mod.ROME_TZ)

    def test_01_signed_owner_background_same_owner_succeeds(self):
        m = self.mod
        with self.context(request=False):
            signed = dict(RECENT, nova_inc132_owner_token=m._inc132_r153_scope_token('owner-A'))
            self.assertTrue(m._inc132_r153_owner_ok(signed, expected_owner_id='owner-A'))
            self.assertIsNone(m._nova_power_coaching_reference(signed, '2026-11-06'))
            self.assertEqual(m._nova_power_coaching_reference(signed, '2026-11-06',
                expected_owner_id='owner-A')['watts'], 274)
            public = m._inc132_r153_public_ftp(signed, '2026-11-06', expected_owner_id='owner-A')
            self.assertEqual(public['watts'], 274)
            self.assertTrue(public['owner_attested'])
            self.assertEqual(public['execution_clearance'], 'SEPARATE')

    def test_02_signed_owner_background_cross_owner_fails(self):
        m = self.mod
        with self.context(request=False):
            signed = dict(RECENT, nova_inc132_owner_token=m._inc132_r153_scope_token('owner-B'))
            self.assertIsNone(m._nova_power_coaching_reference(signed, '2026-11-06',
                expected_owner_id='owner-A'))
            self.assertIsNone(m._inc132_r153_public_ftp(signed, '2026-11-06',
                expected_owner_id='owner-A')['watts'])

    def test_03_authenticated_request_cross_owner_explicit_parameter_fails(self):
        m = self.mod
        with self.context(request=True, owner='owner-A'):
            signed = dict(RECENT, nova_inc132_owner_token=m._inc132_r153_scope_token('owner-B'))
            self.assertIsNone(m._nova_power_coaching_reference(signed, '2026-11-06',
                expected_owner_id='owner-B'))
            self.assertIsNone(m._inc132_r153_public_ftp(signed, '2026-11-06',
                expected_owner_id='owner-B')['watts'])
            with self.assertRaisesRegex(PermissionError, 'OWNER_MISMATCH'):
                m.build_ftp_anchor_context([{'start_date_local': '2026-10-20',
                    'icu_rolling_ftp': 274}], now=self.now(), user_id='owner-B')

    def test_04_rolling_reference_persists_past_fetch_horizon(self):
        m = self.mod
        with self.context(request=False) as (memory, writes):
            hist = [{'id':'a-old', 'start_date_local':'2025-06-01', 'icu_rolling_ftp':266}]
            before = m.build_ftp_anchor_context(hist, now=self.now(), user_id='owner-A')
            after = m.build_ftp_anchor_context([], now=self.now(), user_id='owner-A')
            self.assertEqual(before['current_rolling_ftp'], 266)
            self.assertEqual(after['current_rolling_ftp'], 266)
            self.assertEqual(after['current_rolling_date'], '2025-06-01')
            self.assertEqual(m._inc132_r153_public_ftp(after, '2026-11-06',
                expected_owner_id='owner-A')['watts'], 266)
            self.assertTrue(after['nova_inc132_rolling_history_persisted'])
            self.assertEqual(len(writes), 1, 'No new write on empty fetch')

    def test_05_new_observation_rotates_without_erasing_history(self):
        m = self.mod
        with self.context() as (memory, writes):
            a = [{'id':'early', 'start_date_local':'2025-06-01', 'icu_rolling_ftp':266}]
            b = [{'id':'fresh', 'start_date_local':'2026-11-01', 'icu_rolling_ftp':275}]
            m.build_ftp_anchor_context(a, now=self.now(), user_id='owner-A')
            new = m.build_ftp_anchor_context(b, now=self.now(), user_id='owner-A')
            self.assertEqual((new['current_rolling_ftp'],new['current_rolling_date']), (275,'2026-11-01'))
            self.assertEqual(len(memory), 2)
            self.assertEqual(m.build_ftp_anchor_context([], now=self.now(),
                user_id='owner-A')['current_rolling_ftp'], 275)

    def test_06_cross_owner_storage_isolation(self):
        m = self.mod
        with self.context(request=False) as (memory, writes):
            a = [{'id':'a', 'start_date_local':'2026-10-22','icu_rolling_ftp':281}]
            b = [{'id':'b', 'start_date_local':'2026-10-20','icu_rolling_ftp':211}]
            m.build_ftp_anchor_context(a, now=self.now(),user_id='owner-A')
            m.build_ftp_anchor_context(b, now=self.now(),user_id='owner-B')
            ctx_a = m.build_ftp_anchor_context([], now=self.now(),user_id='owner-A')
            ctx_b = m.build_ftp_anchor_context([], now=self.now(),user_id='owner-B')
            self.assertEqual(ctx_a['current_rolling_ftp'],281)
            self.assertEqual(ctx_b['current_rolling_ftp'],211)
            self.assertIsNone(m._inc132_r153_public_ftp(ctx_b,'2026-11-06',
                expected_owner_id='owner-A')['watts'])

    def test_07_invalid_future_nan_and_collision_ordering(self):
        m=self.mod
        with self.context() as (memory, writes):
            rows=[{'id':'z','start_date_local':'2026-10-20T07:00:00','icu_rolling_ftp':200},
                  {'id':'a','start_date_local':'2026-10-20T09:00:00','icu_rolling_ftp':253},
                  {'id':'bad','start_date_local':'2026-10-21','icu_rolling_ftp':float('nan')},
                  {'id':'future','start_date_local':'2027-10-21','icu_rolling_ftp':999},
                  {'id':'outlier','start_date_local':'2026-10-19','icu_rolling_ftp':99999}]
            x=m.build_ftp_anchor_context(rows,now=self.now(),user_id='owner-A')
            y=m.build_ftp_anchor_context(list(reversed(rows)),now=self.now(),user_id='owner-A')
            self.assertEqual(x['current_rolling_ftp'],253)
            self.assertEqual(y['current_rolling_ftp'],253)
            self.assertEqual(len(memory),1)
            self.assertEqual(len(writes),2)

    def test_08_missing_source_remains_missing(self):
        m=self.mod
        with self.context():
            empty=m.build_ftp_anchor_context([],now=self.now(),user_id='owner-A')
            self.assertEqual(m._inc132_r153_public_ftp(empty,'2026-11-06',
                expected_owner_id='owner-A')['state'],'NOT_AVAILABLE')
            self.assertIsNone(m._nova_power_coaching_reference(empty, '2026-11-06',
                expected_owner_id='owner-A'))

    def test_09_sqlite_real_sql_roundtrip_and_owner_separation(self):
        # Not a mock of the persistence writer: exercise its real SQL against
        # the same existing metric_history table shape in a temporary DB.
        import sqlite3
        import tempfile
        from unittest.mock import patch
        m = self.mod
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'qa.sqlite'
            conn = sqlite3.connect(path)
            conn.execute('''CREATE TABLE intervals_metric_history (
                user_id TEXT NOT NULL, metric_key TEXT NOT NULL,
                metric_date TEXT NOT NULL, value REAL NOT NULL,
                source TEXT NOT NULL, created_at_utc TEXT, updated_at_utc TEXT,
                PRIMARY KEY(user_id,metric_key,metric_date))''')
            conn.commit(); conn.close()
            def connect():
                c = sqlite3.connect(path)
                c.row_factory = sqlite3.Row
                return c
            with patch.object(m,'init_memory_db', lambda: None), \
                 patch.object(m,'_db_connect', connect), \
                 patch.object(m,'_db_is_postgres',lambda:False), \
                 patch.object(m,'_db_sql',lambda sql:sql), \
                 patch.object(m,'_persist_ftp_anchor_events',lambda *a,**kw:0), \
                 patch.object(m,'has_request_context',lambda:False):
                a=m.build_ftp_anchor_context([{'id':'old','start_date_local':'2025-06-01',
                      'icu_rolling_ftp':266}],now=self.now(),user_id='owner-A')
                self.assertEqual(a['current_rolling_ftp'],266)
                b=m.build_ftp_anchor_context([],now=self.now(),user_id='owner-A')
                self.assertEqual(b['current_rolling_ftp'],266)
                c=m.build_ftp_anchor_context([],now=self.now(),user_id='owner-B')
                self.assertIsNone(c['current_rolling_ftp'])
                conn=connect()
                count=conn.execute('SELECT COUNT(*) FROM intervals_metric_history').fetchone()[0]
                conn.close()
                self.assertEqual(count,1)

    def test_10_all_current_tempo_ftp_bands_remain_nonissuable_without_repeat_proof(self):
        # A good pacing reference and a complete scientific HARD dose are
        # different contracts. This catches any future fake-positive test.
        from datetime import date
        m = self.mod
        seen=[]
        for tpl in m._NOVA_WORKOUT_LIBRARY:
            if str(tpl.get('work_domain') or '').upper()!='TEMPO_Z3':
                continue
            dimension=tpl['dimensions'][0]
            band=m._v1943_band(tpl,evidence_ledger={},ftp_anchor=RECENT,
                               as_of_date='2026-11-06',dimension=dimension)
            witness=m._nova_inc083_science_replay({
                'nova_workout_id':tpl['id'],
                'nova_prescription_dimension':dimension,
                'power_prescription':band}, {}, RECENT,
                {'scientific_progression':{'dimension':dimension}},
                today=date(2026,11,6))
            seen.append((tpl['id'], band.get('state'), witness.get('accepted')))
            self.assertEqual(band.get('state'),'PRESCRIBED')
            self.assertFalse(witness.get('accepted'))
            self.assertEqual(witness.get('reason'),
                             'CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN')
        self.assertEqual(len(seen),7)

    def test_11_failed_secondary_storage_does_not_crash_source_snapshot(self):
        m=self.mod
        from unittest.mock import patch
        with self.context():
            with patch.object(m,'_persist_interval_metric_points',
                              side_effect=OSError('synthetic STORAGE_UNAVAILABLE')):
                result=m.build_ftp_anchor_context([
                    {'id':'fresh','start_date_local':'2026-10-20','icu_rolling_ftp':274}],
                    now=self.now(),user_id='owner-A')
                self.assertEqual(result['current_rolling_ftp'],274)
                self.assertEqual(result['nova_inc132_rolling_persistence_state'],
                                 'WRITE_FAILED')

    def test_12_persisted_value_survives_future_dated_current_fetch(self):
        m=self.mod
        with self.context() as (memory,writes):
            m.build_ftp_anchor_context([{'id':'real', 'start_date_local':'2026-10-20',
               'icu_rolling_ftp':274}],now=self.now(),user_id='owner-A')
            future=m.build_ftp_anchor_context([{'id':'future',
                'start_date_local':'2027-03-20', 'icu_rolling_ftp':333}],
                now=self.now(),user_id='owner-A')
            self.assertEqual(future['current_rolling_ftp'],274)
            self.assertEqual(future['current_rolling_date'],'2026-10-20')

if __name__ == '__main__':
    unittest.main(verbosity=2)
