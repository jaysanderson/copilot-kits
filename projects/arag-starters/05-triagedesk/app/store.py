"""SQLite-backed store for submitted verdicts - powers the officer
dashboard/queue and detail views.

Persists across app restarts via a Fly volume mounted at this same path
(`data/`, see fly.toml's [mounts] and the deploy notes in README) - a real
functional requirement once the demo's own narrative is about audit trail /
Back Office handoff, not just a nice-to-have (a machine restart on Fly's
ephemeral filesystem was silently wiping the previous JSON-file store between
sessions; SQLite alone does not fix that without the volume, both are
required together). `seed/seed.py --purge` remains the intentional 30-second
reset - this is about NOT losing data to an unrelated machine restart, not
about making the demo un-resettable.
"""
import json
import os
import sqlite3
import threading

_LOCK = threading.Lock()
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "submissions.db")


def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id TEXT PRIMARY KEY,
            generated_at TEXT NOT NULL,
            verdict_json TEXT NOT NULL
        )
    """)
    return conn


def load_all() -> list[dict]:
    with _LOCK:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT verdict_json FROM submissions ORDER BY generated_at DESC"
            ).fetchall()
        finally:
            conn.close()
    return [json.loads(r[0]) for r in rows]


def save(verdict: dict) -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO submissions (submission_id, generated_at, verdict_json) "
                "VALUES (?, ?, ?)",
                (verdict["RequestId"], verdict["ProcessingDateTime"],
                 json.dumps(verdict, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()


def get(request_id: str) -> dict | None:
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT verdict_json FROM submissions WHERE submission_id = ?",
                (request_id,),
            ).fetchone()
        finally:
            conn.close()
    return json.loads(row[0]) if row else None


def purge() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.execute("DELETE FROM submissions")
            conn.commit()
        finally:
            conn.close()
