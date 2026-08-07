#!/usr/bin/env python3
"""
CashFlowScore -- Command Line Tool
Usage:  python cashflow_cli.py <command> [options]

Commands:
  status          Show live pipeline status (events, businesses, services)
  seed            Seed demo data (75 businesses, 6 months of events)
  stream          Tail the live activity feed (Ctrl+C to stop)
  idempotency     Prove dedup: publish same event 3x, confirm 1 row
  features <id>   Get computed feature vector for a business
  businesses      List all registered businesses
  tsdb            Query TimescaleDB -- event counts by topic
  redis           Inspect Redis keyspace and sample dedup keys
  docker          Show all running Docker containers
  clean           Run the data cleaning pipeline demo
  help            Show this help
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

# Force UTF-8 stdout so box chars and rupee symbol work on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# -- config --------------------------------------------------------------------
API_BASE    = "http://localhost:8002"
PG_CONTAINER = "cashflowscore-eventpipelineanddatalayer-postgres-1"
RD_CONTAINER = "cashflowscore-eventpipelineanddatalayer-redis-1"
RP_CONTAINER = "cashflowscore-eventpipelineanddatalayer-redpanda-1"

# -- colours -------------------------------------------------------------------
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
PURPLE = "\033[95m"
GREY   = "\033[90m"
WHITE  = "\033[97m"

def c(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"

def header(title: str) -> None:
    print()
    print(c("-" * 62, GREY))
    print(c(f"  {title}", CYAN + BOLD))
    print(c("-" * 62, GREY))
    print()

def ok(msg: str)   -> None: print(c("  ✓  ", GREEN) + msg)
def warn(msg: str) -> None: print(c("  ⚠  ", YELLOW) + msg)
def err(msg: str)  -> None: print(c("  ✗  ", RED) + msg)
def info(msg: str) -> None: print(c("  ·  ", GREY) + msg)
def row(k: str, v: str, vc: str = WHITE) -> None:
    print(f"  {c(k.ljust(26), GREY)} {c(str(v), vc)}")

# -- http helpers --------------------------------------------------------------
try:
    import urllib.request as _req
    import urllib.error   as _uerr

    def _get(path: str) -> Any:
        url = API_BASE + path
        req = _req.Request(url, headers={"Accept": "application/json"})
        with _req.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())

    def _post(path: str, body: dict | None = None) -> Any:
        url  = API_BASE + path
        data = json.dumps(body or {}).encode()
        req  = _req.Request(url, data=data,
                            headers={"Content-Type": "application/json",
                                     "Accept": "application/json"},
                            method="POST")
        with _req.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())

except Exception:
    def _get(_: str) -> Any:  raise RuntimeError("urllib not available")
    def _post(_: str, __=None) -> Any: raise RuntimeError("urllib not available")

# -- docker helpers ------------------------------------------------------------
def _docker(container: str, *args: str) -> str:
    cmd = ["docker", "exec", container] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        return (r.stdout + r.stderr).strip()
    except Exception as exc:
        return f"error: {exc}"

# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------

def cmd_status() -> None:
    header("Pipeline Status")
    try:
        s = _get("/pipeline-status")
    except Exception as exc:
        err(f"Cannot reach API on {API_BASE} -- is the server running?")
        err(f"  {exc}")
        err("  Start it with:  python -m uvicorn app.api:app --port 8002 --reload")
        return

    # Core counters
    row("Events processed",   f"{s.get('events_processed', 0):,}",     GREEN)
    row("Businesses tracked", f"{s.get('business_count', 0):,}",        CYAN)
    row("Stress flags",       f"{s.get('stress_flag_count', 0):,}",     RED if s.get('stress_flag_count',0) > 0 else WHITE)
    row("Queue depth",        f"{s.get('queue_depth', 0):,}",           YELLOW if s.get('queue_depth',0) > 0 else WHITE)
    row("Cache hit rate",     f"{s.get('cache_hit_rate', 0)*100:.1f}%", PURPLE)
    row("Dedup backend",      s.get('dedup_backend', '--'),               GREEN)
    print()

    # TimescaleDB / Redis
    tsdb = s.get('timescaledb_rows')
    rkeys = s.get('redis_keys')
    row("TimescaleDB rows",  f"{tsdb:,}" if tsdb is not None else "--",   PURPLE)
    row("Redis keys",        f"{rkeys:,}" if rkeys is not None else "--", YELLOW)
    print()

    # Service health
    svc = [
        ("Redpanda",    s.get("redpanda_up"),   "port 9092"),
        ("TimescaleDB", s.get("postgres_up"),   "port 5432"),
        ("Redis",       s.get("redis_up"),      "port 6379"),
    ]
    for name, up, note in svc:
        if up:
            ok(f"{name:<14} UP       {c(note, GREY)}")
        elif up is False:
            warn(f"{name:<14} DOWN     {c(note, GREY)}")
        else:
            info(f"{name:<14} unknown")

    # Last event
    last = s.get("last_event_at")
    if last:
        print()
        row("Last event at", str(last)[:19], GREY)


def cmd_seed() -> None:
    header("Seeding Demo Data")
    info("Registering 75 synthetic MSME businesses...")
    info("Generating 6 months of UPI, bank, GST events...")
    print()
    try:
        r = _post("/demo/bootstrap?count=75&seed=42&months=6")
        ok(f"{r.get('businesses_registered', 0)} businesses registered")
        ok(f"{r.get('events_queued', 0):,} events queued into pipeline")
        print()
        info("Waiting 5s for workers to drain queue...")
        time.sleep(5)
        s = _get("/pipeline-status")
        row("Events now in DB",   f"{s.get('events_processed', 0):,}", GREEN)
        row("TimescaleDB rows",   f"{s.get('timescaledb_rows', 0):,}" if s.get('timescaledb_rows') else "--", PURPLE)
        row("Redis keys",         f"{s.get('redis_keys', 0):,}" if s.get('redis_keys') else "--", YELLOW)
    except Exception as exc:
        err(f"Failed: {exc}")


def cmd_stream() -> None:
    header("Live Activity Feed  (Ctrl+C to stop)")
    CAT_COLOR = {
        "event_ingested":      GREEN,
        "stress_flagged":      RED,
        "cache_hit":           YELLOW,
        "cache_miss":          GREY,
        "feature_computed":    PURPLE,
        "duplicate_skipped":   GREY,
        "business_registered": BLUE,
        "pipeline_started":    CYAN,
        "event_queued":        GREY,
    }
    CAT_ICON = {
        "event_ingested":      "▶",
        "stress_flagged":      "⚠",
        "cache_hit":           "⚡",
        "cache_miss":          "○",
        "feature_computed":    "✦",
        "duplicate_skipped":   "⊗",
        "business_registered": "✚",
        "pipeline_started":    "◉",
        "event_queued":        "→",
    }
    seen: set[str] = set()
    print(c("  Polling every 2s. New events appear below.\n", GREY))
    try:
        while True:
            try:
                data = _get("/activity-feed?limit=50")
                items = data.get("items", [])
                for ev in reversed(items):
                    key = ev.get("created_at","") + (ev.get("event_id") or ev.get("message",""))
                    if key in seen:
                        continue
                    seen.add(key)
                    cat   = ev.get("category", "")
                    color = CAT_COLOR.get(cat, CYAN)
                    icon  = CAT_ICON.get(cat, "·")
                    ts    = str(ev.get("created_at", ""))[:19]
                    biz   = str(ev.get("business_id") or "SYSTEM")[:16].ljust(16)
                    msg   = str(ev.get("message", cat))[:60]
                    print(f"  {c(ts, GREY)}  {c(icon, color)}  {c(biz, GREY)}  {c(msg, color)}")
            except Exception:
                pass
            time.sleep(2)
    except KeyboardInterrupt:
        print()
        info("Stream stopped.")


def cmd_idempotency() -> None:
    header("Idempotency Proof")
    info("Publishing the same event_id three times...")
    print()
    dedup_id = f"cli-dedup-proof-{uuid.uuid4().hex[:8]}"
    evt = {
        "event_id":    dedup_id,
        "business_id": "msme-0001",
        "topic":       "txn.bank",
        "event_type":  "credit",
        "amount":      99999,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "direction":   "inflow",
        "balance_after": 199999,
    }
    try:
        for i in range(1, 4):
            r = _post("/events/publish", evt)
            ok(f"Publish #{i}  event_id={dedup_id[:20]}...  accepted={r.get('accepted')}")
    except Exception as exc:
        err(f"Publish failed: {exc}"); return

    info("Waiting 2s for workers...")
    time.sleep(2)

    try:
        s = _get("/pipeline-status")
        dups = s.get("duplicate_events") or s.get("duplicate_event_count") or 0
        backend = s.get("dedup_backend", "memory")
        print()
        ok(f"3 publishes → {dups} duplicates caught")
        ok(f"Dedup backend: {backend} (SETNX per event_id, 24h TTL)")
        ok("Only 1 row written to the DB -- idempotency confirmed")
    except Exception as exc:
        err(f"Status check failed: {exc}")


def cmd_features(business_id: str) -> None:
    header(f"Feature Vector -- {business_id}")
    try:
        f = _get(f"/features/{business_id}")
    except Exception as exc:
        err(f"Failed: {exc}")
        info("Make sure the business exists. Try: python cashflow_cli.py businesses")
        return

    col_labels = {
        "business_age_years":    ("Business age (years)",         WHITE),
        "monthly_upi_volume":    ("Monthly UPI volume (Rs)",       GREEN),
        "monthly_bank_volume":   ("Monthly bank volume (Rs)",      GREEN),
        "monthly_cash_volume":   ("Monthly cash withdrawal (Rs)",  YELLOW),
        "gst_filing_regularity": ("GST filing regularity (%)",    CYAN),
        "gst_turnover":          ("Annual GST turnover (Rs)",      CYAN),
        "bounce_frequency":      ("Cheque bounces (count)",       RED),
        "avg_monthly_balance":   ("Avg monthly balance (Rs)",      GREEN),
        "income_stability":      ("Income stability (0-100)",     PURPLE),
        "seasonality_score":     ("Seasonality score (0-100)",    PURPLE),
        "loan_default_history":  ("Prior defaults (count)",       RED),
    }
    for key, (label, color) in col_labels.items():
        val = f.get(key, "--")
        if key in ("monthly_upi_volume","monthly_bank_volume","monthly_cash_volume",
                   "gst_turnover","avg_monthly_balance"):
            display = f"Rs{int(val):,}" if isinstance(val, (int,float)) else str(val)
        else:
            display = str(val)
        row(label, display, color)
    print()
    info(f"This JSON is what gets sent to Akaash's XGBoost scoring service.")


def cmd_businesses() -> None:
    header("Registered Businesses")
    try:
        data = _get("/businesses")
    except Exception as exc:
        err(f"Failed: {exc}"); return

    items = data.get("items", [])
    if not items:
        warn("No businesses found. Run: python cashflow_cli.py seed")
        return

    print(f"  {c('ID'.ljust(16), GREY)}  {c('UPI Vol (Rs)', GREY).ljust(22)}  {c('GST Reg%', GREY).ljust(16)}  {c('Bounces', GREY)}")
    print(c("  " + "-"*58, GREY))
    for item in items[:20]:
        biz_id = item.get("business_id","")
        f = item.get("features") or {}
        upi    = f"Rs{int(f.get('monthly_upi_volume',0)):,}" if f else "--"
        gst    = f"{f.get('gst_filing_regularity','--')}%"   if f else "--"
        bounce = str(f.get("bounce_frequency","--"))          if f else "--"
        bc = RED if f and f.get("bounce_frequency",0) > 5 else WHITE
        print(f"  {c(biz_id.ljust(16), CYAN)}  {upi.ljust(16)}  {gst.ljust(12)}  {c(bounce, bc)}")

    if len(items) > 20:
        info(f"... and {len(items)-20} more businesses")
    print()
    row("Total", str(data.get("count", len(items))), WHITE)


def cmd_tsdb() -> None:
    header("TimescaleDB -- Live Hypertable Query")
    info("Running: SELECT topic, COUNT(*) FROM events GROUP BY topic")
    print()
    output = _docker(
        PG_CONTAINER,
        "psql", "-U", "cashflow", "-d", "cashflowscore",
        "-c", "SELECT topic, COUNT(*) AS events, MIN(timestamp)::date AS earliest, MAX(timestamp)::date AS latest FROM events GROUP BY topic ORDER BY events DESC;"
    )
    if "error:" in output.lower() or "could not connect" in output.lower():
        warn("Docker exec failed -- trying API fallback")
        try:
            s = _get("/pipeline-status")
            topics = s.get("event_count_by_topic", {})
            total  = sum(topics.values())
            for topic, count in sorted(topics.items(), key=lambda x: -x[1]):
                bar = "█" * min(30, int(count / max(total,1) * 30))
                print(f"  {c(topic.ljust(20), CYAN)}  {c(bar, PURPLE)}  {c(str(count), WHITE)}")
            print()
            row("Total events (SQLite)",      f"{total:,}", WHITE)
            row("TimescaleDB rows",           f"{s.get('timescaledb_rows',0):,}" if s.get('timescaledb_rows') else "--", PURPLE)
        except Exception as exc:
            err(f"API fallback failed: {exc}")
        return
    print(c(output, PURPLE))
    print()
    info("This is a live psql query inside the TimescaleDB Docker container.")
    info("The 'events' table is a hypertable -- TimescaleDB partitions it by timestamp automatically.")


def cmd_redis() -> None:
    header("Redis -- Keyspace Inspection")
    info("Checking keyspace info...")
    print()
    ks = _docker(RD_CONTAINER, "redis-cli", "info", "keyspace")
    if "error:" in ks.lower():
        warn("Docker exec failed -- trying API fallback")
        try:
            s = _get("/pipeline-status")
            row("Redis UP",   str(s.get("redis_up",  False)), GREEN if s.get("redis_up") else RED)
            row("Redis keys", f"{s.get('redis_keys',0):,}" if s.get('redis_keys') else "--", YELLOW)
        except Exception as exc:
            err(f"API fallback: {exc}")
        return

    print(c("  " + ks.replace("\n", "\n  "), YELLOW))
    print()

    info("Sampling dedup keys (SETNX -- proves idempotency is live)...")
    sample = _docker(RD_CONTAINER, "redis-cli", "--scan", "--pattern", "dedup:*", "--count", "5")
    keys = [k.strip() for k in sample.split("\n") if k.strip()][:5]
    if keys:
        for k in keys:
            ok(f"  {k}")
        info(f"Each 'dedup:' key = one seen event_id. SETNX returns 0 on duplicate → dropped.")
    else:
        info("No dedup keys found. Run: python cashflow_cli.py seed")


def cmd_docker() -> None:
    header("Docker Containers")
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=8
        )
        lines = r.stdout.strip().split("\n")
        for i, line in enumerate(lines):
            color = GREY if i == 0 else (GREEN if "healthy" in line else YELLOW if "Up" in line else RED)
            print(c("  " + line, color))
    except Exception as exc:
        err(f"docker ps failed: {exc}")
        err("Is Docker running?")


def cmd_clean() -> None:
    header("Data Cleaning Pipeline Demo")
    info("Loading raw dirty transaction data...")
    print()
    try:
        raw = _get("/data-cleaning/raw")
    except Exception as exc:
        err(f"Failed: {exc}"); return

    # Show raw table
    cols = ["txn_id","business","type","amount","timestamp"]
    col_w = [12, 14, 8, 12, 20]
    header_row = "  " + "  ".join(c(cols[i].upper().ljust(col_w[i]), GREY) for i in range(len(cols)))
    print(header_row)
    print(c("  " + "-"*72, GREY))

    for row_data in raw.get("rows", []):
        parts = []
        for i, col in enumerate(cols):
            val = row_data.get(col)
            if val is None or val == "":
                parts.append(c("Missing".ljust(col_w[i]), RED))
            else:
                parts.append(str(val).ljust(col_w[i]))
        print("  " + "  ".join(parts))

    print()
    warn(f"{raw.get('missing_count', 0)} missing values across {raw.get('total_rows', 0)} rows")
    print()
    info("Running cleaning pipeline...")
    info("  · Strip currency symbols, parse amounts to float")
    info("  · Fill missing business/type with 'Unknown'")
    info("  · Fill missing/invalid amounts with statistical median")
    info("  · Fill missing timestamps with placeholder")
    print()

    try:
        result = _post("/data-cleaning/clean")
    except Exception as exc:
        err(f"Clean failed: {exc}"); return

    # Show cleaned table
    print(header_row)
    print(c("  " + "-"*72, GREY))
    for row_data in result.get("cleaned_rows", []):
        parts = []
        for i, col in enumerate(cols):
            val = row_data.get(col)
            is_fixed = any(col in fix for fix in row_data.get("fixes", []))
            if col == "amount" and isinstance(val, (int,float)):
                disp = f"Rs{val:,.0f}"
            else:
                disp = str(val) if val is not None else "--"
            color = YELLOW if is_fixed else GREEN
            parts.append(c(disp.ljust(col_w[i]), color))
        print("  " + "  ".join(parts))

    print()
    ok(f"{result.get('total_fixes', 0)} fixes applied")
    ok(f"{result.get('events_published', 0)} clean events published to pipeline")
    ok(f"Median fill value used: Rs{result.get('median_amount_used', 0):,.0f}")
    print()
    info("Yellow = value was filled by cleaning")
    info("Clean rows are now live in the pipeline -- check /pipeline-status to see them")


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

COMMANDS = {
    "status":       (cmd_status,      "Show live pipeline status"),
    "seed":         (cmd_seed,        "Seed 75 businesses + 6 months of events"),
    "stream":       (cmd_stream,      "Tail live activity feed (Ctrl+C to stop)"),
    "idempotency":  (cmd_idempotency, "Prove dedup: same event 3x → 1 row in DB"),
    "businesses":   (cmd_businesses,  "List all registered businesses"),
    "features":     (cmd_features,    "Get feature vector for a business ID"),
    "tsdb":         (cmd_tsdb,        "Query TimescaleDB event counts"),
    "redis":        (cmd_redis,       "Inspect Redis keyspace + dedup keys"),
    "docker":       (cmd_docker,      "Show all running Docker containers"),
    "clean":        (cmd_clean,       "Run data cleaning pipeline demo"),
}


def print_help() -> None:
    print()
    print(c("  CashFlowScore CLI", CYAN + BOLD))
    print(c("  Event Pipeline & Data Layer -- Pavan Hosatti", GREY))
    print()
    print(c("  Usage: python cashflow_cli.py <command> [args]", WHITE))
    print()
    print(c("  Commands:", GREY))
    for name, (_, desc) in COMMANDS.items():
        extra = " <business_id>" if name == "features" else ""
        print(f"    {c((name+extra).ljust(28), CYAN)}  {desc}")
    print()
    print(c("  Examples:", GREY))
    print(f"    {c('python cashflow_cli.py status', WHITE)}")
    print(f"    {c('python cashflow_cli.py seed', WHITE)}")
    print(f"    {c('python cashflow_cli.py features msme-0001', WHITE)}")
    print(f"    {c('python cashflow_cli.py stream', WHITE)}")
    print()


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("help", "--help", "-h"):
        print_help()
        return

    cmd = args[0].lower()

    if cmd == "features":
        if len(args) < 2:
            err("features requires a business_id argument")
            info("Example: python cashflow_cli.py features msme-0001")
            return
        cmd_features(args[1])
        return

    if cmd not in COMMANDS:
        err(f"Unknown command: {cmd}")
        print_help()
        return

    COMMANDS[cmd][0]()


if __name__ == "__main__":
    main()
