#!/usr/bin/env python3
"""
CashFlowScore -- Unified Project CLI
One command covers the whole project.

  python cashflow.py start              Start all services (Docker + APIs)
  python cashflow.py stop               Stop all services
  python cashflow.py status             Health check everything at once

  python cashflow.py pipeline seed      Seed demo data
  python cashflow.py pipeline stream    Tail live event feed
  python cashflow.py pipeline idempotency  Prove dedup live
  python cashflow.py pipeline tsdb      Live TimescaleDB query
  python cashflow.py pipeline redis     Redis keyspace + dedup keys
  python cashflow.py pipeline clean     Data cleaning demo

  python cashflow.py ml score <biz_id>  Score a business (live API)
  python cashflow.py ml score-offline <file.xlsx>  Score offline (no internet)
  python cashflow.py ml metrics         Model accuracy + AUC

  python cashflow.py demo               Open browser demo page
  python cashflow.py help               This message
"""
from __future__ import annotations
import io, json, os, subprocess, sys, time, uuid, webbrowser
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT     = Path(__file__).parent
ML_DIR   = ROOT / "CashFlowScore-ML"
PIPE_DIR = ROOT / "CashFlowScore-Event pipeline and data layer"
FE_DIR   = ROOT / "CashFlowScore-Frontend-API" / "frontend"

PIPE_API = os.getenv("CASHFLOW_API",    "http://localhost:8002")
ML_API   = os.getenv("CASHFLOW_ML_API", "http://localhost:8001")
FE_URL   = "http://localhost:3000"

PG = "cashflowscore-eventpipelineanddatalayer-postgres-1"
RD = "cashflowscore-eventpipelineanddatalayer-redis-1"
RP = "cashflowscore-eventpipelineanddatalayer-redpanda-1"

# ── colours ───────────────────────────────────────────────────────────────────
RST="\033[0m"; BOLD="\033[1m"; CYAN="\033[96m"; GRN="\033[92m"
YLW="\033[93m"; RED="\033[91m"; PRP="\033[95m"; GRY="\033[90m"; WHT="\033[97m"

def c(t, col): return f"{col}{t}{RST}"
def hdr(title):
    w = 64
    print(); print(c("="*w, GRY))
    print(c(f"  {title}", CYAN+BOLD))
    print(c("="*w, GRY)); print()
def ok(m):   print(c("  [OK]  ", GRN)  + m)
def warn(m): print(c("  [!!]  ", YLW)  + m)
def fail(m): print(c("  [XX]  ", RED)  + m)
def info(m): print(c("  [..]  ", GRY)  + m)
def kv(k, v, vc=WHT):
    print(f"  {c(str(k).ljust(30), GRY)} {c(str(v), vc)}")

# ── stdlib HTTP (no pip install needed) ───────────────────────────────────────
import urllib.request as _req, urllib.error as _uerr

def _get(base, path):
    try:
        with _req.urlopen(
            _req.Request(base+path, headers={"Accept":"application/json"}),
            timeout=5
        ) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)

def _post(base, path, body=None):
    data = json.dumps(body or {}).encode()
    req  = _req.Request(base+path, data=data,
                        headers={"Content-Type":"application/json"},
                        method="POST")
    try:
        with _req.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, str(e)

def _docker(*args):
    try:
        r = subprocess.run(["docker"]+list(args),
                           capture_output=True, text=True, timeout=12)
        return (r.stdout + r.stderr).strip(), r.returncode
    except Exception as e:
        return str(e), 1

def _docker_exec(container, *args):
    out, code = _docker("exec", container, *args)
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  INFRA COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

def cmd_start():
    hdr("Starting CashFlowScore -- All Services")

    # 1. Docker
    info("Starting Docker containers (Redpanda, TimescaleDB, Redis)...")
    out, code = _docker("compose", "up", "-d",
                        "--project-directory", str(PIPE_DIR))
    if code == 0:
        ok("Docker containers started")
    else:
        warn("docker compose returned non-zero -- containers may already be running")

    info("Waiting for containers to be healthy...")
    time.sleep(6)

    # 2. Probe containers
    for name, container in [("Redpanda", RP), ("TimescaleDB", PG), ("Redis", RD)]:
        probe = _docker_exec(container, "echo", "ok")
        if "ok" in probe:
            ok(f"{name} container ready")
        else:
            warn(f"{name} not responding yet -- give it 10 more seconds")

    # 3. Start pipeline API in background
    print()
    info("Starting Pipeline API on port 8002 (background)...")
    pipe_log = PIPE_DIR / "uvicorn_pipeline.log"
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.api:app",
         "--host", "0.0.0.0", "--port", "8002"],
        cwd=str(PIPE_DIR),
        stdout=open(pipe_log, "w"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # 4. Start ML API in background
    info("Starting ML Scoring API on port 8001 (background)...")
    # Use the venv python if available
    ml_python = ML_DIR / "venv" / "bin" / "python"
    if not ml_python.exists():
        ml_python = ML_DIR / "venv" / "Scripts" / "python.exe"
    if not ml_python.exists():
        ml_python = Path(sys.executable)
    ml_log = ML_DIR / "uvicorn_ml.log"
    subprocess.Popen(
        [str(ml_python), "-m", "uvicorn", "api.main:app",
         "--host", "0.0.0.0", "--port", "8001"],
        cwd=str(ML_DIR),
        stdout=open(ml_log, "w"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    # 5. Wait for APIs to be up
    info("Waiting for APIs to come up...")
    for attempt in range(15):
        time.sleep(2)
        s, _ = _get(PIPE_API, "/health")
        if s:
            ok("Pipeline API is up")
            break
        if attempt == 14:
            warn("Pipeline API taking longer than expected -- check uvicorn_pipeline.log")

    for attempt in range(10):
        time.sleep(1)
        m, _ = _get(ML_API, "/health")
        if m:
            ok("ML API is up")
            break
        if attempt == 9:
            warn("ML API not responding -- check uvicorn_ml.log")

    # 6. Seed data
    print()
    info("Seeding demo data (75 businesses, 6 months of events)...")
    r, e = _post(PIPE_API, "/demo/bootstrap?count=75&seed=42&months=6")
    if r:
        ok(f"{r.get('businesses_registered',0)} businesses registered, {r.get('events_queued',0):,} events queued")
        time.sleep(4)
    else:
        warn(f"Seed failed: {e}")

    # 7. Final status
    print()
    cmd_status()

    print()
    ok("System is ready. Run any command:")
    print(f"  {c('python cashflow.py pipeline tsdb', WHT)}")
    print(f"  {c('python cashflow.py pipeline idempotency', WHT)}")
    print(f"  {c('python cashflow.py ml score msme-0001', WHT)}")
    print(f"  {c('python cashflow.py demo', WHT)}")
    print(f"  {c('python cashflow.py help', WHT)}")


def cmd_stop():
    hdr("Stopping Docker containers")
    out, code = _docker("compose", "down",
                        "--project-directory", str(PIPE_DIR))
    if code == 0:
        ok("All containers stopped")
    else:
        warn(out[:200])


def cmd_status():
    hdr("CashFlowScore -- Full System Status")

    results = {}

    # Pipeline API
    s, e = _get(PIPE_API, "/pipeline-status")
    if s:
        ok(f"Pipeline API (:{PIPE_API.split(':')[-1]})  --  "
           f"events={s.get('events_processed',0):,}  "
           f"biz={s.get('business_count',0)}  "
           f"tsdb={s.get('timescaledb_rows','--')}  "
           f"redis_keys={s.get('redis_keys','--')}")
        results["pipeline"] = True
        # Services inside pipeline
        for svc, key in [("Redpanda","redpanda_up"),("TimescaleDB","postgres_up"),("Redis","redis_up")]:
            up = s.get(key)
            if up: ok(f"  {svc}")
            else:  warn(f"  {svc} -- DOWN")
    else:
        fail(f"Pipeline API unreachable  ({e})")
        fail("  Start it: cd \"CashFlowScore-Event pipeline and data layer\"")
        fail("            python -m uvicorn app.api:app --port 8002 --reload")
        results["pipeline"] = False

    print()

    # ML API
    m, e2 = _get(ML_API, "/health")
    if m:
        ok(f"ML Scoring API (:{ML_API.split(':')[-1]})  --  status={m.get('status')}")
        results["ml"] = True
    else:
        warn(f"ML API not running (port 8001)  -- offline scoring still works")
        results["ml"] = False

    print()

    # Docker containers
    dout, _ = _docker("ps", "--format",
                      "table {{.Names}}\t{{.Status}}")
    lines = [l for l in dout.split("\n") if "cashflow" in l.lower() and "Up" in l]
    if lines:
        ok(f"Docker: {len(lines)} container(s) running")
        for l in lines:
            info("  " + l.strip())
    else:
        warn("Docker: no CashFlowScore containers found -- run: python cashflow.py start")

    print()
    total = sum(results.values())
    if total == len(results):
        ok("All services UP -- ready for demo")
    else:
        warn(f"{total}/{len(results)} services reachable")

# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

def cmd_pipeline_seed():
    hdr("Pipeline -- Seeding Demo Data")
    info("Registering 75 synthetic MSME businesses, 6 months of events...")
    r, e = _post(PIPE_API, "/demo/bootstrap?count=75&seed=42&months=6")
    if e: fail(f"Seed failed: {e}"); return
    ok(f"{r.get('businesses_registered',0)} businesses registered")
    ok(f"{r.get('events_queued',0):,} events queued")
    info("Waiting 5s for workers to drain...")
    time.sleep(5)
    s, _ = _get(PIPE_API, "/pipeline-status")
    if s:
        kv("Events in DB",      f"{s.get('events_processed',0):,}",              GRN)
        kv("TimescaleDB rows",  f"{s.get('timescaledb_rows',0):,}" if s.get('timescaledb_rows') else "--", PRP)
        kv("Redis keys",        f"{s.get('redis_keys',0):,}"       if s.get('redis_keys')       else "--", YLW)


def cmd_pipeline_stream():
    hdr("Pipeline -- Live Activity Feed  (Ctrl+C to stop)")
    CAT = {
        "event_ingested":      (GRN,  ">>"),
        "stress_flagged":      (RED,  "!!"),
        "cache_hit":           (YLW,  "**"),
        "cache_miss":          (GRY,  "oo"),
        "feature_computed":    (PRP,  "##"),
        "duplicate_skipped":   (GRY,  "--"),
        "business_registered": (CYAN, "++"),
    }
    seen: set[str] = set()
    info("Polling every 2s. New events scroll below.\n")
    try:
        while True:
            data, _ = _get(PIPE_API, "/activity-feed?limit=60")
            if data:
                for ev in reversed(data.get("items", [])):
                    key = str(ev.get("created_at","")) + str(ev.get("event_id","")) + str(ev.get("message",""))
                    if key in seen: continue
                    seen.add(key)
                    cat   = ev.get("category","")
                    col, icon = CAT.get(cat, (CYAN,".."))
                    ts    = str(ev.get("created_at",""))[:19]
                    biz   = str(ev.get("business_id") or "SYSTEM")[:16].ljust(16)
                    msg   = str(ev.get("message", cat))[:65]
                    print(f"  {c(ts,GRY)}  {c(icon,col)}  {c(biz,GRY)}  {c(msg,col)}")
            time.sleep(2)
    except KeyboardInterrupt:
        print(); info("Stream stopped.")


def cmd_pipeline_idempotency():
    hdr("Pipeline -- Idempotency Proof")
    eid = f"idempotency-proof-{uuid.uuid4().hex[:8]}"
    evt = {"event_id":eid,"business_id":"msme-0001","topic":"txn.bank",
           "event_type":"credit","amount":99999,"direction":"inflow",
           "balance_after":199999,"timestamp":datetime.now(timezone.utc).isoformat()}
    info(f"Publishing event_id={eid[:28]}... three times")
    print()
    for i in range(1, 4):
        r, e = _post(PIPE_API, "/events/publish", evt)
        if e: fail(f"Publish #{i} failed: {e}"); return
        ok(f"Publish #{i}  accepted={r.get('accepted')}")
    info("Waiting 2s for workers...")
    time.sleep(2)
    s, _ = _get(PIPE_API, "/pipeline-status")
    dups = s.get("duplicate_events") or s.get("duplicate_event_count") or 0 if s else 0
    backend = s.get("dedup_backend","memory") if s else "unknown"
    print()
    ok(f"3 publishes -> {dups} duplicates caught by {backend}")
    ok("Only 1 row written to DB -- idempotency confirmed")


def cmd_pipeline_tsdb():
    hdr("Pipeline -- TimescaleDB Live Query")
    info("Running psql inside the Docker container...\n")
    out = _docker_exec(PG, "psql","-U","cashflow","-d","cashflowscore","-c",
        "SELECT topic, COUNT(*) AS events, "
        "MIN(timestamp)::date AS earliest, MAX(timestamp)::date AS latest "
        "FROM events GROUP BY topic ORDER BY events DESC;")
    if "error:" in out.lower() or "could not connect" in out.lower():
        warn("docker exec failed -- trying API fallback")
        s, _ = _get(PIPE_API, "/pipeline-status")
        if s:
            topics = s.get("event_count_by_topic", {})
            total  = sum(topics.values()) or 1
            for t, cnt in sorted(topics.items(), key=lambda x:-x[1]):
                bar = "|" * min(30, int(cnt/total*30))
                print(f"  {c(t.ljust(20),CYAN)}  {c(bar,PRP)}  {c(str(cnt),WHT)}")
        return
    print(c(out, PRP))
    print()
    info("'events' is a hypertable -- TimescaleDB partitions it by timestamp automatically")


def cmd_pipeline_redis():
    hdr("Pipeline -- Redis Keyspace")
    ks = _docker_exec(RD, "redis-cli","info","keyspace")
    if "error:" in ks.lower():
        s, _ = _get(PIPE_API, "/pipeline-status")
        if s:
            kv("Redis UP",    str(s.get("redis_up")), GRN if s.get("redis_up") else RED)
            kv("Redis keys",  str(s.get("redis_keys","--")), YLW)
        return
    print(c("  " + ks.replace("\n","\n  "), YLW))
    print()
    info("Sampling dedup keys (each = one seen event_id, set via SETNX)...")
    sample = _docker_exec(RD, "redis-cli","--scan","--pattern","dedup:*","--count","5")
    for k in [x.strip() for x in sample.split("\n") if x.strip()][:5]:
        ok(f"  {k}")
    info("SETNX returns 0 for existing key -> duplicate dropped, never written to DB")


def cmd_pipeline_clean():
    hdr("Pipeline -- Data Cleaning Demo")
    info("Loading raw dirty transaction data...\n")
    raw, e = _get(PIPE_API, "/data-cleaning/raw")
    if e: fail(f"Failed: {e}"); return
    cols = ["txn_id","business","type","amount","timestamp"]
    W    = [10,14,8,12,20]
    _print_table(cols, W, raw.get("rows",[]), phase="raw")
    print()
    warn(f"{raw.get('missing_count',0)} missing values across {raw.get('total_rows',0)} rows")
    print()
    info("Running cleaning pipeline (strip symbols, fill medians, fill nulls)...")
    res, e2 = _post(PIPE_API, "/data-cleaning/clean")
    if e2: fail(f"Clean failed: {e2}"); return
    print()
    _print_table(cols, W, res.get("cleaned_rows",[]), phase="clean")
    print()
    ok(f"{res.get('total_fixes',0)} fixes applied")
    ok(f"{res.get('events_published',0)} clean events published to pipeline")
    ok(f"Median fill: Rs{res.get('median_amount_used',0):,.0f}")


def _print_table(cols, widths, rows, phase):
    hline = "  " + "  ".join(c(cols[i].upper().ljust(widths[i]), GRY) for i in range(len(cols)))
    print(hline)
    print(c("  " + "-"*70, GRY))
    for row_d in rows:
        parts = []
        for i, col in enumerate(cols):
            val = row_d.get(col)
            is_fixed = any(col in f for f in (row_d.get("fixes") or []))
            if val is None or val == "":
                parts.append(c("Missing".ljust(widths[i]), RED))
            else:
                if col == "amount" and phase == "clean" and isinstance(val, (int,float)):
                    disp = f"Rs{val:,.0f}"
                else:
                    disp = str(val)
                col_c = YLW if is_fixed else WHT
                parts.append(c(disp.ljust(widths[i]), col_c))
        print("  " + "  ".join(parts))

# ─────────────────────────────────────────────────────────────────────────────
#  ML COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

def cmd_ml_score(biz_id: str):
    hdr(f"ML -- Scoring {biz_id}")

    # Step 1: get features from pipeline
    info("Fetching feature vector from pipeline API...")
    feat, e = _get(PIPE_API, f"/features/{biz_id}")
    if e:
        fail(f"Could not get features: {e}")
        info("Is the pipeline API running on port 8002?")
        return

    # Step 2: send to ML API
    info("Sending features to XGBoost scoring service...")
    payload = {"business_id": biz_id, "features": feat}
    result, e2 = _post(ML_API, "/score", payload)
    if e2:
        warn(f"ML API not reachable ({e2}) -- trying offline scoring instead")
        cmd_ml_score_offline_dict(feat, biz_id)
        return

    score   = result.get("score", result.get("credit_score", 0))
    reasons = result.get("top_reasons", result.get("reasons", []))
    decision = "APPROVED" if score >= 70 else "REVIEW" if score >= 55 else "REJECTED"
    dcol = GRN if score >= 70 else YLW if score >= 55 else RED

    print()
    kv("Business ID",  biz_id,    CYAN)
    kv("Credit Score", score,     dcol)
    kv("Decision",     decision,  dcol)
    print()
    info("Top reasons (SHAP explainability):")
    for r in (reasons if isinstance(reasons, list) else [reasons]):
        print(f"    {c('--', GRY)} {r}")


def cmd_ml_score_offline_dict(feat: dict, biz_id: str = "business"):
    """Score using the local model -- no API, no internet."""
    sys.path.insert(0, str(ML_DIR))
    try:
        from services.predictor import predict_score
        from services.explainability import generate_reasons
    except ImportError as e:
        fail(f"Cannot import ML services: {e}")
        info(f"Make sure you are in the right environment or the ML venv has deps installed.")
        return

    score, prob = predict_score(feat)
    try:
        reasons = generate_reasons(feat, score)
    except Exception:
        reasons = [f"Score: {score}/100 (SHAP not available in offline mode)"]

    decision = "APPROVED" if score >= 70 else "REVIEW" if score >= 55 else "REJECTED"
    dcol = GRN if score >= 70 else YLW if score >= 55 else RED

    print()
    kv("Business ID",  biz_id,    CYAN)
    kv("Credit Score", score,     dcol)
    kv("Probability",  f"{prob:.3f}", dcol)
    kv("Decision",     decision,  dcol)
    kv("Mode",         "OFFLINE -- no server, no internet", GRY)
    print()
    info("Top reasons:")
    for r in (reasons if isinstance(reasons, list) else [reasons]):
        print(f"    {c('--', GRY)} {r}")


def cmd_ml_score_offline(file_path: str):
    hdr("ML -- Offline Batch Scoring")
    p = Path(file_path)
    if not p.exists():
        fail(f"File not found: {file_path}")
        return

    info(f"Scoring {p.name} offline -- no internet, no server needed")
    # Delegate to the existing offline_score.py
    python = str(ML_DIR / "venv" / "bin" / "python")
    if not Path(python).exists():
        python = sys.executable   # fallback to current python
    script = str(ML_DIR / "offline" / "offline_score.py")
    os.chdir(str(ML_DIR))
    result = subprocess.run([python, script, str(p.resolve())],
                            capture_output=False, text=True)
    if result.returncode != 0:
        fail("Offline scoring failed")
    else:
        ok("Done. Output saved to CashFlowScore-ML/offline/scored_output.xlsx")


def cmd_ml_metrics():
    hdr("ML -- Model Metrics")
    metrics_path = ML_DIR / "model" / "metrics.json"
    if metrics_path.exists():
        m = json.loads(metrics_path.read_text())
        kv("Accuracy", f"{m.get('accuracy',0)*100:.1f}%", GRN)
        kv("AUC",      f"{m.get('auc',0):.4f}",           GRN)
        print()
        info("Model: XGBoost  |  Explainability: SHAP TreeExplainer")
        info("Trained on synthetic MSME profiles with realistic noise")
        info("No external API -- entire scoring path runs locally")
    else:
        fail(f"metrics.json not found at {metrics_path}")

# ─────────────────────────────────────────────────────────────────────────────
#  DEMO + HELP
# ─────────────────────────────────────────────────────────────────────────────

def cmd_connect(url: str):
    hdr("Connecting to CashFlowScore Server")
    url = url.rstrip("/")
    info(f"Testing connection to {url} ...")
    s, e = _get(url, "/health")
    if e:
        fail(f"Cannot reach {url}")
        fail(f"  Error: {e}")
        return
    ok(f"Connected to {url}")
    ok(f"  Status: {s.get('status')}")
    ok(f"  Events processed: {s.get('events_processed', '--')}")
    print()
    # Write a .env file so all future commands use this URL
    env_path = ROOT / ".cashflow_env"
    env_path.write_text(f"CASHFLOW_API={url}\nCASHFLOW_ML_API={url.replace('8002','8001')}\n")
    ok(f"Saved to {env_path}")
    info("All future commands now point to this server.")
    info(f"To reset back to localhost: delete {env_path}")


def _load_env():
    """Load saved server URL if exists."""
    env_path = ROOT / ".cashflow_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    """One command. Starts everything, seeds data, runs the full demo sequence."""
    hdr("CashFlowScore -- Full Demo Run")
    info("This will start all services, seed data, and run the full proof sequence.")
    print()
    cmd_start()
    print()
    hdr("Running full proof sequence")
    cmd_pipeline_tsdb()
    print()
    cmd_pipeline_redis()
    print()
    cmd_pipeline_idempotency()
    print()
    cmd_pipeline_clean()
    print()
    cmd_ml_metrics()
    print()
    info("Scoring msme-0005 via ML service...")
    cmd_ml_score("msme-0005")
    print()
    ok("Full demo sequence complete.")
    ok("Opening browser demo page...")
    time.sleep(1)
    cmd_demo()
    hdr("Opening Demo")
    demo_url = f"{PIPE_API}/demo"
    info(f"Opening {demo_url} in your browser...")
    webbrowser.open(demo_url)
    time.sleep(1)
    info(f"If browser did not open, go to: {demo_url}")
    info(f"Frontend dashboard: {FE_URL}")


def cmd_help():
    w = 64
    print()
    print(c("="*w, GRY))
    print(c("  CashFlowScore -- Unified CLI", CYAN+BOLD))
    print(c("  Event Pipeline + ML Scoring + Data Cleaning", GRY))
    print(c("="*w, GRY))
    print()
    sections = [
        ("INFRA", [
            ("run",                       "ONE COMMAND -- start everything + run full demo"),
            ("start",                     "Start Docker + both APIs + seed data"),
            ("stop",                      "Stop all Docker containers"),
            ("status",                    "Health check every service at once"),
            ("connect <url>",             "Point CLI at a remote server instead of localhost"),
            ("demo",                      "Open live demo page in browser"),
        ]),
        ("PIPELINE  (Pavan)", [
            ("pipeline seed",             "Seed 75 businesses + 6 months of events"),
            ("pipeline stream",           "Tail live activity feed  (Ctrl+C to stop)"),
            ("pipeline idempotency",      "Publish same event 3x -- prove 1 row in DB"),
            ("pipeline tsdb",             "Live psql query on TimescaleDB hypertable"),
            ("pipeline redis",            "Redis keyspace + dedup key sample"),
            ("pipeline clean",            "Run data cleaning pipeline demo"),
        ]),
        ("ML  (Akaash)", [
            ("ml score <biz_id>",         "Score a business via live API + SHAP reasons"),
            ("ml score-offline <file>",   "Score Excel file -- zero internet, no server"),
            ("ml metrics",                "Show model AUC and accuracy"),
        ]),
    ]
    for section, cmds in sections:
        print(c(f"  {section}", YLW+BOLD))
        for cmd, desc in cmds:
            print(f"    {c(('python cashflow.py '+cmd).ljust(40), CYAN)}  {desc}")
        print()
    print(c("  Examples:", GRY))
    print(f"    {c('python cashflow.py start', WHT)}")
    print(f"    {c('python cashflow.py status', WHT)}")
    print(f"    {c('python cashflow.py pipeline seed', WHT)}")
    print(f"    {c('python cashflow.py pipeline idempotency', WHT)}")
    print(f"    {c('python cashflow.py ml score msme-0001', WHT)}")
    print(f"    {c('python cashflow.py ml score-offline data/sample_businesses.xlsx', WHT)}")
    print(f"    {c('python cashflow.py demo', WHT)}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("help","--help","-h"):
        cmd_help(); return

    top = args[0].lower()

    # Single-word commands
    if top == "start":   cmd_start();  return
    if top == "stop":    cmd_stop();   return
    if top == "status":  cmd_status(); return
    if top == "demo":    cmd_demo();   return
    if top == "run":     cmd_run();    return
    if top == "connect":
        if len(args) < 2:
            fail("Usage: python cashflow.py connect <server-url>")
            info("Example: python cashflow.py connect https://api.cashflowscore.in")
            return
        cmd_connect(args[1]); return

    # Two-word commands
    if len(args) < 2:
        fail(f"Unknown command: {top}")
        cmd_help(); return

    sub = args[1].lower()

    if top == "pipeline":
        dispatch = {
            "seed":         cmd_pipeline_seed,
            "stream":       cmd_pipeline_stream,
            "idempotency":  cmd_pipeline_idempotency,
            "tsdb":         cmd_pipeline_tsdb,
            "redis":        cmd_pipeline_redis,
            "clean":        cmd_pipeline_clean,
        }
        fn = dispatch.get(sub)
        if fn: fn()
        else:
            fail(f"Unknown pipeline command: {sub}")
            cmd_help()
        return

    if top == "ml":
        if sub == "metrics":
            cmd_ml_metrics(); return
        if sub == "score":
            if len(args) < 3:
                fail("Usage: python cashflow.py ml score <business_id>"); return
            cmd_ml_score(args[2]); return
        if sub == "score-offline":
            if len(args) < 3:
                fail("Usage: python cashflow.py ml score-offline <file.xlsx>"); return
            cmd_ml_score_offline(args[2]); return
        fail(f"Unknown ml command: {sub}")
        cmd_help(); return

    fail(f"Unknown command: {top}")
    cmd_help()

if __name__ == "__main__":
    _load_env()
    # Re-read env after loading saved config
    global PIPE_API, ML_API
    PIPE_API = os.getenv("CASHFLOW_API",    PIPE_API)
    ML_API   = os.getenv("CASHFLOW_ML_API", ML_API)
    main()
