"""INC-051: real Flask sessions + isolated SQLite, synthetic users only.

No network, no athlete data, no production database. A required part of the
staging gate, not a substitute for production-equivalent Neon and Android E2E.
"""
import json
import os
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

with tempfile.TemporaryDirectory(prefix="inc051-auth-") as tmp:
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("THE_LAB_OWNER_DATABASE_URL", None)
    os.environ["THE_LAB_SQLITE_PATH"] = str(Path(tmp) / "card3_test.sqlite3")
    os.environ["SECRET_KEY"] = "inc051-ci-only-isolated-synthetic-secret-123456"
    os.environ["PRODUCT_SECURITY_STRICT"] = "0"
    os.environ["SESSION_COOKIE_SECURE"] = "0"

    import the_lab_app as m
    from flask import jsonify

    m.app.config.update(TESTING=True)
    m.init_memory_db()
    password = "synthetic-integration-only-password-123"
    now = m._now_utc_text()
    for suffix in ("A", "B"):
        uid = "inc051-synthetic-" + suffix
        username = "inc051_qa_" + suffix.lower()
        m._db_execute(
            "INSERT INTO users (id, username, username_key, password_hash, role, status, birth_date, created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, username, username, m.generate_password_hash(password), "athlete", "active", "1990-01-01", now, now))
        m._db_execute(
            "INSERT INTO licenses (id, user_id, license_type, status, created_at_utc) VALUES (?, ?, ?, ?, ?)",
            ("license-" + suffix, uid, "BETA", "active", now))
        m._db_execute(
            "INSERT INTO latest_report (singleton_id, user_id, generated_at_utc, generated_at_local, app_version, payload_json) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, uid, now, now, "INC051 SYNTHETIC QA", json.dumps({"owner_tag": suffix})))

    @m.app.route("/__inc051_test_session")
    def _inc051_test_session():
        user = m.current_user(touch=False)
        if not user:
            return jsonify({"ok": False}), 401
        owner = m._nova_inc051_verified_owner_id()
        report = m.load_latest_report(include_payload=True)
        fake = {"nova_decision": {"action": "TRAIN", "goal_key": "POWER_20"},
                "future_quality_plan": {"workout_id": "UNSIGNED_FAKE",
                    "status": "CONDITIONAL_NOT_CLEARED"}}
        card = m._nova_r1969104_canonical_card3(fake)
        return jsonify({"ok": True, "owner": owner,
            "tag": (report.get("data") or {}).get("owner_tag"),
            "unsanctioned_rejected": not bool(card.get("verified_future_plan"))
                                   and not bool(card.get("workout_id"))})

    a = m.app.test_client()
    b = m.app.test_client()
    assert a.get("/session/csrf").status_code == 401, "Anonymous CSRF access"
    assert a.get("/__inc051_test_session").status_code == 401, "Anonymous owner access"
    assert a.get("/login").status_code == 200, "Login page unavailable"

    for client, suffix in ((a, "A"), (b, "B")):
        assert client.get("/login").status_code == 200
        with client.session_transaction() as sess:
            csrf_token = sess.get("csrf_token")
        assert csrf_token, "Missing login CSRF token"
        response = client.post("/login", data={
            "username": "inc051_qa_" + suffix.lower(), "password": password,
            "csrf_token": csrf_token})
        assert response.status_code in (302, 303), (suffix, response.status_code)
        assert client.get("/session/csrf").status_code == 200
        state = client.get("/__inc051_test_session")
        assert state.status_code == 200, (suffix, state.status_code)
        payload = state.get_json()
        assert payload["owner"] == "inc051-synthetic-" + suffix, payload
        assert payload["tag"] == suffix, payload
        assert payload["unsanctioned_rejected"], payload

    assert a.get("/__inc051_test_session").get_json()["tag"] == "A"
    assert b.get("/__inc051_test_session").get_json()["tag"] == "B"
    logout = a.get("/logout")
    assert logout.status_code in (302, 303)
    assert a.get("/__inc051_test_session").status_code == 401
    assert b.get("/__inc051_test_session").get_json()["tag"] == "B"
    print("INC051 FLASK AUTH + SQLITE TWO-OWNER SMOKE: PASS")
