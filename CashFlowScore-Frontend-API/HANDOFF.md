# Handoff Notes

## What I completed
- Built a React + Vite dashboard for the CashFlowScore demo.
- Implemented a FastAPI gateway with mock-first routes for businesses, detail, scoring, batch scoring, and status.
- Added a live-editable underwriting panel with instant score recalculation.
- Implemented a batch upload flow with progress, preview, summary stats, and downloadable CSV/XLSX output.
- Added a live status strip and activity feed that behave like an operations console.
- Verified the frontend build and gateway endpoints locally.

## What still depends on Pavan
- The gateway status route is wired to use a configurable upstream URL when provided, but the real Pavan service is not yet connected.
- The live pipeline status numbers should be replaced with the real Pavan payload when available.

## What still depends on Akaash
- The scoring endpoints are currently mock-backed unless the environment variables point to an upstream service.
- The real scoring and batch-scoring responses should be swapped in once Akaash provides the final API contract.

## How to integrate their services later
1. Set the environment variables in gateway/.env (or gateway/.env.example) to the upstream service URLs:
   - AKAASH_SCORE_URL
   - PAVAN_STATUS_URL
2. Restart the gateway so the new values are picked up.
3. Confirm that the upstream responses match the expected payload shapes used by the frontend.
4. Remove the mock fallback once the upstream services are stable.
