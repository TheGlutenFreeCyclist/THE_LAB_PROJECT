# R196.9.99 Neon egress fix (not deployed)

Apply the two exact substitutions below to `the_lab_app.py`. Keep the branch isolated until QA is complete.

## 1. Select metadata projection without large JSON

Find:

```python
    rows = _data_execute(owner_id,
        "SELECT singleton_id, user_id, generated_at_utc, generated_at_local, app_version, payload_json FROM latest_report WHERE user_id=? LIMIT 1",
        (owner_id,), fetch=True,
    )
```

Replace:

```python
    needs_payload = bool(include_payload or include_qa_replay)
    if needs_payload:
        projection = "singleton_id, user_id, generated_at_utc, generated_at_local, app_version, payload_json"
    else:
        length_expr = ("OCTET_LENGTH(payload_json)"
                       if (_owner_personal_data_enabled(owner_id) or _db_is_postgres())
                       else "LENGTH(CAST(payload_json AS BLOB))")
        projection = ("singleton_id, user_id, generated_at_utc, generated_at_local, app_version, "
                      f"COALESCE({length_expr}, 2) AS payload_bytes")
    rows = _data_execute(owner_id,
        f"SELECT {projection} FROM latest_report WHERE user_id=? LIMIT 1",
        (owner_id,), fetch=True,
    )
```

## 2. Preserve payload behavior and QA replay

Find:

```python
    raw = row.get("payload_json") or "{}"
    meta["payload_bytes"] = len(raw.encode("utf-8"))
    meta["payload_human"] = _human_bytes(meta["payload_bytes"])
    if include_payload or include_qa_replay:
```

Replace:

```python
    if needs_payload:
        raw = row.get("payload_json") or "{}"
        meta["payload_bytes"] = len(raw.encode("utf-8"))
    else:
        meta["payload_bytes"] = int(row.get("payload_bytes") or 0)
    meta["payload_human"] = _human_bytes(meta["payload_bytes"])
    if needs_payload:
```

Do not modify full Snapshot reads. Verify SQLite, Product Postgres and bridged Personal Neon routing, and QA replay.

The exact standalone .patch file is supplied separately in the conversation.
