# CashFlowScore

## Project overview
CashFlowScore is a mock-first underwriting demo that combines a React dashboard with a FastAPI gateway. The experience is designed to feel like a real bank-operations control room for reviewing businesses, editing underwriting inputs, and scoring batches of records.

## Features completed
- Portfolio summary cards for total scored, approved, rejected, and unlocked credit.
- Business table view with pagination at 50 rows per page.
- Business detail panel with live-editable underwriting inputs and instant score updates.
- Batch scoring workflow with CSV/XLSX upload, progress feedback, preview rows, summary stats, and downloadable output.
- Live status strip with events processed, queue depth, cache hit rate, and service health indicators.
- Browser-safe gateway integration so the React frontend can call the backend from the local Vite dev server.

## Folder structure
- frontend/ — React + Vite dashboard and styling assets
- gateway/ — FastAPI backend, mock data, and batch verification helper
- PROJECT_STRUCTURE.md — repository tree summary
- HANDOFF.md — integration and handoff notes

## Installation
### Frontend
1. cd frontend
2. npm install

### Gateway
1. cd gateway
2. pip install -r requirements.txt
3. Optional: copy .env.example to .env and set upstream URLs if you want to test against real services.

## Run commands
### Backend
- cd gateway
- uvicorn app.main:app --host 127.0.0.1 --port 8000

### Frontend
- cd frontend
- npm run dev

### Build verification
- cd frontend
- npm run build

## Pending backend integrations
- Pavan: the status route can be wired to the real pipeline-status endpoint once the service is available.
- Akaash: the scoring and batch-scoring routes can be wired to the real scoring service once the API contract is available.
