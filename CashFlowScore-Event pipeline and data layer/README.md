# CashFlowScore Event Pipeline

This folder contains Pavan's event-ingestion and feature-engineering layer.

## What Pavan owns

- Kafka/Redpanda-style event intake.
- Idempotent ingestion into the database.
- Redis-style dedup and feature caching behavior.
- Feature engineering from collected transactions.
- Pipeline health and queue visibility for the dashboard.

## No API keys needed

- This layer does not call any external AI or credit APIs.
- Kafka/Redpanda, Redis, and Postgres are local infrastructure services.
- If Docker is available, those services run in containers on your laptop.
- If Docker is not available, the code falls back to the local-first in-process demo path using the same endpoint and feature contract.
- The feature cache uses Redis when available, but it also works in memory so the demo still runs on a bad venue machine.

## Build order

1. Stand up the transport and storage layer.
2. Register MSME profiles before publishing events.
3. Stream or bulk-ingest transaction events.
4. Let the ingestion worker persist raw events.
5. Let the stress-signal worker flag bounces and large outflows.
6. Compute the feature payload from stored events.
7. Expose `/features/{business_id}` to Akash.
8. Expose `/pipeline-status` to Nikita.
9. Use `/dashboard/bootstrap` for the first screen, then `/businesses` and `/businesses/{business_id}` for drill-downs.
10. Run the demo bootstrap script and verify the queue drains to zero.

## How startup works

1. `start_demo.ps1` checks whether Docker is available.
2. If Docker works, it starts Redpanda, Redis, and Postgres with `docker compose`.
3. The simulator generates synthetic UPI, bank, and GST events.
4. The ingestion worker writes raw events to the store with `event_id` deduplication.
5. The stress worker flags bounce events and large outflows once per unique event.
6. The feature service reads stored events and computes the 11-feature payload for Akash.
7. Nikita reads `/pipeline-status` and `/businesses` from the same pipeline state.
8. If Docker fails, the same scripts run the local proof path so the demo still works.

## Practical scripts

- `python scripts/check_services.py` probes the Redpanda, Redis, and Postgres ports.
- `python scripts/demo_seed.py` seeds the pipeline and prints a basic status snapshot.
- `python scripts/prove_system.py` runs the full proof path: seed, drain, replay duplicates, read features, and print dashboard-facing counts.
- `powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1 -Detach` starts the local stack and immediately runs the proof path.
- `powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1 -NoDocker` skips Docker and runs the local-first proof path only.
- `python -m app.simulator --help` shows the live-event simulator options.
- `python -m app.simulator --continuous` emits a bounded live-style stream with pauses.

## What this slice does

- Generates synthetic MSME event streams.
- Ingests events through a two-consumer pipeline.
- Deduplicates by `event_id` at the database layer.
- Computes the exact feature JSON Akash's model expects.
- Exposes `/transactions/ingest`, `/transactions/bulk`, `/features/{business_id}`, `/pipeline-status`, and `/contracts/features` for integration.
- Also exposes `/businesses`, `/businesses/{business_id}`, and `/transactions/{business_id}` for dashboard list/detail/timeline views.
- Exposes `/activity-feed` and `/demo-story` so you can show judges the backend movement and the product storyline, not just raw tables.

## Why this is system-design level

- The event stream is separate from the feature service.
- The store is the source of truth, not the API layer.
- Redis-style cache behavior is modeled with a TTL feature cache that uses Redis when `REDIS_URL` is set and falls back to local memory if Redis is unavailable.
- The contract is stable so Akash can consume it without guessing field names.
- The API shape leaves room for a real Redpanda/Redis/Postgres swap without changing the caller contract.

## What each service does

- Redpanda carries the live transaction stream between producers and consumers.
- Redis is used for dedup/cache behavior when available: event_ids are claimed first, then SQLite/Postgres remains the durable backstop.
- Postgres/TimescaleDB stores the durable ledger of raw events and stress flags.
- The Python app is the ingestion, feature, and status layer on top of that storage.
- The dashboard and scoring service consume only the documented JSON contracts, not internal tables.
- `GET /pipeline-status` now reports `dedup_backend` and `cache_backend`, so you can tell whether the venue is running with Redis or the local fallback.
- `GET /activity-feed` shows a recent human-readable trail of what the backend did: pipeline start, business registration, event queued, event ingested, duplicate skipped, stress flagged, and feature cache activity.
- `GET /dashboard/bootstrap` returns one judge-friendly payload with the headline, hero metrics, story, activity feed, and featured businesses.

## Demo sequence

1. Start the pipeline service.
2. Seed 20 to 75 synthetic businesses.
3. Publish the generated events.
4. Wait for the ingestion queue to drain.
5. Open `/pipeline-status` and confirm event counters move.
6. Fetch `/features/{business_id}` for one business and confirm it matches Akash's expected schema.
7. Fetch `/businesses` for the portfolio view.
8. Fetch `/transactions/{business_id}` for drill-down.
9. Replay one event three times and verify only one stored row is created.
10. Keep the service alive while the dashboard reads the status strip.

## What to show a technical judge

1. Start Docker compose for the infrastructure services.
2. Run `python scripts/check_services.py` to show the ports are reachable.
3. Run `python scripts/prove_system.py` to prove queueing, dedup, and feature generation.
4. Point Nikita's dashboard at `/dashboard/bootstrap` for the hero section and `/businesses` for drill-down cards.
5. Hand the feature JSON to Akash's scoring service.
6. Open `/demo-story` when you want a short, human-readable explanation of what the backend is doing live.

## Feature contract for Akash

The `/features/{business_id}` endpoint returns only these keys:

- `business_age_years`
- `monthly_upi_volume`
- `monthly_bank_volume`
- `monthly_cash_volume`
- `gst_filing_regularity`
- `gst_turnover`
- `bounce_frequency`
- `avg_monthly_balance`
- `income_stability`
- `seasonality_score`
- `loan_default_history`

Akash can call `/score` with either that feature dict or just `business_id`; if he sends `business_id`, his service will fetch the payload from this endpoint.

## Local run

```bash
uvicorn app.api:app --reload
```

Bring up the infrastructure and run the proof flow on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1 -Detach
```

If Docker Desktop is unavailable or unstable at the venue, use the fallback:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1 -NoDocker
```

If you only want the containers:

```powershell
docker compose up -d
```

Seed demo data:

```bash
python scripts/demo_seed.py
```

## Integration notes

- Akash's scoring service can call `GET /features/{business_id}` directly.
- The status strip can poll `GET /pipeline-status`.
- The dashboard can load `GET /dashboard/bootstrap` first, then use the embedded status, story, activity feed, and featured business cards.
- The dashboard or API gateway can use `POST /transactions/bulk` for replay or batch ingest.
- `GET /contracts/features` returns the locked feature schema in one place.
- `GET /businesses` and `GET /businesses/{business_id}` give Nikita list/detail data without coupling her UI to the store layer.
- The current implementation is local-first so it runs without Docker, but the schema and endpoint shapes are stable for a Redpanda/Redis/Postgres swap.

## Judge-facing proof points

- Idempotency: same `event_id` published three times creates one stored event.
- Live pipeline status: counters update from the in-memory workers.
- Feature contract: Akash sees the exact 11-feature schema.
- Dashboard support: list, detail, and transaction timeline endpoints exist.
