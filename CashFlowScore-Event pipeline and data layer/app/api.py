from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .contracts import FEATURE_COLUMNS, BusinessProfile, RawEvent
from .pipeline import build_pipeline

pipeline = build_pipeline()
app = FastAPI(title="CashFlowScore Event Pipeline", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_DEMO_HTML = Path(__file__).parent / "demo.html"


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def live_demo() -> HTMLResponse:
    """Open http://localhost:8002/demo in a browser for the live pipeline demo."""
    return HTMLResponse(_DEMO_HTML.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    status = pipeline.snapshot()
    return {
        "status": "healthy",
        "services": {
            "redpanda": status["redpanda_up"],
            "redis": status["redis_up"],
            "postgres": status["postgres_up"],
        },
        "events_processed": status["events_processed"],
    }


@app.get("/pipeline-status")
def pipeline_status() -> dict:
    status = pipeline.snapshot()
    status["recent_activity_count"] = len(pipeline.store.recent_activity(limit=25))
    return status


@app.get("/activity-feed")
def activity_feed(limit: int = 25) -> dict:
    return {
        "count": len(pipeline.store.recent_activity(limit=limit)),
        "items": pipeline.store.recent_activity(limit=limit),
    }


@app.get("/demo-story")
def demo_story() -> dict:
    status = pipeline.snapshot()
    activity = pipeline.store.recent_activity(limit=5)
    return {
        "headline": "Live cash-flow infrastructure, not just a scorer",
        "story": [
            f"{status['business_count']} businesses are registered and the event stream is live.",
            f"Queue depth is {status['queue_depth']} and dedup is running via {status['dedup_backend']}.",
            f"Feature cache is using {status['cache_backend']} and recent activity is being tracked.",
            "Use /businesses for the portfolio view, /features/{business_id} for the ML handoff, and /activity-feed to show the backend moving.",
        ],
        "recent_activity": activity,
        "status": status,
    }


@app.get("/dashboard/bootstrap")
def dashboard_bootstrap(business_limit: int = 6, activity_limit: int = 10) -> dict:
    status = pipeline.snapshot()
    activity = pipeline.store.recent_activity(limit=activity_limit)
    business_ids = pipeline.store.list_business_ids()[:business_limit]
    featured_businesses = []

    for business_id in business_ids:
        profile = pipeline.store.get_business_profile(business_id) or {"business_id": business_id}
        try:
            features = pipeline.get_features(business_id)
        except KeyError:
            features = None

        featured_businesses.append(
            {
                "business_id": business_id,
                "profile": profile,
                "features": features,
            }
        )

    return {
        "headline": "CashFlowScore is live and moving",
        "elevator_pitch": "One request shows the live event pipeline, the business portfolio, and the backend activity trail.",
        "hero_metrics": {
            "businesses_registered": status["business_count"],
            "events_processed": status["events_processed"],
            "queue_depth": status["queue_depth"],
            "dedup_backend": status["dedup_backend"],
            "cache_backend": status["cache_backend"],
        },
        "story": [
            f"{status['business_count']} businesses are registered and the event stream is live.",
            f"Queue depth is {status['queue_depth']} and dedup is running via {status['dedup_backend']}.",
            f"Feature cache is using {status['cache_backend']} and the dashboard can watch activity in real time.",
        ],
        "judge_talk_track": [
            "This is not just a score service; it is the live data layer, feature engine, and portfolio control plane.",
            "The dashboard can show business cards, activity, and status from one canonical backend response.",
            "Akash's scoring service and Nikita's frontend both consume the same documented contracts.",
        ],
        "status": status,
        "activity_feed": {
            "count": len(activity),
            "items": activity,
        },
        "featured_businesses": featured_businesses,
        "feature_contract": FEATURE_COLUMNS,
    }


@app.get("/businesses")
def businesses() -> dict:
    business_ids = pipeline.store.list_business_ids()
    items = []
    for business_id in business_ids:
        profile = pipeline.store.get_business_profile(business_id) or {"business_id": business_id}
        try:
            features = pipeline.get_features(business_id)
        except KeyError:
            features = None
        items.append(
            {
                "business_id": business_id,
                "profile": profile,
                "features": features,
            }
        )
    return {"count": len(items), "items": items}


@app.get("/businesses/{business_id}")
def business_detail(business_id: str) -> dict:
    profile = pipeline.store.get_business_profile(business_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Unknown business_id: {business_id}")
    return {
        "business_id": business_id,
        "profile": profile,
        "features": pipeline.get_features(business_id),
        "recent_events": pipeline.store.list_events(business_id),
    }


@app.get("/transactions/{business_id}")
def transactions(business_id: str) -> dict:
    profile = pipeline.store.get_business_profile(business_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Unknown business_id: {business_id}")
    return {
        "business_id": business_id,
        "events": pipeline.store.list_events(business_id),
    }


@app.get("/features/{business_id}")
def features(business_id: str) -> dict:
    try:
        return pipeline.get_features(business_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/events/publish")
def publish_event(event: dict) -> dict:
    normalized = RawEvent.from_mapping(event)
    return pipeline.publish_event(normalized.as_record())


@app.post("/transactions/ingest")
def ingest_transaction(event: dict) -> dict:
    normalized = RawEvent.from_mapping(event)
    accepted = pipeline.publish_event(normalized.as_record())
    return {
        "accepted": accepted["accepted"],
        "event_id": accepted["event_id"],
        "ingestion_path": "stream",
    }


@app.post("/transactions/bulk")
def ingest_transactions(events: List[dict]) -> dict:
    accepted = 0
    rejected = 0
    event_ids: List[str] = []

    for payload in events:
        try:
            normalized = RawEvent.from_mapping(payload)
            pipeline.publish_event(normalized.as_record())
            accepted += 1
            event_ids.append(normalized.event_id)
        except Exception:
            rejected += 1

    return {
        "accepted": accepted,
        "rejected": rejected,
        "event_ids": event_ids,
        "queue_depth": pipeline.snapshot()["queue_depth"],
    }


@app.post("/demo/bootstrap")
def bootstrap_demo(count: int = 75, seed: int = 42, months: int = 6) -> dict:
    result = pipeline.seed_demo_data(count=count, seed=seed, months=months)
    return {**result, "status": "queued", "feature_contract": FEATURE_COLUMNS}


@app.post("/businesses/register")
def register_business(profile: dict) -> dict:
    normalized = BusinessProfile.from_mapping(profile)
    pipeline.register_business(normalized)
    return {"registered": True, "business_id": normalized.business_id}


@app.get("/contracts/features")
def feature_contract() -> dict:
    return {"feature_columns": FEATURE_COLUMNS}


# ── Data Cleaning Demo ─────────────────────────────────────────────────────────

@app.get("/data-cleaning/raw")
def data_cleaning_raw() -> dict:
    """
    Returns synthetic dirty transaction data — missing values, wrong formats.
    This is what the data cleaning demo shows BEFORE cleaning.
    """
    raw_rows = [
        {"txn_id": "TXN-1001", "business": "ABC Stores",  "type": "UPI",    "amount": "₹12,450", "timestamp": "2026-07-01 10:12", "status": "dirty"},
        {"txn_id": "TXN-1002", "business": None,           "type": "GST",    "amount": None,       "timestamp": "2026-07-01 10:14", "status": "dirty"},
        {"txn_id": "TXN-1003", "business": "XYZ Mart",    "type": "Bank",   "amount": "₹4,500",  "timestamp": "2026-07-01 10:17", "status": "dirty"},
        {"txn_id": "TXN-1004", "business": "XYZ Mart",    "type": "Bounce", "amount": None,       "timestamp": None,               "status": "dirty"},
        {"txn_id": "TXN-1005", "business": "LMN Shop",    "type": "UPI",    "amount": "₹8,900",  "timestamp": "2026-07-01 10:22", "status": "dirty"},
        {"txn_id": "TXN-1006", "business": "LMN Shop",    "type": "Bank",   "amount": "",         "timestamp": "2026-07-01 10:25", "status": "dirty"},
        {"txn_id": "TXN-1007", "business": "Raj Traders", "type": "UPI",    "amount": "abc",      "timestamp": "2026-07-01 10:28", "status": "dirty"},
        {"txn_id": "TXN-1008", "business": None,           "type": None,     "amount": "₹3,200",  "timestamp": "2026-07-01 10:30", "status": "dirty"},
    ]
    missing_count = sum(
        1 for row in raw_rows for v in row.values()
        if v is None or v == ""
    )
    return {
        "rows": raw_rows,
        "total_rows": len(raw_rows),
        "missing_count": missing_count,
        "columns": ["txn_id", "business", "type", "amount", "timestamp"],
    }


@app.post("/data-cleaning/clean")
def data_cleaning_clean() -> dict:
    """
    Runs the cleaning pipeline on the dirty data:
    - Strips currency symbols, parses amounts to float
    - Fills missing business with 'Unknown'
    - Fills missing type with 'Unknown'
    - Fills missing/invalid amount with median
    - Fills missing timestamp with 'N/A'
    Then publishes cleaned rows as real pipeline events.
    """
    import re, uuid
    from datetime import datetime, timezone

    raw_rows = [
        {"txn_id": "TXN-1001", "business": "ABC Stores",  "type": "UPI",    "amount": "₹12,450", "timestamp": "2026-07-01 10:12"},
        {"txn_id": "TXN-1002", "business": None,           "type": "GST",    "amount": None,       "timestamp": "2026-07-01 10:14"},
        {"txn_id": "TXN-1003", "business": "XYZ Mart",    "type": "Bank",   "amount": "₹4,500",  "timestamp": "2026-07-01 10:17"},
        {"txn_id": "TXN-1004", "business": "XYZ Mart",    "type": "Bounce", "amount": None,       "timestamp": None},
        {"txn_id": "TXN-1005", "business": "LMN Shop",    "type": "UPI",    "amount": "₹8,900",  "timestamp": "2026-07-01 10:22"},
        {"txn_id": "TXN-1006", "business": "LMN Shop",    "type": "Bank",   "amount": "",         "timestamp": "2026-07-01 10:25"},
        {"txn_id": "TXN-1007", "business": "Raj Traders", "type": "UPI",    "amount": "abc",      "timestamp": "2026-07-01 10:28"},
        {"txn_id": "TXN-1008", "business": None,           "type": None,     "amount": "₹3,200",  "timestamp": "2026-07-01 10:30"},
    ]

    def parse_amount(v):
        if v is None or str(v).strip() == "":
            return None
        cleaned = re.sub(r"[^0-9.]", "", str(v))
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    # Parse amounts to get median
    amounts = [parse_amount(r["amount"]) for r in raw_rows]
    valid_amounts = [a for a in amounts if a is not None]
    median_amount = sorted(valid_amounts)[len(valid_amounts) // 2] if valid_amounts else 0.0

    cleaned_rows = []
    fixes = []
    for i, row in enumerate(raw_rows):
        clean = dict(row)
        row_fixes = []

        # Business
        if not clean["business"]:
            clean["business"] = "Unknown"
            row_fixes.append("business filled")

        # Type
        if not clean["type"]:
            clean["type"] = "Unknown"
            row_fixes.append("type filled")

        # Amount
        parsed = parse_amount(clean["amount"])
        if parsed is None:
            clean["amount"] = median_amount
            row_fixes.append(f"amount filled with median ₹{median_amount:,.0f}")
        else:
            clean["amount"] = parsed

        # Timestamp
        if not clean["timestamp"]:
            clean["timestamp"] = "2026-07-01 00:00"
            row_fixes.append("timestamp filled")

        clean["status"] = "clean"
        clean["fixes"] = row_fixes
        cleaned_rows.append(clean)
        if row_fixes:
            fixes.append({"row": clean["txn_id"], "fixes": row_fixes})

    # Publish cleaned rows as real pipeline events
    topic_map = {"UPI": "txn.upi", "Bank": "txn.bank", "GST": "gst.filing",
                 "Bounce": "txn.bank", "Unknown": "txn.bank"}
    events_published = 0
    for row in cleaned_rows:
        try:
            evt = {
                "event_id": f"cleaning-{row['txn_id']}-{uuid.uuid4().hex[:8]}",
                "business_id": f"clean-{row['business'].lower().replace(' ', '-')[:12]}",
                "topic": topic_map.get(row["type"], "txn.bank"),
                "event_type": "bounce" if row["type"] == "Bounce" else "credit",
                "amount": float(row["amount"]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "direction": "outflow" if row["type"] == "Bounce" else "inflow",
                "balance_after": float(row["amount"]) * 1.1,
                "metadata": {"source": "data_cleaning_demo", "txn_id": row["txn_id"]},
            }
            pipeline.publish_event(evt)
            events_published += 1
        except Exception:
            pass

    return {
        "cleaned_rows": cleaned_rows,
        "total_rows": len(cleaned_rows),
        "fixes_applied": fixes,
        "total_fixes": sum(len(f["fixes"]) for f in fixes),
        "events_published": events_published,
        "median_amount_used": median_amount,
        "message": f"Cleaned {len(cleaned_rows)} rows, applied {sum(len(f['fixes']) for f in fixes)} fixes, published {events_published} events to pipeline.",
    }


# ── Live verification endpoints ───────────────────────────────────────────────
# Run real docker commands inline or pop a terminal window during demo.

_DOCKER_PREFIX = "cashflowscore-eventpipelineanddatalayer"

_TERMINAL_COMMANDS = {
    "timescaledb_rows": (
        "TimescaleDB: Event counts by topic",
        f'docker exec {_DOCKER_PREFIX}-postgres-1 psql -U cashflow -d cashflowscore '
        f'-c "SELECT topic, COUNT(*) AS events, MIN(timestamp)::date AS earliest, '
        f'MAX(timestamp)::date AS latest FROM events GROUP BY topic ORDER BY events DESC;"'
    ),
    "timescaledb_hypertable": (
        "TimescaleDB: Hypertable chunk info",
        f'docker exec {_DOCKER_PREFIX}-postgres-1 psql -U cashflow -d cashflowscore '
        f'-c "SELECT hypertable_name, num_chunks FROM timescaledb_information.hypertables;"'
    ),
    "timescaledb_recent": (
        "TimescaleDB: 10 most recent events",
        f'docker exec {_DOCKER_PREFIX}-postgres-1 psql -U cashflow -d cashflowscore '
        f'-c "SELECT event_id, business_id, topic, amount, direction, timestamp '
        f'FROM events ORDER BY timestamp DESC LIMIT 10;"'
    ),
    "redis_keyspace": (
        "Redis: Live keyspace (dedup + feature cache keys)",
        f'docker exec {_DOCKER_PREFIX}-redis-1 redis-cli info keyspace'
    ),
    "redis_dedup_sample": (
        "Redis: Sample dedup keys (SETNX idempotency)",
        f'docker exec {_DOCKER_PREFIX}-redis-1 redis-cli --scan --pattern "dedup:*" | Select-Object -First 20'
    ),
    "redpanda_cluster": (
        "Redpanda: Live cluster info",
        f'docker exec {_DOCKER_PREFIX}-redpanda-1 rpk cluster info'
    ),
    "redpanda_topics": (
        "Redpanda: Topics list",
        f'docker exec {_DOCKER_PREFIX}-redpanda-1 rpk topic list'
    ),
    "docker_ps": (
        "Docker: All running containers",
        'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
    ),
}


@app.get("/run-query/{query_id}")
def run_query(query_id: str) -> dict:
    """
    Execute a real Docker/psql/redis-cli command and return the raw output.
    Called by the demo page to populate inline result panels.
    """
    if query_id not in _TERMINAL_COMMANDS:
        raise HTTPException(status_code=404, detail=f"Unknown query: {query_id}")

    title, cmd = _TERMINAL_COMMANDS[query_id]
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=12
        )
        output = (result.stdout or "") + (result.stderr or "")
        return {
            "query_id": query_id,
            "title": title,
            "command": cmd,
            "output": output.strip() or "(no output)",
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"query_id": query_id, "title": title, "command": cmd,
                "output": "Timed out after 12s — is Docker running?", "exit_code": -1}
    except Exception as exc:
        return {"query_id": query_id, "title": title, "command": cmd,
                "output": f"Error: {exc}", "exit_code": -1}


@app.post("/launch-terminal/{query_id}")
def launch_terminal(query_id: str) -> dict:
    """
    Writes a .ps1 to %TEMP% and opens it in a new PowerShell window.
    Returns immediately — window pops up in <300ms.
    """
    if query_id not in _TERMINAL_COMMANDS:
        raise HTTPException(status_code=404, detail=f"Unknown query: {query_id}")

    title, cmd = _TERMINAL_COMMANDS[query_id]

    import tempfile, os
    # Write script to a .ps1 file — avoids all subprocess quoting/escaping
    script = "\n".join([
        f'$host.UI.RawUI.WindowTitle = "{title}"',
        f'Write-Host ("=" * 62) -ForegroundColor DarkGray',
        f'Write-Host "  {title}" -ForegroundColor Cyan',
        f'Write-Host ("=" * 62) -ForegroundColor DarkGray',
        'Write-Host ""',
        cmd,          # raw command written as plain text — no escaping needed
        'Write-Host ""',
        'Write-Host "--- finished ---" -ForegroundColor Green',
        'Write-Host "Press any key to close..." -ForegroundColor DarkGray',
        '$null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")',
    ])

    tmp_path = os.path.join(tempfile.gettempdir(), f"cfs_{query_id}.ps1")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(script)

    try:
        # Use shell=True so Windows finds powershell.exe — returns instantly
        subprocess.Popen(
            f'powershell -NoProfile -ExecutionPolicy Bypass -File "{tmp_path}"',
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return {"launched": True, "query_id": query_id, "title": title}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
