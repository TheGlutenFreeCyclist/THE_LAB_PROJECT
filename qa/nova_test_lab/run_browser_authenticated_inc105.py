"""INC105 actual Chromium cookie/auth report-path integration in isolated staging.

Real browser -> localhost Flask -> actual /login + CSRF -> DB-backed
auth_sessions token HMAC -> /last-report. The report data itself is synthetic
and read from real owner-scoped SQLite using an explicitly SEEDED synthetic\nreport row (not the producer save path). Real production/Neon credentials and
the actual issuer chain are not used. No personal screenshots or logs.
"""
import contextlib
import io
import json
import os
import tempfile
import threading
import sys
from pathlib import Path
from unittest.mock import patch

for key in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
            "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import the_lab_app as nova
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

TEST_SECRET = "synthetic-inc105-key-used-only-in-ephemeral-lab-sqlite-2026"
TEST_PASSWORD = "INC105-local-test-credential-only"


def run():
    old = (nova.SQLITE_PATH, nova._DB_READY, nova.DATABASE_URL,
           nova.SECRET_KEY, nova.app.secret_key)
    server = None
    thread = None
    with tempfile.TemporaryDirectory(prefix="nova-inc105-browser-") as directory:
        try:
            nova.SQLITE_PATH = os.path.join(directory, "browser-auth.sqlite")
            nova._DB_READY = False
            nova.DATABASE_URL = ""
            nova.SECRET_KEY = TEST_SECRET
            nova.app.secret_key = TEST_SECRET
            nova.init_memory_db()
            now = nova._now_utc_text()
            nova._db_execute(
                "INSERT INTO users (id,username,username_key,password_hash,role,status,"
                "created_at_utc,updated_at_utc) VALUES (?,?,?,?,?,?,?,?)",
                ("inc105-browser-admin", "inc105browser", "inc105browser",
                 nova.generate_password_hash(TEST_PASSWORD), "admin", "active",
                 now, now))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                data = nova.build_preview_data()
            # INC106 upgrades the prior mocked report read into the genuine
            # owner-scoped load_latest_report() SQL path. Only seed is synthetic.
            payload = json.dumps(data,ensure_ascii=False,
                                 default=nova._report_json_default)
            nova._db_execute(
                "INSERT INTO latest_report (singleton_id,user_id,generated_at_utc,"
                "generated_at_local,app_version,payload_json) VALUES (?,?,?,?,?,?)",
                ("inc105-browser-admin","inc105-browser-admin",now,
                 "2026-11-03T09:00:00+01:00","INC106 SYNTHETIC STAGING",payload))
            with patch.object(nova,"get_clock_preview",return_value={}):
                server = make_server("127.0.0.1",0,nova.app,threaded=True)
                thread = threading.Thread(target=server.serve_forever,daemon=True)
                thread.start()
                root = "http://127.0.0.1:" + str(server.server_port)
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
                    try:
                        ctx = browser.new_context(
                            viewport={"width":390,"height":850},
                            reduced_motion="reduce",device_scale_factor=1)
                        ctx.route("**/*",lambda route:
                            route.continue_() if route.request.url.startswith(root)
                            else route.abort())
                        page=ctx.new_page()
                        page.goto(root+"/login",wait_until="domcontentloaded")
                        csrf=page.locator('input[name="csrf_token"]').input_value()
                        if not csrf:
                            raise AssertionError("missing_csrf")
                        r=ctx.request.post(root+"/login",form={
                            "username":"inc105browser","password":TEST_PASSWORD,
                            "csrf_token":csrf},max_redirects=0)
                        if r.status not in (302,303):
                            raise AssertionError("real_login_failed")
                        authenticated=ctx.request.get(root+"/session/csrf")
                        if authenticated.status != 200:
                            raise AssertionError("db_hmac_session_failed")
                        saved=ctx.request.get(root+"/last-report")
                        if saved.status != 200:
                            raise AssertionError("authenticated_saved_report_not_rendered")
                        page.goto(root+"/last-report",wait_until="domcontentloaded")
                        if page.locator(".v1962-quality-card").count() != 1:
                            raise AssertionError("card3_dom_missing")
                        # A different browser context has NO session and cannot read report.
                        unauth=browser.new_context()
                        try:
                            denied=unauth.request.get(root+"/last-report",max_redirects=0)
                            if denied.status not in (302,303,401,403):
                                raise AssertionError("anonymous_saved_report_allowed")
                        finally:
                            unauth.close()
                        # Cookie rejection after revocation: real DB and auth.
                        nova._db_execute("UPDATE auth_sessions SET revoked_at_utc=? WHERE user_id=?",
                                         (nova._now_utc_text(),"inc105-browser-admin"))
                        revoked=ctx.request.get(root+"/session/csrf")
                        if revoked.status != 401:
                            raise AssertionError("revoked_browser_session_still_valid")
                    finally:
                        browser.close()
            print(json.dumps({"suite":"INC105_BROWSER_AUTH","status":"PASS",
                              "real_flask_cookie":True,"real_csrf":True,
                              "db_backed_hmac":True,"revocation":True,
                              "real_owner_scoped_sql_load":True,"synthetic_report_payload":True,\n                              "real_issuer_hmac":False,
                              "production_secrets":False},sort_keys=True))
            return 0
        except Exception as exc:
            print(json.dumps({"suite":"INC105_BROWSER_AUTH","status":"FAIL",
                              "error_class":type(exc).__name__},sort_keys=True))
            return 1
        finally:
            if server is not None:
                server.shutdown()
            if thread is not None:
                thread.join(timeout=3)
            (nova.SQLITE_PATH,nova._DB_READY,nova.DATABASE_URL,
             nova.SECRET_KEY,nova.app.secret_key)=old


if __name__=="__main__":
    raise SystemExit(run())
