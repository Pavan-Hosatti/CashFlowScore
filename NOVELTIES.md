# CashFlowScore — Novelties & Technical Differentiators

## What Makes This Project Stand Out

CashFlowScore is not a wrapper around a pre-built credit scoring API. Every layer of the system was built from scratch with real engineering decisions. Here is what is genuinely novel about this project.

---

## 1. Alternative Data for Credit Scoring

**The insight:** India's 63 million MSMEs are "credit invisible" to traditional bureaus. They have no CIBIL score, no ITR for 3 years, and no collateral. But they do have rich behavioral signals.

**What we built:** A scoring system that uses UPI transaction volumes, GST filing regularity, cheque bounce history, and average monthly balances as primary credit signals. The model treats behavioral consistency as a proxy for creditworthiness, not historical debt.

**Why it matters:** This is how modern fintech companies like Khatabook, OkCredit, and BNPL lenders in Southeast Asia work. We built the same infrastructure from scratch.

---

## 2. Full Event-Driven Architecture (Not Just a REST API)

Most student projects at this level implement a simple CRUD API. We built a genuine event-driven system.

**What we built:**
- An `InMemoryEventBus` that mirrors the Kafka pub-sub model (topics, subscribers, queues)
- A dedicated ingestion worker thread that processes events asynchronously
- A separate stress detection worker that flags bounces and large outflows in real-time
- Idempotent event processing via Redis `SETNX` dedup — the same event can be submitted 100 times but will only be stored once

**Real infrastructure integration:**
- Redpanda (Kafka-compatible) as the durable event log on port 9092
- TimescaleDB hypertable as the persistent event store (auto-partitioned by timestamp)
- The system works with **or without** Docker infrastructure — falls back gracefully

---

## 3. Time-Windowed Feature Engineering

Standard ML pipelines receive pre-computed features. We compute features from raw events at query time.

**What we built:**
A `FeatureService` that computes 11 financial features across **four time windows** (30, 90, 180, 365 days) from raw event data stored in TimescaleDB:

- `monthly_upi_volume` — UPI inflow sum, last 30 days
- `gst_filing_regularity` — percentage of expected months with a GST event, last 180 days
- `income_stability` — coefficient of variation of monthly inflows (lower CV = more stable)
- `seasonality_score` — current month vs prior-period average (detects sudden drops)
- `bounce_frequency` — cheque/NACH bounce count, last 90 days

These are not static fields read from a database. They are computed dynamically from the event stream every time a score is requested (and then cached).

---

## 4. Two-Layer Caching Strategy

**Layer 1 — Feature Cache (Redis, 15-min TTL):**
Feature vectors are expensive to compute (requires TimescaleDB aggregate queries across potentially thousands of events). After the first computation, the result is cached in Redis. Re-scoring the same business within 15 minutes costs <1ms instead of a full database scan.

**Layer 2 — Response Cache (Redis, keyed on feature hash):**
The full ML response (score + reasons) is cached using a JSON hash of the feature vector as the key. When a loan officer adjusts a slider and re-submits the same values, the response is served from cache without touching the XGBoost model.

**Cache backend transparency:** The system detects whether Redis is available and falls back to an in-memory TTL cache with the same interface, with zero code changes required.

---

## 5. SHAP-Based Explainability (Regulatory Compliance)

In India, the RBI mandates that lenders explain credit rejections to applicants. Black-box models are not acceptable in regulated lending.

**What we built:**
- `shap.TreeExplainer` on the XGBoost model to compute per-feature SHAP values
- Feature contributions ranked by absolute SHAP value
- Top 3 contributors mapped to human-readable reason codes

Example output:
```json
{
  "score": 62,
  "top_reasons": [
    "Cash inflow is moderate and improving",
    "GST filing cadence is healthy",
    "Bounce frequency is manageable"
  ]
}
```

Every credit decision is auditable and explainable — not just a number.

---

## 6. Batch Portfolio Scoring at Scale

Individual scoring is useful for demos. What NBFCs actually need is portfolio-level scoring.

**What we built:**
- `POST /score-batch` accepts an Excel or CSV file with up to 1,000 businesses
- Vectorized XGBoost inference on all rows in a single pass
- Gateway generates a formatted Excel report using openpyxl:
  - Color-coded credit scores (green/amber/red)
  - Status column (Approved / Rejected)
  - Risk Band (Low / Medium / High)
  - Credit Unlock Amount (1.5× monthly UPI volume for approved businesses)
  - Top-3 reason codes per business
- Report returned as base64-encoded download in the API response
- All scored rows are simultaneously published as real events to the pipeline

**Performance:** 1,000 businesses scored and report generated in under 2 seconds.

---

## 7. Live Data Cleaning Pipeline

A common problem in MSME data: missing values, inconsistent formats, currency symbols in numeric fields.

**What we built:**
- `GET /data-cleaning/raw` — returns synthetic dirty data (null business names, "₹12,450" as strings, missing timestamps)
- `POST /data-cleaning/clean` — runs the cleaning pipeline:
  - Strips currency symbols and commas from amount fields
  - Fills missing business names with "Unknown"
  - Fills missing amounts with the statistical median of valid rows
  - Fills missing timestamps with a default value
  - Records exactly which fixes were applied to each row
  - Publishes all cleaned rows as real events to the pipeline
- Frontend shows a before/after table with color-coded cells (red = missing, amber = auto-filled, white = valid) and a missing-value heatmap

---

## 8. Interactive Live Proof System

Rather than claiming the infrastructure exists, we built a way to prove it.

**What we built:**
- Three "Execute in Terminal" buttons in the frontend
- Each button calls `POST /diagnostics` on the gateway
- Gateway executes the actual Docker command inside the running container:
  - `docker exec redpanda rpk cluster info` — proves Redpanda is live
  - `psql -c "SELECT count(*) FROM events;"` — proves TimescaleDB has real rows
  - `redis-cli info keyspace` — proves Redis is caching real keys
- The actual terminal output is returned and displayed in a simulated terminal window in the browser

This means any evaluator can click a button and see real system output — not a mock.

---

## 9. System Resilience by Design

**Graceful degradation at every layer:**

| Component | Failure Mode | Fallback |
|---|---|---|
| Redis unavailable | Feature cache miss on every request | In-memory LRU cache, same interface |
| TimescaleDB down | Event storage fails | SQLite fallback store |
| Redpanda down | Kafka publish fails | InMemoryEventBus handles routing |
| ML API down | Scoring request fails | Gateway heuristic scoring engine |
| Pipeline down | Business data unavailable | Gateway mock data for demo |

The system never crashes hard. Every failure path has been handled explicitly.

---

## 10. Single-Command Deployment

The entire system — 4 application services + 3 infrastructure services — is orchestrated in a single `docker-compose.yml`. Any laptop with Docker Desktop can run the full production-equivalent stack with one command.

All 4 application images are published to Docker Hub (`pavanhosatti/*`) and can be pulled and run anywhere without any code or dependency setup.

---

## Summary

| What Most Projects Do | What CashFlowScore Does |
|---|---|
| Static ML model with preloaded data | Live feature computation from event stream |
| Single API endpoint | 4-service distributed architecture |
| No caching | Two-layer Redis caching (features + responses) |
| Black-box scores | SHAP explainability on every decision |
| Manual setup required | One-command Docker deployment |
| Fake infrastructure claims | Live terminal proof from running containers |
| CSV scoring only | Real-time event ingestion + batch portfolio |
| No data quality handling | Automated data cleaning pipeline with audit trail |
