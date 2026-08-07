import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEMO_DB = PROJECT_ROOT / "data" / "pipeline.db"
if DEMO_DB.exists():
    DEMO_DB.unlink()

from app.pipeline import build_pipeline


DEMO_BUSINESS_ID = "msme-0001"


def main() -> None:
    pipeline = build_pipeline()
    print("[1/4] Seeding demo businesses and transactions...")
    summary = pipeline.seed_demo_data(count=20, seed=42, months=4)
    print(summary)

    print("[2/4] Waiting for ingestion and stress workers to drain the queue...")
    pipeline.wait_until_idle(timeout_seconds=15)
    print({"queue_depth": pipeline.snapshot()["queue_depth"]})

    print("[3/4] Pipeline status snapshot...")
    print(pipeline.snapshot())

    print("[4/4] Feature contract for Akash...")
    print(pipeline.get_features(DEMO_BUSINESS_ID))


if __name__ == "__main__":
    main()
