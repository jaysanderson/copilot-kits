"""Tiny JSON-document store on SQLite. Holds review state and operational metadata (PRD s7);
the knowledge itself is indexed in Progress Agentic RAG, not here."""
import json
import sqlite3
import threading
import time
import uuid

from .config import DB_PATH

_lock = threading.RLock()
_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row
TABLES = ("sites", "pages", "mentions", "relations", "entities", "conflicts", "ambiguities",
          "suggestions", "runs", "decisions")
for t in TABLES:
    _db.execute(f"CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY, site_id TEXT, data TEXT NOT NULL)")
    _db.execute(f"CREATE INDEX IF NOT EXISTS ix_{t}_site ON {t}(site_id)")
_db.commit()


def new_id():
    return uuid.uuid4().hex[:12]


def put(table, id_, site_id, obj):
    with _lock:
        _db.execute(f"INSERT OR REPLACE INTO {table}(id, site_id, data) VALUES (?,?,?)",
                    (id_, site_id, json.dumps(obj, default=str)))
        _db.commit()


def get(table, id_):
    with _lock:
        r = _db.execute(f"SELECT data FROM {table} WHERE id=?", (id_,)).fetchone()
    return json.loads(r["data"]) if r else None


def all_(table, site_id):
    with _lock:
        rows = _db.execute(f"SELECT data FROM {table} WHERE site_id=?", (site_id,)).fetchall()
    return [json.loads(r["data"]) for r in rows]


def clear(table, site_id):
    with _lock:
        _db.execute(f"DELETE FROM {table} WHERE site_id=?", (site_id,))
        _db.commit()


def delete(table, id_):
    with _lock:
        _db.execute(f"DELETE FROM {table} WHERE id=?", (id_,))
        _db.commit()


def update(table, id_, **fields):
    with _lock:
        cur = get(table, id_)
        if cur is None:
            return None
        cur.update(fields)
        r = _db.execute(f"SELECT site_id FROM {table} WHERE id=?", (id_,)).fetchone()
        put(table, id_, r["site_id"], cur)
        return cur


def now():
    return time.time()
