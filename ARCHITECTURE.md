# CashFlowScore — System Architecture

## Overview

CashFlowScore is a **four-service distributed system** that ingests live financial events, computes behavioral features, scores businesses using a machine learning model, and presents results through an interactive dashboard. Each service is independently deployable and communicates over HTTP.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                     │
│         UPI Transactions · Bank Statements · GST Filings · Bounces           │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │ POST /events/publish
                                 │ POST /transactions/bulk
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SERVICE 1 — EVENT PIPELINE  (port 8000)                    │
│                                                                               │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────────────────┐  │
│  │  FastAPI     │───▶│  InMemoryEventBus │───▶│  Ingestion Worker (thread)  │  │
│  │  API Layer  │    │  (Kafka-mirrored) │    │  + Stress Worker (thread)   │  │
│  └─────────────┘    └──────────────────┘    └────────────┬────────────────┘  │
│                                                          │                   │
│  ┌──────────────────────────────────────────────────────▼─────────────────┐  │
│  │                        PERSISTENCE LAYER                                │  │
│  │                                                                         │  │
│  │  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │  │
│  │  │  Redpanda       │  │   TimescaleDB     │  │  Redis               │   │  │
│  │  │  (Kafka API)    │  │   (Hypertable)    │  │  SETNX Dedup         │   │  │
│  │  │  port 9092      │  │   port 5432       │  │  Feature Cache 15m   │   │  │
│  │  │  Topics:        │  │   Table: events   │  │  port 6379           │   │  │
│  │  │  txn.upi        │  │   Auto-partitioned│  └──────────────────────┘   │  │
│  │  │  txn.bank       │  │   by timestamp    │                             │  │
│  │  │  gst.filing     │  └──────────────────┘                             │  │
│  │  │  cash.withdraw  │                                                    │  │
│  │  └────────────────┘                                                    │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                      FEATURE ENGINEERING                                 │  │
│  │  Computes 11 features from raw events across 30/90/180/365-day windows  │  │
│  │  monthly_upi_volume · gst_filing_regularity · bounce_frequency · etc.   │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ GET /features/{business_id}
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      SERVICE 2 — ML API  (port 8001)                          │
│                                                                               │
│  ┌──────────────────┐   ┌──────────────────────────────────────────────────┐  │
│  │  Feature         │   │  XGBoost Inference                               │  │
│  │  Resolution      │──▶│  model/xgb_model.json                           │  │
│  │  (direct or      │   │  Vectorized batch scoring                        │  │
│  │   via pipeline)  │   │  < 100ms per business                           │  │
│  └──────────────────┘   └────────────────────┬─────────────────────────────┘  │
│                                              │                               │
│                         ┌────────────────────▼─────────────────────────────┐  │
│                         │  SHAP Explainability                              │  │
│                         │  TreeExplainer on XGBoost                        │  │
│                         │  Top-3 reason codes per decision                 │  │
│                         │  Plain-English labels for loan officers           │  │
│                         └────────────────────┬─────────────────────────────┘  │
│                                              │                               │
│                         ┌────────────────────▼─────────────────────────────┐  │
│                         │  Redis Response Cache                             │  │
│                         │  Key: JSON hash of feature vector                │  │
│                         │  Serves repeated scores from cache               │  │
│                         └──────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ /score  /score-batch
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SERVICE 3 — GATEWAY API  (port 8002)                       │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  FastAPI + CORS + Bearer API Key Auth                                 │    │
│  │                                                                       │    │
│  │  /businesses      → proxies pipeline  → portfolio view               │    │
│  │  /score           → proxies ML API    → single business score        │    │
│  │  /score-batch     → upload Excel → ML batch → Excel report download  │    │
│  │  /pipeline-stats  → proxies pipeline status                          │    │
│  │  /pipeline        → polls Redis, TimescaleDB, Redpanda, ML health    │    │
│  │  /diagnostics     → runs live Docker commands (rpk, psql, redis-cli) │    │
│  │  /data-cleaning/* → proxies pipeline data cleaning endpoints         │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Fallback: heuristic scoring engine (no ML dependency required)              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ HTTP REST
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SERVICE 4 — FRONTEND  (port 5173)                          │
│                                                                               │
│  React 18 + Vite + Tailwind CSS                                              │
│                                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │  Hero Section   │  │  Portfolio Scorer │  │  Live Kafka Event Feed      │  │
│  │  Live metrics   │  │  Upload CSV/XLSX  │  │  Real-time activity ticker  │  │
│  │  System status  │  │  Score 1,000 biz  │  │  Stress flag alerts         │  │
│  │  Infrastructure │  │  Download report  │  │  Queue depth gauge          │  │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │  Data Cleaning  │  │  Live Proof       │  │  Comparison Table           │  │
│  │  Demo (8 rows)  │  │  Terminal buttons │  │  CashFlowScore vs CIBIL     │  │
│  │  Before/After   │  │  rpk / psql /     │  │  Feature signal analysis    │  │
│  │  Heatmap viz    │  │  redis-cli live   │  │                             │  │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow — Single Business Score

```
1. Business registers via POST /businesses/register
   → BusinessProfile stored in SQLite / TimescaleDB

2. Financial events arrive via POST /transactions/bulk
   → Events published to InMemoryEventBus (mirrors Kafka topics)
   → Ingestion worker persists to TimescaleDB hypertable
   → Dedup worker checks Redis SETNX (prevents duplicate processing)
   → Stress worker flags bounces and large outflows

3. GET /features/{business_id} called by ML API
   → Redis cache checked (15-min TTL)
   → Cache hit: feature vector returned in <1ms
   → Cache miss: events queried from TimescaleDB
     → Features computed across 30/90/180/365-day windows
     → Result cached in Redis

4. POST /score called on ML API
   → Feature vector resolved
   → Redis response cache checked (keyed on feature hash)
   → XGBoost inference: 11 features → credit score (0–100)
   → SHAP TreeExplainer: top-3 reason codes
   → Response cached in Redis

5. Score returned to Gateway → Frontend
   → Dashboard shows score, risk band, credit unlock amount
   → Loan officer can adjust sliders → live re-scoring via Redis cache
```

---

## Data Flow — Batch Portfolio Scoring

```
1. NBFC loan officer uploads Excel (1,000 rows) via Frontend

2. POST /score-batch → Gateway API
   → Reads CSV/XLSX rows
   → Forwards to ML /score-batch if ML service is online
   → ML service: vectorized XGBoost inference on all rows
   → Returns scored rows

3. Gateway generates Excel report
   → openpyxl formatted with color-coded credit scores
   → Columns: Business Name, Score, Status, Risk Band, Credit Unlocked, Reasons
   → Returned as base64-encoded download

4. Gateway publishes each scored row as a real event to pipeline
   → POST /transactions/bulk
   → Events land in TimescaleDB hypertable

5. Frontend triggers auto-download of scored Excel report
   → User sees summary stats: approved count, avg score, total credit unlocked
```

---

## Infrastructure Components

### Redpanda (Kafka-Compatible Event Bus)
- Topics: `txn.upi`, `txn.bank`, `gst.filing`, `cash.withdrawal`, `loan_applications`
- Acts as the durable, replicated event log for all financial transactions
- Admin UI: `http://localhost:8080`

### TimescaleDB
- PostgreSQL extension for time-series workloads
- `events` table is a hypertable, auto-partitioned by `timestamp`
- Enables sub-second queries across millions of financial events
- Used for feature computation and compliance audit trail

### Redis
- **Dedup**: `SETNX dedup:{event_id}` with expiry prevents duplicate event processing
- **Feature Cache**: `features:{business_id}` with 15-min TTL avoids recomputing features on every score request
- **Response Cache**: Full scoring responses cached by feature-hash key

### XGBoost Model
- Trained on synthetic MSME financial data (11 features)
- Gradient-boosted decision trees for tabular financial data
- Sub-100ms inference per business
- Model artifact: `CashFlowScore-ML/model/xgb_model.json`

### SHAP Explainability
- `shap.TreeExplainer` on the XGBoost model
- Computes SHAP values for each feature contribution
- Top-3 positive/negative contributors mapped to human-readable labels
- Required for regulatory explainability in NBFC lending context

---

## Port Reference

| Service | Port | Protocol |
|---|---|---|
| Event Pipeline API | 8000 | HTTP |
| ML Scoring API | 8001 | HTTP |
| Gateway API | 8002 | HTTP |
| Frontend Dev Server | 5173 | HTTP |
| Redpanda Kafka | 9092 | TCP |
| Redpanda Admin API | 9644 | HTTP |
| Redpanda Console UI | 8080 | HTTP |
| TimescaleDB | 5432 | TCP |
| Redis | 6379 | TCP |

---

## Deployment Architecture (Docker)

```
docker-compose.yml
├── pipeline      → pavanhosatti/cashflowscore-pipeline:latest
├── ml-api        → pavanhosatti/cashflowscore-ml:latest
├── gateway       → pavanhosatti/cashflowscore-gateway:latest
├── frontend      → pavanhosatti/cashflowscore-frontend:latest
└── [optional infrastructure containers via pipeline docker-compose]
    ├── redpanda
    ├── postgres (TimescaleDB)
    └── redis
```

Services communicate via Docker bridge network. Gateway connects to pipeline (`PAVAN_PIPELINE_URL`) and ML API (`AKAASH_SCORE_URL`) via environment variables.

---

## Resilience & Fallbacks

The system is designed to degrade gracefully when infrastructure services are unavailable:

- **Redis down** → Feature cache falls back to in-memory LRU with 15-min TTL
- **TimescaleDB down** → Events stored in SQLite fallback store
- **Redpanda down** → InMemoryEventBus handles event routing in-process
- **ML API down** → Gateway falls back to heuristic scoring engine (rule-based)
- **Pipeline down** → Gateway uses mock business data for demo
