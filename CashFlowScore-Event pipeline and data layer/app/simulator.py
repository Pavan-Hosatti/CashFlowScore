from __future__ import annotations

import argparse
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Dict, Iterable, Iterator, List, Sequence

from .contracts import BusinessProfile, RawEvent, clamp, utc_now_iso


@dataclass(frozen=True)
class GeneratedBundle:
    profile: BusinessProfile
    events: List[RawEvent]


def generate_business_profiles(count: int = 75, seed: int = 42) -> List[BusinessProfile]:
    rng = random.Random(seed)
    profiles: List[BusinessProfile] = []

    for index in range(count):
        business_id = f"msme-{index + 1:04d}"
        business_age_years = rng.randint(1, 20)
        monthly_upi_volume = rng.randint(150_000, 950_000)
        monthly_bank_volume = rng.randint(300_000, 5_000_000)
        monthly_cash_volume = rng.randint(0, 450_000)
        gst_filing_regularity = rng.randint(50, 100)
        gst_turnover = rng.randint(800_000, 50_000_000)
        bounce_frequency = rng.randint(0, 14)
        avg_monthly_balance = rng.randint(15_000, 2_000_000)
        income_stability = rng.randint(40, 100)
        seasonality_score = rng.randint(30, 100)
        loan_default_history = 1 if rng.random() < 0.12 else 0
        opening_balance = max(10_000, int(avg_monthly_balance * rng.uniform(0.6, 1.4)))
        target_monthly_growth = round(rng.uniform(-0.05, 0.18), 3)

        profiles.append(
            BusinessProfile(
                business_id=business_id,
                business_age_years=business_age_years,
                monthly_upi_volume=monthly_upi_volume,
                monthly_bank_volume=monthly_bank_volume,
                monthly_cash_volume=monthly_cash_volume,
                gst_filing_regularity=gst_filing_regularity,
                gst_turnover=gst_turnover,
                bounce_frequency=bounce_frequency,
                avg_monthly_balance=avg_monthly_balance,
                income_stability=income_stability,
                seasonality_score=seasonality_score,
                loan_default_history=loan_default_history,
                opening_balance=opening_balance,
                target_monthly_growth=target_monthly_growth,
            )
        )

    return profiles


def _month_offset(month_index: int) -> datetime:
    base = datetime.now(timezone.utc) - timedelta(days=30 * month_index)
    return base


def _event_time(month_index: int, slot_index: int, slot_count: int) -> datetime:
    month_start = _month_offset(month_index)
    minute_offset = int((slot_index + 1) * 24 * 60 / max(slot_count, 1))
    return month_start + timedelta(minutes=minute_offset)


def _build_event(
    business_id: str,
    topic: str,
    event_type: str,
    amount: float,
    timestamp: datetime,
    direction: str,
    balance_after: float,
    **metadata,
) -> RawEvent:
    return RawEvent(
        event_id=str(uuid.uuid4()),
        business_id=business_id,
        topic=topic,
        event_type=event_type,
        amount=round(float(amount), 2),
        timestamp=timestamp.isoformat(),
        direction=direction,
        balance_after=round(float(balance_after), 2),
        metadata=dict(metadata),
    )


def generate_history_events(profile: BusinessProfile, months: int = 6, seed: int = 42) -> List[RawEvent]:
    rng = random.Random(f"{seed}:{profile.business_id}")
    balance = float(profile.opening_balance)
    events: List[RawEvent] = []

    monthly_profiles = [
        ("txn.upi", "credit", profile.monthly_upi_volume, 6),
        ("txn.bank", "credit", profile.monthly_bank_volume, 5),
        ("cash.withdrawal", "cash_withdrawal", profile.monthly_cash_volume, 3),
    ]

    for month_index in range(months, 0, -1):
        for topic, event_type, monthly_amount, slot_count in monthly_profiles:
            if monthly_amount <= 0:
                continue
            split_count = max(1, int(slot_count + rng.randint(-1, 2)))
            chunk = monthly_amount / split_count
            for slot in range(split_count):
                variation = rng.uniform(0.82, 1.18)
                amount = max(1.0, chunk * variation)
                timestamp = _event_time(month_index, slot, split_count)
                direction = "inflow" if event_type == "credit" else "outflow"
                balance += amount if direction == "inflow" else -amount
                events.append(
                    _build_event(
                        business_id=profile.business_id,
                        topic=topic,
                        event_type=event_type,
                        amount=amount,
                        timestamp=timestamp,
                        direction=direction,
                        balance_after=balance,
                        month_index=month_index,
                    )
                )

        gst_amount = max(1.0, profile.gst_turnover / 12.0 * rng.uniform(0.9, 1.08))
        gst_time = _event_time(month_index, 1, 1)
        events.append(
            _build_event(
                business_id=profile.business_id,
                topic="gst.filing",
                event_type="filing",
                amount=gst_amount,
                timestamp=gst_time,
                direction="neutral",
                balance_after=balance,
                filing_month=month_index,
            )
        )

    bounce_count = max(0, profile.bounce_frequency)
    for bounce_index in range(bounce_count):
        month_index = rng.randint(1, months)
        timestamp = _event_time(month_index, bounce_index, max(bounce_count, 1))
        amount = rng.uniform(1500, 40000)
        balance -= amount
        events.append(
            _build_event(
                business_id=profile.business_id,
                topic="txn.bank",
                event_type="bounce",
                amount=amount,
                timestamp=timestamp,
                direction="outflow",
                balance_after=balance,
                bounce_index=bounce_index,
            )
        )

    events.sort(key=lambda event: event.timestamp)
    return events


def generate_demo_bundle(count: int = 75, seed: int = 42, months: int = 6) -> List[GeneratedBundle]:
    bundles: List[GeneratedBundle] = []
    for profile in generate_business_profiles(count=count, seed=seed):
        bundles.append(GeneratedBundle(profile=profile, events=generate_history_events(profile, months=months, seed=seed)))
    return bundles


def iter_live_events(
    count: int = 75,
    seed: int = 42,
    months: int = 6,
    events_per_tick: int = 1,
) -> Iterator[Dict[str, object]]:
    for bundle in generate_demo_bundle(count=count, seed=seed, months=months):
        for event in bundle.events:
            yield event.as_record()


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="CashFlowScore event simulator")
    parser.add_argument("--count", type=int, default=20, help="Number of businesses to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--months", type=int, default=4, help="Historical months to generate")
    parser.add_argument("--continuous", action="store_true", help="Emit events continuously with pauses")
    parser.add_argument("--interval", type=float, default=1.5, help="Seconds between continuous events")
    parser.add_argument("--limit", type=int, default=25, help="Max events to emit in continuous mode")
    args = parser.parse_args(argv)

    if args.continuous:
        emitted = 0
        for event in iter_live_events(count=args.count, seed=args.seed, months=args.months):
            print(event)
            emitted += 1
            if emitted >= args.limit:
                break
            sleep(args.interval)
    else:
        for event in iter_live_events(count=args.count, seed=args.seed, months=args.months):
            print(event)


if __name__ == "__main__":
    main()
