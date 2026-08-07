import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEMO_DB = PROJECT_ROOT / "data" / "pipeline.db"
if DEMO_DB.exists():
    DEMO_DB.unlink()

from app.pipeline import build_pipeline
from app.api import dashboard_bootstrap


DUPLICATE_EVENT_ID = "evt-proof-1"
BUSINESS_ID = "msme-proof-1"


def main() -> None:
    pipeline = build_pipeline()

    print("[1] Bootstrapping demo data")
    summary = pipeline.seed_demo_data(count=20, seed=42, months=4)
    print(summary)

    print("[2] Waiting for queue drain")
    pipeline.wait_until_idle(timeout_seconds=15)
    print({"queue_depth": pipeline.snapshot()["queue_depth"]})

    print("[3] Registering proof business")
    pipeline.register_business(
        {
            "business_id": BUSINESS_ID,
            "business_age_years": 8,
            "monthly_upi_volume": 320000,
            "monthly_bank_volume": 950000,
            "monthly_cash_volume": 35000,
            "gst_filing_regularity": 92,
            "gst_turnover": 7200000,
            "bounce_frequency": 2,
            "avg_monthly_balance": 180000,
            "income_stability": 84,
            "seasonality_score": 76,
            "loan_default_history": 0,
        }
    )

    live_events = [
        {
            "event_id": "evt-proof-upi-1",
            "business_id": BUSINESS_ID,
            "topic": "txn.upi",
            "event_type": "credit",
            "amount": 180000,
            "timestamp": "2026-08-01T10:00:00+00:00",
            "direction": "inflow",
            "balance_after": 245000,
        },
        {
            "event_id": "evt-proof-bank-1",
            "business_id": BUSINESS_ID,
            "topic": "txn.bank",
            "event_type": "credit",
            "amount": 50000,
            "timestamp": "2026-08-01T11:00:00+00:00",
            "direction": "inflow",
            "balance_after": 295000,
        },
        {
            "event_id": "evt-proof-gst-1",
            "business_id": BUSINESS_ID,
            "topic": "gst.filing",
            "event_type": "filing",
            "amount": 420000,
            "timestamp": "2026-08-01T12:00:00+00:00",
            "direction": "neutral",
            "balance_after": 295000,
        },
    ]
    for event in live_events:
        pipeline.publish_event(event)

    print("[4] Replaying the same event three times to prove idempotency")
    replay_event = {
        "event_id": DUPLICATE_EVENT_ID,
        "business_id": BUSINESS_ID,
        "topic": "txn.bank",
        "event_type": "credit",
        "amount": 50000,
        "timestamp": "2026-08-01T12:00:00+00:00",
        "direction": "inflow",
        "balance_after": 230000,
    }
    for _ in range(3):
        pipeline.publish_event(replay_event)

    pipeline.wait_until_idle(timeout_seconds=10)
    print(pipeline.snapshot())

    print("[5] Feature payload for Akash")
    print(pipeline.get_features(BUSINESS_ID))

    print("[6] Recent infrastructure activity")
    print(pipeline.store.recent_activity(limit=10))

    print("[7] Dashboard-facing read models")
    print({"business_count": pipeline.store.count_businesses(), "event_count": pipeline.store.count_events()})
    print({"businesses": pipeline.store.list_business_ids()[:3]})
    print("[8] Judge-friendly dashboard bootstrap")
    bootstrap = dashboard_bootstrap(business_limit=3, activity_limit=5)
    print(bootstrap["headline"])
    print(bootstrap["hero_metrics"])
    print(bootstrap["judge_talk_track"][0])


if __name__ == "__main__":
    main()
