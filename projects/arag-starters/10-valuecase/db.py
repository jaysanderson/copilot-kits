"""SQLite persistence for the ROI & Value Case tool.

Every case a value engineer builds is a persistent, reopenable object -
this is the structural fix for the GM's "demo page, not a day-to-day tool"
finding (work item 0be7b846). The database file lives on a Fly volume
(see fly.toml) so it survives redeploys and restarts; the app runs on a
single machine (--ha=false at deploy) so there is exactly one writer.

No ARAG data lives here - this is case metadata and the buyer's own
numbers, never a Knowledge Box, never an API key.
"""
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("ROI_DB_PATH", str(os.path.dirname(__file__)) + "/data/roi_cases.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    seller_name TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'discovery',
    discount_rate REAL,
    horizon_months INTEGER NOT NULL DEFAULT 24,
    pricing_tier TEXT NOT NULL DEFAULT 'starter',
    custom_monthly_cost REAL,
    one_time_cost REAL,
    discovery_json TEXT NOT NULL DEFAULT '{}',
    selected_levers TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lever_input_values (
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    lever_id TEXT NOT NULL,
    input_key TEXT NOT NULL,
    scenario TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (case_id, lever_id, input_key, scenario)
);

CREATE TABLE IF NOT EXISTS lever_input_meta (
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    lever_id TEXT NOT NULL,
    input_key TEXT NOT NULL,
    measure_in_pov INTEGER NOT NULL DEFAULT 0,
    provided_by_name TEXT,
    provided_by_role TEXT,
    provided_at TEXT,
    source_type TEXT,
    PRIMARY KEY (case_id, lever_id, input_key)
);

CREATE TABLE IF NOT EXISTS lever_owners (
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    lever_id TEXT NOT NULL,
    owner_name TEXT,
    owner_role TEXT,
    PRIMARY KEY (case_id, lever_id)
);
"""


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_conn():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_case_id():
    return secrets.token_urlsafe(8).replace("_", "").replace("-", "")[:10]


# ---------------------------------------------------------------- cases

def create_case(account_name: str, seller_name: str) -> str:
    case_id = new_case_id()
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cases (id, account_name, seller_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (case_id, account_name, seller_name, ts, ts),
        )
    return case_id


def list_cases():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, account_name, seller_name, stage, updated_at, created_at FROM cases ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_case(case_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return None
        case = dict(row)
        values = conn.execute(
            "SELECT lever_id, input_key, scenario, value FROM lever_input_values WHERE case_id = ?", (case_id,)
        ).fetchall()
        meta = conn.execute(
            "SELECT lever_id, input_key, measure_in_pov, provided_by_name, provided_by_role, provided_at, source_type "
            "FROM lever_input_meta WHERE case_id = ?",
            (case_id,),
        ).fetchall()
        owners = conn.execute(
            "SELECT lever_id, owner_name, owner_role FROM lever_owners WHERE case_id = ?", (case_id,)
        ).fetchall()
        case["values"] = [dict(r) for r in values]
        case["meta"] = [dict(r) for r in meta]
        case["owners"] = [dict(r) for r in owners]
        return case


def delete_case(case_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))


def update_case_fields(case_id: str, fields: dict):
    if not fields:
        return
    allowed = {
        "account_name", "seller_name", "stage", "discount_rate", "horizon_months",
        "pricing_tier", "custom_monthly_cost", "one_time_cost", "discovery_json", "selected_levers",
    }
    cols = [k for k in fields if k in allowed]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols) + ", updated_at = ?"
    values = [fields[c] for c in cols] + [now_iso(), case_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE cases SET {set_clause} WHERE id = ?", values)


def upsert_input_partial(case_id: str, lever_id: str, input_key: str, values: dict, meta: dict):
    """PARTIAL update - `values` and `meta` carry ONLY the keys the caller
    actually wants to change (e.g. `values={"expected": 400}` alone from one
    field's blur). Anything omitted is left exactly as already stored.

    This replaces the old upsert_input, which always wrote all three
    scenario columns and the whole meta row on every call - fine as long as
    the caller's snapshot was current, but demo-tester (22 Sep 2026) proved
    it silently NULLED genuinely-saved values whenever the caller's local
    state had gone stale (e.g. after navigating away and back without a
    fresh fetch). A partial write cannot suffer that failure mode: a value
    this call never mentions is a value this call cannot touch."""
    with get_conn() as conn:
        for scenario, v in values.items():
            if scenario not in ("conservative", "expected", "aggressive"):
                continue
            conn.execute(
                "INSERT INTO lever_input_values (case_id, lever_id, input_key, scenario, value) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(case_id, lever_id, input_key, scenario) DO UPDATE SET value = excluded.value",
                (case_id, lever_id, input_key, scenario, v),
            )
        if meta:
            existing = conn.execute(
                "SELECT measure_in_pov, provided_by_name, provided_by_role, provided_at, source_type "
                "FROM lever_input_meta WHERE case_id = ? AND lever_id = ? AND input_key = ?",
                (case_id, lever_id, input_key),
            ).fetchone()
            merged = dict(existing) if existing else {
                "measure_in_pov": 0, "provided_by_name": None, "provided_by_role": None,
                "provided_at": None, "source_type": None,
            }
            merged.update(meta)
            conn.execute(
                "INSERT INTO lever_input_meta (case_id, lever_id, input_key, measure_in_pov, provided_by_name, "
                "provided_by_role, provided_at, source_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(case_id, lever_id, input_key) DO UPDATE SET "
                "measure_in_pov = excluded.measure_in_pov, provided_by_name = excluded.provided_by_name, "
                "provided_by_role = excluded.provided_by_role, provided_at = excluded.provided_at, "
                "source_type = excluded.source_type",
                (
                    case_id, lever_id, input_key,
                    1 if merged.get("measure_in_pov") else 0,
                    merged.get("provided_by_name"), merged.get("provided_by_role"),
                    merged.get("provided_at"), merged.get("source_type"),
                ),
            )
        if values or meta:
            conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now_iso(), case_id))


def upsert_owner(case_id: str, lever_id: str, owner_name: str, owner_role: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO lever_owners (case_id, lever_id, owner_name, owner_role) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(case_id, lever_id) DO UPDATE SET owner_name = excluded.owner_name, owner_role = excluded.owner_role",
            (case_id, lever_id, owner_name, owner_role),
        )
        conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now_iso(), case_id))


def purge_all():
    """The 30-second reset - wipes every case. Gated behind the passphrase
    at the API layer, never exposed unauthenticated."""
    with get_conn() as conn:
        conn.executescript(
            "DELETE FROM lever_owners; DELETE FROM lever_input_meta; DELETE FROM lever_input_values; DELETE FROM cases;"
        )
