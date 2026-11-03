"""INC105 auth contract: genuine Flask login + signed sessions on ephemeral SQLite.

Staging SECRET_KEY, two fabricated admin accounts, zero network/production DB.
No monkeypatch of login, current_user, require_login or auth HMAC functions.
This proves the isolated auth/session boundary, not a deployed signed issuer E2E.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

for k in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
          "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
          "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
          "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[k] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"

import the_lab_app as nova  # noqa: E402

LAB_SECRET = "INC105-only-synthetic-staging-key-not-for-any-deployment-2026"
PASSWORD = "local-lab-password-only-not-a-real-credential"


class Inc105RealAuthSqlite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nova-inc105-auth-")
        self.previous = (nova.SQLITE_PATH, nova._DB_READY, nova.SECRET_KEY,
                         nova.app.secret_key, nova.DATABASE_URL)
        nova.SQLITE_PATH = os.path.join(self.tmp.name, "isolated.sqlite")
        nova.DATABASE_URL = ""
        nova._DB_READY = False
        nova.SECRET_KEY = LAB_SECRET
        nova.app.secret_key = LAB_SECRET
        nova.init_memory_db()
        for user_id, username in (("lab-alpha", "inc105alpha"),
                                  ("lab-beta", "inc105beta")):
            nova._db_execute(
                "INSERT INTO users (id,username,username_key,password_hash,role,status,"
                "created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?,?,?)",
                (user_id, username, username, nova.generate_password_hash(PASSWORD),
                 "admin", "active", "2026-11-03T00:00:00Z", "2026-11-03T00:00:00Z"),
            )

    def tearDown(self):
        (nova.SQLITE_PATH, nova._DB_READY, nova.SECRET_KEY,
         nova.app.secret_key, nova.DATABASE_URL) = self.previous
        self.tmp.cleanup()

    def login(self, username):
        c = nova.app.test_client()
        r = c.post("/login", data={"username": username, "password": PASSWORD},
                   follow_redirects=False)
        self.assertIn(r.status_code, (302, 303), "Real /login failed")
        auth = c.get("/session/csrf")
        self.assertEqual(auth.status_code, 200, "Real session was not accepted")
        self.assertTrue(auth.get_json()["ok"])
        return c

    def test_real_login_persists_hmac_and_signed_cookie(self):
        c = self.login("inc105alpha")
        with c.session_transaction() as s:
            self.assertEqual(s["user_id"], "lab-alpha")
            raw = s["auth_token"]
        self.assertNotIn(PASSWORD, raw)
        saved = nova._db_execute(
            "SELECT user_id,token_hash FROM auth_sessions WHERE user_id=?",
            ("lab-alpha",), fetch=True)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["token_hash"], nova._security_hmac(raw))
        self.assertNotEqual(saved[0]["token_hash"], raw)

    def test_owner_swap_rejected_and_revoked_session_rejected(self):
        alpha = self.login("inc105alpha")
        beta = self.login("inc105beta")
        with alpha.session_transaction() as a:
            stolen = a["auth_token"]
        with beta.session_transaction() as b:
            b["auth_token"] = stolen  # valid Flask-signed cookie, WRONG owner binding
        self.assertEqual(beta.get("/session/csrf").status_code, 401)
        self.assertEqual(alpha.get("/session/csrf").status_code, 200)
        nova._db_execute("UPDATE auth_sessions SET revoked_at_utc=? WHERE user_id=?",
                         (nova._now_utc_text(), "lab-alpha"))
        self.assertEqual(alpha.get("/session/csrf").status_code, 401)

    def test_bad_password_does_not_issue_session(self):
        client = nova.app.test_client()
        r = client.post("/login", data={"username":"inc105alpha",
                                        "password":"synthetic-wrong-passphrase"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(client.get("/session/csrf").status_code, 401)
        self.assertFalse(nova._db_execute(
            "SELECT id FROM auth_sessions WHERE user_id=?",
            ("lab-alpha",), fetch=True))

    def test_future_quality_hmac_owner_and_dose_binding(self):
        plan = {"schema": "INC105-SYNTHETIC-ONLY", "workout_id": "P5_5X3_EASYREC",
                "power_prescription": {"low_watts": 350, "high_watts": 370},
                "status":"CONDITIONAL_NOT_CLEARED"}
        signed = nova._nova_inc051_plan_seal(plan, "lab-alpha")
        self.assertEqual(len(signed), 64)
        self.assertEqual(signed, nova._nova_inc051_plan_seal(plan, "lab-alpha"))
        self.assertNotEqual(signed, nova._nova_inc051_plan_seal(plan, "lab-beta"))
        changed = {**plan, "power_prescription":{"low_watts":350,"high_watts":385}}
        self.assertNotEqual(signed, nova._nova_inc051_plan_seal(changed, "lab-alpha"))
        # This signs an INC051 synthetic plan, NOT an end-to-end issuer release.


if __name__ == "__main__":
    unittest.main(verbosity=2)
