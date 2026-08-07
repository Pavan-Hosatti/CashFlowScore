# CashFlowScore

**Real-time ML credit scoring infrastructure for India's underserved MSMEs.**

---

## The Problem

63 million micro and small businesses in India have no credit history, no collateral, and no CIBIL score. Traditional lenders reject them outright. They are forced into predatory informal lending at 36–60% APR.

CashFlowScore solves this by scoring creditworthiness from **live behavioral data** — UPI transaction volumes, GST filing regularity, and cheque bounce history — not from historical debt records that most MSMEs simply don't have.

---

## What It Does

- Ingests live financial events (UPI, bank, GST, bounces) via a Kafka-compatible event stream
- Computes 11 financial features per business in real-time
- Scores each business using a trained **XGBoost model** in under 100ms
- Explains every decision with **SHAP-based reason codes** in plain English
- Lets NBFC loan officers upload a 1,000-business portfolio Excel and get a fully-scored downloadable report in under 2 seconds

---

## Architecture Overview

```
NBFC Upload / Live Events
         │
         ▼
  ┌─────────────────────────────────────────────────────────┐
  │              Event Pipeline  (port 8000)                 │
  │   Redpanda (Kafka) → Dedup (Redis SETNX) → TimescaleDB  │
  │   Feature Engineering → Feature Cache (Redis, 15m TTL)  │
  └──────────────────────┬──────────────────────────────────┘
                         │  /features/{business_id}
                         ▼
  ┌──────────────────────────────────────────┐
  │         ML Scoring API  (port 8001)       │
  │   XGBoost Inference + SHAP Explainability │
  │   Redis Response Cache                    │
  └──────────────────┬───────────────────────┘
                     │  /score  /score-batch
                     ▼
  ┌──────────────────────────────────────────┐
  │         Gateway API  (port 8002)          │
  │   FastAPI · CORS · API Key Auth           │
  │   Batch Excel → Score → Excel Report      │
  └──────────────────┬───────────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────────┐
  │         React Frontend  (port 5173)       │
  │   Live Dashboard · Portfolio Scorer       │
  │   Data Cleaning Demo · System Proof       │
  └──────────────────────────────────────────┘
```

---

## Repository Structure

```
CashFlowScore/
├── CashFlowScore-Event pipeline and data layer/   # Event ingestion + feature engine
│   ├── app/
│   │   ├── api.py          # FastAPI routes
│   │   ├── pipeline.py     # Core pipeline: bus, cache, feature service
│   │   ├── store.py        # SQLite + TimescaleDB + Redis persistence
│   │   ├── contracts.py    # Shared data contracts (11 features)
│   │   └── simulator.py    # Demo data generator
│   ├── scripts/            # Demo seed + verification scripts
│   ├── docker-compose.yml  # Redpanda + TimescaleDB + Redis
│   └── requirements.txt
│
├── CashFlowScore-ML/                              # ML scoring service
│   ├── api/
│   │   ├── main.py         # FastAPI: /score, /score-batch
│   │   └── scoring_service.py  # XGBoost + SHAP + Redis cache
│   ├── services/           # Predictor, explainability, batch scorer, cache
│   ├── model/
│   │   ├── xgb_model.json  # Trained XGBoost model
│   │   └── metrics.json    # Training metrics
│   └── requirements.txt
│
├── CashFlowScore-Frontend-API/                    # Frontend + Gateway
│   ├── gateway/
│   │   └── app/main.py     # FastAPI gateway: routing, batch scoring, diagnostics
│   └── frontend/
│       └── src/App.jsx     # React single-page application
│
├── docker-compose.yml      # Full-stack orchestration (all 5 services)
├── README.md
├── ARCHITECTURE.md
├── NOVELTIES.md
└── SETUP.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Event Streaming | Redpanda (Kafka-compatible) |
| Time-Series DB | TimescaleDB (PostgreSQL hypertable) |
| Feature Cache | Redis (SETNX dedup + 15-min TTL) |
| ML Model | XGBoost (gradient-boosted trees) |
| Explainability | SHAP (top-3 reason codes per decision) |
| Backend APIs | FastAPI (Python 3.11) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Containerization | Docker + Docker Compose |

---

## Quick Start (Docker)

The fastest way to run the entire stack. Requires Docker Desktop.

```bash
# Pull all images from Docker Hub
docker pull pavanhosatti/cashflowscore-pipeline:latest
docker pull pavanhosatti/cashflowscore-ml:latest
docker pull pavanhosatti/cashflowscore-gateway:latest
docker pull pavanhosatti/cashflowscore-frontend:latest

# Start all services
docker run -d -p 8000:8000 --name pipeline  pavanhosatti/cashflowscore-pipeline:latest
docker run -d -p 8001:8001 --name ml-api    pavanhosatti/cashflowscore-ml:latest
docker run -d -p 8002:8002 --name gateway   pavanhosatti/cashflowscore-gateway:latest
docker run -d -p 5173:5173 --name frontend  pavanhosatti/cashflowscore-frontend:latest
```

Then open **http://localhost:5173** in your browser.

See [SETUP.md](./SETUP.md) for local development setup.

---

## Docker Hub

All 4 images are published at:

| Service | Image |
|---|---|
| Event Pipeline | `pavanhosatti/cashflowscore-pipeline` |
| ML API | `pavanhosatti/cashflowscore-ml` |
| Gateway API | `pavanhosatti/cashflowscore-gateway` |
| Frontend | `pavanhosatti/cashflowscore-frontend` |

---

## API Reference

### Event Pipeline — `http://localhost:8000`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health + infrastructure status |
| `/pipeline-status` | GET | Full pipeline snapshot: queue depth, event counts, service status |
| `/businesses` | GET | All registered businesses with computed features |
| `/features/{id}` | GET | Feature vector for a single business (ML handoff contract) |
| `/events/publish` | POST | Publish a single financial event |
| `/transactions/bulk` | POST | Bulk ingest events |
| `/demo/bootstrap` | POST | Seed 75 synthetic MSME businesses |
| `/activity-feed` | GET | Live Kafka event stream |
| `/data-cleaning/raw` | GET | Sample dirty transaction data |
| `/data-cleaning/clean` | POST | Run cleaning pipeline + publish to stream |

### ML API — `http://localhost:8001`

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Model + Redis status |
| `/score` | POST | Score a single business (11-feature vector) |
| `/score-batch` | POST | Score a portfolio Excel file |

### Gateway API — `http://localhost:8002`

| Endpoint | Method | Description |
|---|---|---|
| `/businesses` | GET | Portfolio view (proxies pipeline) |
| `/score` | POST | Single score (proxies ML API) · API key required |
| `/score-batch` | POST | Batch portfolio scoring · API key required |
| `/status` | GET | Aggregated system status |
| `/pipeline-stats` | GET | Live pipeline metrics |
| `/pipeline` | GET | Full infrastructure health (Redis, TimescaleDB, Redpanda, ML) |
| `/diagnostics` | POST | Execute live Docker terminal commands |

---

## The Feature Contract

All scoring is based on these 11 features computed from live financial events:

| Feature | Description |
|---|---|
| `business_age_years` | Years since business registration |
| `monthly_upi_volume` | Total UPI inflows in last 30 days (₹) |
| `monthly_bank_volume` | Bank transaction volume in last 30 days (₹) |
| `monthly_cash_volume` | Cash withdrawal volume in last 30 days (₹) |
| `gst_filing_regularity` | Percentage of months with GST filing (0–100) |
| `gst_turnover` | Annual GST-declared revenue (₹) |
| `bounce_frequency` | Cheque/NACH bounces in last 90 days |
| `avg_monthly_balance` | Average end-of-day balance over 90 days (₹) |
| `income_stability` | Coefficient of variation of monthly inflows (0–100) |
| `seasonality_score` | Current month vs prior-month average ratio (0–100) |
| `loan_default_history` | Count of past loan defaults |

---

## Team

| Name | Module |
|---|---|
| Pavan Hosatti | Event Pipeline & Data Layer |
| Akaash | ML Scoring Engine |
| Nikita | Frontend & Gateway API |

---

## License

MIT
