from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from .contracts import BusinessProfile, RawEvent, parse_timestamp

# ── optional deps ─────────────────────────────────────────────────────────────
try:
    import redis as _redis_lib  # type: ignore
except Exception:
    _redis_lib = None

try:
    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore
except Exception:
    psycopg2 = None  # type: ignore

_PG_DSN = os.getenv(
    "PG_DSN",
    "host=localhost port=5432 dbname=cashflowscore user=cashflow password=cashflow connect_timeout=3",
)
_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _pg_connect():
    """Return a new psycopg2 connection, or None if unavailable."""
    if psycopg2 is None:
        return None
    try:
        conn = psycopg2.connect(_PG_DSN)
        conn.autocommit = True
        return conn
    except Exception:
        return None


def _redis_connect():
    """Return a connected Redis client, or None if unavailable."""
    if _redis_lib is None:
        return None
    try:
        client = _redis_lib.Redis.from_url(_REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


class PipelineStore:
    """
    Dual-write store: SQLite (fast, always available) + Postgres/TimescaleDB (demo-visible).
    Redis is used for dedup (SETNX) and feature caching.
    Falls back gracefully when Docker services are down.
    """

    def __init__(self, db_path: str | Path = "data/pipeline.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._dedup_lock = Lock()
        self._dedup_seen: set[str] = set()

        # ── SQLite (primary, always on) ──────────────────────────────────────
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._ensure_schema()

        # ── Redis (dedup + feature cache) ────────────────────────────────────
        self._rc = _redis_connect()

        # ── Postgres / TimescaleDB (dual-write for demo) ─────────────────────
        self._pg = _pg_connect()

    # ── schema ────────────────────────────────────────────────────────────────

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS businesses (
                    business_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    direction TEXT NOT NULL,
                    balance_after REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_business_time
                    ON events (business_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_topic_time
                    ON events (topic, timestamp);
                CREATE TABLE IF NOT EXISTS stress_flags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    business_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pipeline_stats (
                    stat_key TEXT PRIMARY KEY,
                    stat_value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activity_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    business_id TEXT,
                    event_id TEXT,
                    created_at TEXT NOT NULL
                );
            """)
            self._conn.commit()

    # ── internal Postgres helpers ─────────────────────────────────────────────

    def _pg_exec(self, sql: str, params: tuple = ()) -> None:
        """Fire-and-forget write to Postgres; silently skips if PG is down."""
        if self._pg is None:
            return
        try:
            with self._pg.cursor() as cur:
                cur.execute(sql, params)
        except Exception:
            # Reconnect once; if that fails too, go silent.
            self._pg = _pg_connect()

    def _pg_exec_many(self, sql: str, rows: list) -> None:
        if self._pg is None or not rows:
            return
        try:
            with self._pg.cursor() as cur:
                psycopg2.extras.execute_batch(cur, sql, rows, page_size=200)
        except Exception:
            self._pg = _pg_connect()

    # ── dedup ─────────────────────────────────────────────────────────────────

    def claim_event_id(self, event_id: str) -> bool:
        """Returns True if this event_id is new (claim it). False = duplicate."""
        if self._rc is not None:
            try:
                return bool(self._rc.set(f"dedup:{event_id}", "1", nx=True, ex=86400))
            except Exception:
                self._rc = _redis_connect()
        with self._dedup_lock:
            if event_id in self._dedup_seen:
                return False
            self._dedup_seen.add(event_id)
            return True

    def dedup_backend(self) -> str:
        return "redis" if self._rc is not None else "memory"

    # ── businesses ────────────────────────────────────────────────────────────

    def register_business(self, profile: BusinessProfile | Dict[str, Any]) -> None:
        payload = profile.as_record() if isinstance(profile, BusinessProfile) else dict(profile)
        biz_id = str(payload["business_id"])
        now = parse_timestamp(None).isoformat()
        profile_json = json.dumps(payload)

        # SQLite
        with self._lock:
            self._conn.execute(
                """INSERT INTO businesses (business_id, profile_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(business_id) DO UPDATE SET
                       profile_json = excluded.profile_json,
                       updated_at   = excluded.updated_at""",
                (biz_id, profile_json, now, now),
            )
            self._conn.commit()

        # Postgres dual-write
        self._pg_exec(
            """INSERT INTO businesses (business_id, profile_json, created_at, updated_at)
               VALUES (%s, %s, NOW(), NOW())
               ON CONFLICT (business_id) DO UPDATE SET
                   profile_json = EXCLUDED.profile_json,
                   updated_at   = NOW()""",
            (biz_id, profile_json),
        )

    def get_business_profile(self, business_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT profile_json FROM businesses WHERE business_id = ?", (business_id,)
            ).fetchone()
        return json.loads(row["profile_json"]) if row else None

    def list_business_ids(self) -> List[str]:
        with self._lock:
            return [r["business_id"] for r in self._conn.execute(
                "SELECT business_id FROM businesses ORDER BY business_id"
            ).fetchall()]

    # ── events ────────────────────────────────────────────────────────────────

    def insert_event(self, event: RawEvent | Dict[str, Any]) -> bool:
        payload = event.as_record() if isinstance(event, RawEvent) else dict(event)
        row = (
            payload["event_id"],
            payload["business_id"],
            payload.get("topic", "txn.bank"),
            payload.get("event_type", "credit"),
            float(payload.get("amount", 0.0)),
            payload.get("direction", "inflow"),
            float(payload.get("balance_after", 0.0)),
            str(payload.get("timestamp")),
            json.dumps(payload.get("metadata", {})),
        )

        # SQLite
        with self._lock:
            cur = self._conn.execute(
                """INSERT OR IGNORE INTO events
                   (event_id, business_id, topic, event_type, amount,
                    direction, balance_after, timestamp, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                row,
            )
            self._conn.commit()
            inserted = cur.rowcount > 0

        # Postgres dual-write (non-blocking)
        if inserted:
            self._pg_exec(
                """INSERT INTO events
                   (event_id, business_id, topic, event_type, amount,
                    direction, balance_after, timestamp, metadata_json)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s::timestamptz, %s)
                   ON CONFLICT (event_id, timestamp) DO NOTHING""",
                row,
            )

        return inserted

    def insert_events(self, events: Iterable[RawEvent | Dict[str, Any]]) -> Dict[str, int]:
        inserted = duplicate = 0
        rows: list = []
        for event in events:
            p = event.as_record() if isinstance(event, RawEvent) else dict(event)
            rows.append((
                p["event_id"], p["business_id"],
                p.get("topic", "txn.bank"), p.get("event_type", "credit"),
                float(p.get("amount", 0.0)), p.get("direction", "inflow"),
                float(p.get("balance_after", 0.0)), str(p.get("timestamp")),
                json.dumps(p.get("metadata", {})),
            ))

        with self._lock:
            self._conn.execute("BEGIN")
            for row in rows:
                cur = self._conn.execute(
                    """INSERT OR IGNORE INTO events
                       (event_id, business_id, topic, event_type, amount,
                        direction, balance_after, timestamp, metadata_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    row,
                )
                if cur.rowcount > 0:
                    inserted += 1
                else:
                    duplicate += 1
            self._conn.commit()

        # Postgres batch dual-write
        if rows:
            self._pg_exec_many(
                """INSERT INTO events
                   (event_id, business_id, topic, event_type, amount,
                    direction, balance_after, timestamp, metadata_json)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s::timestamptz, %s)
                   ON CONFLICT (event_id, timestamp) DO NOTHING""",
                rows,
            )

        return {"inserted": inserted, "duplicate": duplicate}

    def list_events(self, business_id: str, since_days: int = 365) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT event_id, business_id, topic, event_type, amount, direction,
                          balance_after, timestamp, metadata_json
                   FROM events WHERE business_id = ? ORDER BY timestamp ASC""",
                (business_id,),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            items.append(item)
        return items

    # ── stress flags ──────────────────────────────────────────────────────────

    def record_stress_flag(self, event: RawEvent | Dict[str, Any], reason: str) -> bool:
        p = event.as_record() if isinstance(event, RawEvent) else dict(event)
        row = (p["event_id"], p["business_id"], reason,
               float(p.get("amount", 0.0)), str(p.get("timestamp")))
        with self._lock:
            cur = self._conn.execute(
                """INSERT OR IGNORE INTO stress_flags
                   (event_id, business_id, reason, amount, timestamp) VALUES (?, ?, ?, ?, ?)""",
                row,
            )
            self._conn.commit()
            inserted = cur.rowcount > 0
        if inserted:
            self._pg_exec(
                """INSERT INTO stress_flags (event_id, business_id, reason, amount, timestamp)
                   VALUES (%s, %s, %s, %s, %s::timestamptz)
                   ON CONFLICT (event_id) DO NOTHING""",
                row,
            )
        return inserted

    # ── activity log ──────────────────────────────────────────────────────────

    def record_activity(self, category: str, message: str,
                        business_id: str | None = None,
                        event_id: str | None = None) -> None:
        now = parse_timestamp(None).isoformat()
        with self._lock:
            self._conn.execute(
                """INSERT INTO activity_events (category, message, business_id, event_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (category, message, business_id, event_id, now),
            )
            self._conn.commit()
        # Also push to Postgres so activity is visible there too
        self._pg_exec(
            """INSERT INTO activity_events (category, message, business_id, event_id, created_at)
               VALUES (%s, %s, %s, %s, %s::timestamptz)""",
            (category, message, business_id, event_id, now),
        )

    def recent_activity(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT category, message, business_id, event_id, created_at
                   FROM activity_events ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── counters (all read from SQLite — fast) ────────────────────────────────

    def get_last_event_timestamp(self) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT timestamp FROM events ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
        return row["timestamp"] if row else None

    def count_events(self) -> int:
        with self._lock:
            return int(self._conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"])

    def count_businesses(self) -> int:
        with self._lock:
            return int(self._conn.execute("SELECT COUNT(*) AS c FROM businesses").fetchone()["c"])

    def count_stress_flags(self) -> int:
        with self._lock:
            return int(self._conn.execute("SELECT COUNT(*) AS c FROM stress_flags").fetchone()["c"])

    def count_events_by_topic(self) -> Dict[str, int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT topic, COUNT(*) AS c FROM events GROUP BY topic ORDER BY topic"
            ).fetchall()
        return {r["topic"]: int(r["c"]) for r in rows}

    def count_duplicate_events(self) -> int:
        with self._lock:
            total = int(self._conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"])
            distinct = int(self._conn.execute(
                "SELECT COUNT(DISTINCT event_id) AS c FROM events"
            ).fetchone()["c"])
        return max(total - distinct, 0)

    # ── pipeline stats KV ─────────────────────────────────────────────────────

    def set_stat(self, key: str, value: Any) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO pipeline_stats (stat_key, stat_value) VALUES (?, ?)
                   ON CONFLICT(stat_key) DO UPDATE SET stat_value = excluded.stat_value""",
                (key, json.dumps(value)),
            )
            self._conn.commit()

    def get_stat(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT stat_value FROM pipeline_stats WHERE stat_key = ?", (key,)
            ).fetchone()
        return json.loads(row["stat_value"]) if row else default

    # ── service probes (used by /pipeline-status) ─────────────────────────────

    def postgres_row_count(self) -> Optional[int]:
        """Return total event rows in TimescaleDB, or None if PG is down."""
        if self._pg is None:
            return None
        try:
            with self._pg.cursor() as cur:
                cur.execute("SELECT count(*) FROM events")
                return cur.fetchone()[0]
        except Exception:
            return None

    def redis_key_count(self) -> Optional[int]:
        """Return total Redis key count, or None if Redis is down."""
        if self._rc is None:
            return None
        try:
            return self._rc.dbsize()
        except Exception:
            return None
