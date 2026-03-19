"""
persistence.py — SQLite-backed progress tracking.

Tracks:
  - Session history (bank, layer, score, timestamp)
  - Layer checkpoint log (Layer A 3-session rule)
  - Miss log (per question/layer for remediation)
  - Interference pair miss counts (for Layer D prioritization)
"""
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, date

DB_PATH = Path(__file__).parent / "progress.db"


def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db():
    """Create tables if they don't exist."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id     TEXT    NOT NULL,
            bank_title  TEXT,
            layer       TEXT,
            score_pct   REAL,
            earned      INTEGER,
            max_pts     INTEGER,
            q_count     INTEGER,
            elapsed_sec INTEGER,
            ts          TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS layer_checkpoints (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id     TEXT    NOT NULL,
            layer       TEXT    NOT NULL,
            session_num INTEGER NOT NULL,  -- 1, 2, or 3 (for Layer A 3-step rule)
            score_pct   REAL,
            passed      INTEGER,           -- 1=yes, 0=no
            ts          TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS miss_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_id         TEXT,
            question_id     TEXT,
            layer           TEXT,
            layer_subtype   TEXT,
            concept_bucket  TEXT,
            miss_type       TEXT,
            interference_pair TEXT,
            ts              TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS interference_priority (
            bank_id         TEXT,
            pair_name       TEXT,
            miss_count      INTEGER DEFAULT 0,
            last_missed     TEXT,
            PRIMARY KEY (bank_id, pair_name)
        );
        """)


def save_session(bank_id, bank_title, layer, score_pct, earned, max_pts,
                 q_count, elapsed_sec, miss_details):
    """
    Persist a completed session.
    miss_details: list of (q, earned, max, detail_dict) from aggregate_results
    """
    init_db()
    with _conn() as c:
        c.execute("""
            INSERT INTO sessions (bank_id, bank_title, layer, score_pct,
                                  earned, max_pts, q_count, elapsed_sec)
            VALUES (?,?,?,?,?,?,?,?)
        """, (bank_id, bank_title, layer, score_pct, earned, max_pts, q_count, elapsed_sec))

        now = datetime.utcnow().isoformat()
        for q, e, p, d in miss_details:
            if e < p:  # only log misses
                miss_type = d.get("inferred_miss_type", "")
                pair = q.get("interference_pair", "")
                c.execute("""
                    INSERT INTO miss_log
                    (bank_id, question_id, layer, layer_subtype, concept_bucket,
                     miss_type, interference_pair)
                    VALUES (?,?,?,?,?,?,?)
                """, (bank_id, q.get("id",""), q.get("layer",""),
                      q.get("layer_subtype",""), q.get("concept_bucket",""),
                      miss_type, pair))

                if pair:
                    c.execute("""
                        INSERT INTO interference_priority (bank_id, pair_name, miss_count, last_missed)
                        VALUES (?,?,1,?)
                        ON CONFLICT(bank_id, pair_name) DO UPDATE SET
                            miss_count = miss_count + 1,
                            last_missed = excluded.last_missed
                    """, (bank_id, pair, now))


def record_layer_checkpoint(bank_id, layer, session_num, score_pct, passed):
    """Record a Layer A/B/C/D checkpoint (3-session mastery rule)."""
    init_db()
    with _conn() as c:
        c.execute("""
            INSERT INTO layer_checkpoints
            (bank_id, layer, session_num, score_pct, passed)
            VALUES (?,?,?,?,?)
        """, (bank_id, layer, session_num, score_pct, int(passed)))


def get_layer_history(bank_id, layer):
    """Return list of checkpoint rows for a bank+layer, ordered by ts."""
    init_db()
    with _conn() as c:
        rows = c.execute("""
            SELECT * FROM layer_checkpoints
            WHERE bank_id=? AND layer=?
            ORDER BY ts ASC
        """, (bank_id, layer)).fetchall()
    return [dict(r) for r in rows]


def get_session_history(bank_id=None, limit=20):
    """Return recent sessions, optionally filtered by bank."""
    init_db()
    with _conn() as c:
        if bank_id:
            rows = c.execute("""
                SELECT * FROM sessions WHERE bank_id=?
                ORDER BY ts DESC LIMIT ?
            """, (bank_id, limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT * FROM sessions ORDER BY ts DESC LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_priority_pairs(bank_id):
    """Return interference pairs ordered by miss count (highest first)."""
    init_db()
    with _conn() as c:
        rows = c.execute("""
            SELECT pair_name, miss_count, last_missed
            FROM interference_priority
            WHERE bank_id=?
            ORDER BY miss_count DESC
        """, (bank_id,)).fetchall()
    return [dict(r) for r in rows]


def get_weak_concepts(bank_id, limit=5):
    """Return concept buckets with highest miss rates."""
    init_db()
    with _conn() as c:
        rows = c.execute("""
            SELECT concept_bucket, COUNT(*) as miss_count
            FROM miss_log
            WHERE bank_id=? AND concept_bucket != ''
            GROUP BY concept_bucket
            ORDER BY miss_count DESC
            LIMIT ?
        """, (bank_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get_layer_mastery_summary(bank_id):
    """
    Returns dict: {layer: {sessions, best_pct, last_pct, is_mastered}}
    A layer is 'mastered' if the 3 checkpoint rule is satisfied for Layer A,
    or last score >= threshold for others.
    """
    from config import LAYER_STOP_RULES
    init_db()
    with _conn() as c:
        rows = c.execute("""
            SELECT layer, score_pct, ts
            FROM sessions
            WHERE bank_id=?
            ORDER BY ts ASC
        """, (bank_id,)).fetchall()

    summary = {}
    for r in rows:
        l = r["layer"] or "All Layers"
        if l not in summary:
            summary[l] = {"sessions": [], "best_pct": 0, "last_pct": 0}
        summary[l]["sessions"].append(r["score_pct"])
        summary[l]["best_pct"] = max(summary[l]["best_pct"], r["score_pct"])
        summary[l]["last_pct"] = r["score_pct"]

    for l, d in summary.items():
        threshold = LAYER_STOP_RULES.get(l, 68)
        d["threshold"] = threshold
        d["is_mastered"] = d["last_pct"] >= threshold
        d["session_count"] = len(d["sessions"])

    return summary


def layer_is_unlocked(bank_id, layer):
    """
    Soft enforcement: returns (unlocked: bool, reason: str).
    Layer A is always unlocked. Each subsequent layer requires the previous
    to have been attempted at least once AND scored >= threshold.
    """
    from config import LAYER_ORDER, LAYER_STOP_RULES
    if layer not in LAYER_ORDER:
        return True, ""

    idx = LAYER_ORDER.index(layer)
    if idx == 0:
        return True, ""

    prev_layer = LAYER_ORDER[idx - 1]
    summary = get_layer_mastery_summary(bank_id)
    prev = summary.get(prev_layer)
    if not prev:
        return False, f"Complete at least one {prev_layer} session first."
    threshold = LAYER_STOP_RULES.get(prev_layer, 68)
    if prev["last_pct"] < threshold:
        return False, (f"Reach {threshold}% on {prev_layer} "
                       f"(current best: {prev['best_pct']:.0f}%) before advancing.")
    return True, ""
