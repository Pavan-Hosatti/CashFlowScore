# CashFlowScore — Local Development Setup

This guide covers running the full stack locally without Docker for development. For the quickest path using Docker images, see [README.md](./README.md).

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend services |
| Node.js | 18+ | Frontend |
| npm | 9+ | Frontend package manager |
| Git | any | Version control |
| Docker Desktop | any | Optional (for Redpanda, TimescaleDB, Redis) |

---

## Repository Structure

```
cashflowscore-complete project/
├── CashFlowScore-Event pipeline and data layer/   ← Service 1 (port 8000)
├── CashFlowScore-ML/                              ← Service 2 (port 8001)
└── CashFlowScore-Frontend-API/
    ├── gateway/                                   ← Service 3 (port 8002)
    └── frontend/                                  ← Service 4 (port 5173)
```

Each service has its own virtual environment and requirements.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/Pavan-Hosatti/CashFlowScore.git
cd CashFlowScore
```

---

## Step 2 — Set Up the Event Pipeline (Service 1)

```bash
cd "CashFlowScore-Event pipeline and data layer"

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

The pipeline API is now running at **http://localhost:8000**

Verify: `http://localhost:8000/health`

---

## Step 3 — Set Up the ML API (Service 2)

Open a new terminal:

```bash
cd "CashFlowScore-ML"

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

The ML API is now running at **http://localhost:8001**

Verify: `http://localhost:8001/health`

---

## Step 4 — Set Up the Gateway API (Service 3)

Open a new terminal:

```bash
cd "CashFlowScore-Frontend-API/gateway"

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Point gateway at the running pipeline and ML services
$env:PAVAN_PIPELINE_URL = "http://127.0.0.1:8000"   # Windows PowerShell
$env:AKAASH_SCORE_URL   = "http://127.0.0.1:8001"   # Windows PowerShell

# macOS / Linux
export PAVAN_PIPELINE_URL=http://127.0.0.1:8000
export AKAASH_SCORE_URL=http://127.0.0.1:8001

uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

The Gateway API is now running at **http://localhost:8002**

Verify: `http://localhost:8002/health`

---

## Step 5 — Set Up the Frontend (Service 4)

Open a new terminal:

```bash
cd "CashFlowScore-Frontend-API/frontend"

npm install

npm run dev
```

The frontend is now running at **http://localhost:5173**

Open this URL in your browser to use the full dashboard.

---

## Step 6 — Seed Demo Data (Optional but Recommended)

With the pipeline running, seed 75 synthetic MSME businesses:

```bash
curl -X POST "http://localhost:8000/demo/bootstrap?count=75"
```

Or in PowerShell:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/demo/bootstrap?count=75" -Method POST
```

This generates realistic business profiles and 6 months of synthetic transactions.

---

## Step 7 — Start Infrastructure Services (Optional)

For the full production-equivalent experience with Redpanda, TimescaleDB, and Redis:

```bash
cd "CashFlowScore-Event pipeline and data layer"

docker-compose up -d
```

This starts:
- **Redpanda** on port 9092 (Kafka-compatible event bus)
- **TimescaleDB** on port 5432 (time-series database)
- **Redis** on port 6379 (dedup + feature cache)
- **Redpanda Console** on port 8080 (admin UI)

Without these services, the pipeline uses SQLite and in-memory fallbacks automatically.

---

## Verify Everything is Working

Once all 4 services are running:

| Check | URL |
|---|---|
| Frontend dashboard | http://localhost:5173 |
| Pipeline health | http://localhost:8000/health |
| ML API health | http://localhost:8001/health |
| Gateway health | http://localhost:8002/health |
| Live activity feed | http://localhost:8000/activity-feed |
| Pipeline status | http://localhost:8000/pipeline-status |

---

## Test a Single Score

```bash
curl -X POST http://localhost:8002/score \
  -H "Authorization: Bearer NBFC_TEST_KEY_123" \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "business_age_years": 5,
      "monthly_upi_volume": 350000,
      "monthly_bank_volume": 80000,
      "monthly_cash_volume": 10000,
      "gst_filing_regularity": 90,
      "gst_turnover": 1200000,
      "bounce_frequency": 0,
      "avg_monthly_balance": 150000,
      "income_stability": 80,
      "seasonality_score": 70,
      "loan_default_history": 0
    }
  }'
```

Expected response:
```json
{
  "score": 78,
  "top_reasons": ["Cash inflow is strong and recurring", "..."],
  "source": "xgboost"
}
```

---

## API Authentication

The Gateway API uses a static Bearer token for development:

```
Authorization: Bearer NBFC_TEST_KEY_123
```

Required on: `POST /score`, `POST /score-batch`, `POST /diagnostics`, `POST /data-cleaning/clean`

---

## Running the Data Cleaning Demo

1. Open the frontend at http://localhost:5173
2. Scroll to the **Data Cleaning Pipeline** section
3. Click **"Load Raw Dirty Data"** to see the synthetic dirty transactions
4. Click **"Run Cleaning Pipeline"** to clean and publish to the live stream
5. Watch the missing-value heatmap update and the activity feed show the new events

---

## Troubleshooting

**Port already in use:**
```bash
# Find what's using a port (Windows)
netstat -ano | findstr :8000

# Kill by PID
taskkill /PID <pid> /F
```

**ML model not loading:**
Check that `CashFlowScore-ML/model/xgb_model.json` exists. This is the trained model artifact.

**Gateway can't reach pipeline or ML:**
Make sure Services 1 and 2 are running before starting Service 3. Check the environment variables `PAVAN_PIPELINE_URL` and `AKAASH_SCORE_URL`.

**Redis / TimescaleDB / Redpanda not connecting:**
These are optional. The system falls back to in-memory and SQLite automatically. You will see warnings in the logs but the application continues to work.

**Frontend shows "—" for all metrics:**
This means the gateway is not reachable from the browser. Check that Service 3 (gateway) is running on port 8002.

---

## Environment Variables

| Variable | Service | Default | Description |
|---|---|---|---|
| `PAVAN_PIPELINE_URL` | Gateway | `http://127.0.0.1:8000` | Pipeline API base URL |
| `PAVAN_STATUS_URL` | Gateway | — | Pipeline status endpoint (legacy) |
| `AKAASH_SCORE_URL` | Gateway, ML | `http://127.0.0.1:8001` | ML API score endpoint |
| `PAVAN_FEATURES_URL` | ML | `http://127.0.0.1:8001` | Pipeline features endpoint |
| `REDIS_URL` | Pipeline, ML | — | Redis connection URL (e.g. `redis://localhost:6379`) |

---

## Service Startup Order

For best results, start services in this order:

```
1. docker-compose up -d          (infrastructure: Redpanda, TimescaleDB, Redis)
2. uvicorn app.api:app ...        (pipeline, port 8000)
3. uvicorn api.main:app ...       (ML API, port 8001)
4. uvicorn app.main:app ...       (gateway, port 8002)
5. npm run dev                    (frontend, port 5173)
```

Each service starts independently. Later services fall back gracefully if earlier ones are not yet up.
