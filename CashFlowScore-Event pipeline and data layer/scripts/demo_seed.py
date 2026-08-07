import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEMO_DB = PROJECT_ROOT / "data" / "pipeline.db"
if DEMO_DB.exists():
    DEMO_DB.unlink()

from app.pipeline import build_pipeline


def main() -> None:
    pipeline = build_pipeline()
    summary = pipeline.seed_demo_data(count=20, seed=42, months=4)
    pipeline.wait_until_idle(timeout_seconds=10)
    print(summary)
    print(pipeline.snapshot())
    print(pipeline.get_features("msme-0001"))


if __name__ == "__main__":
    main()
