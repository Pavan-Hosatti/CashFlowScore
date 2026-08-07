from __future__ import annotations

import json
import os
import queue
import socket
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic
from typing import Any, Dict, List, Optional

from .contracts import FEATURE_COLUMNS, BusinessProfile, RawEvent, clamp
from .simulator import GeneratedBundle, generate_demo_bundle
from .store import PipelineStore

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None


@dataclass
class FeatureCache:
    ttl_seconds: int = 900
    _items: Dict[str, tuple[float, Dict[str, Any]]] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    redis_url: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_URL"))
    _redis_client: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.redis_url and redis is not None:
            try:
                self._redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self._redis_client.ping()
            except Exception:
                self._redis_client = None

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self._redis_client is not None:
            try:
                value = self._redis_client.get(key)
                if value is not None:
                    self.hits += 1
                    return json.loads(value)
            except Exception:
                self._redis_client = None

        now = monotonic()
        with self.lock:
            item = self._items.get(key)
            if item is None:
                self.misses += 1
                return None
            expires_at, value = item
            if expires_at < now:
                self._items.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return dict(value)

    def set(self, key: str, value: Dict[str, Any]) -> None:
        if self._redis_client is not None:
            try:
                self._redis_client.setex(key, self.ttl_seconds, json.dumps(value))
            except Exception:
                self._redis_client = None

        with self.lock:
            self._items[key] = (monotonic() + self.ttl_seconds, dict(value))

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total) if total else 0.0
            return {
                "cache_hit_rate": round(hit_rate, 3),
                "cache_hits": self.hits,
                "cache_misses": self.misses,
                "cache_size": len(self._items),
                "cache_backend": "redis" if self._redis_client is not None else "memory",
            }


class InMemoryEventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[queue.Queue]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, stream_name: str) -> queue.Queue:
        subscriber = queue.Queue()
        with self._lock:
            self._subscribers[stream_name].append(subscriber)
        return subscriber

    def publish(self, event: Dict[str, Any]) -> None:
        with self._lock:
            subscriber_lists = [list(subscribers) for subscribers in self._subscribers.values()]
        for subscriber_list in subscriber_lists:
            for subscriber in subscriber_list:
                subscriber.put(dict(event))

    def depth(self) -> int:
        with self._lock:
            return sum(subscriber.qsize() for subscribers in self._subscribers.values() for subscriber in subscribers)


@dataclass
class PipelineState:
    events_processed: int = 0
    duplicate_events: int = 0
    stress_flags: int = 0
    businesses_registered: int = 0
    last_event_at: Optional[str] = None
    stress_event_ids: set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def bump(self, field_name: str, amount: int = 1) -> None:
        with self.lock:
            current = getattr(self, field_name)
            setattr(self, field_name, current + amount)

    def set_last_event_at(self, value: str) -> None:
        with self.lock:
            self.last_event_at = value

    def mark_stress_event(self, event_id: str) -> bool:
        with self.lock:
            if event_id in self.stress_event_ids:
                return False
            self.stress_event_ids.add(event_id)
            return True

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "events_processed": self.events_processed,
                "duplicate_events": self.duplicate_events,
                "stress_flags": self.stress_flags,
                "businesses_registered": self.businesses_registered,
                "last_event_at": self.last_event_at,
            }


class FeatureService:
    def __init__(self, store: PipelineStore, cache: FeatureCache) -> None:
        self.store = store
        self.cache = cache

    def get_features(self, business_id: str) -> Dict[str, int]:
        cache_key = f"features:{business_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.store.record_activity("cache_hit", f"Feature cache hit for {business_id}", business_id=business_id)
            return cached

        profile_payload = self.store.get_business_profile(business_id)
        if profile_payload is None:
            raise KeyError(f"Unknown business_id: {business_id}")

        profile = BusinessProfile.from_mapping(profile_payload)
        events = self.store.list_events(business_id)
        features = self._compute_features(profile, events)
        self.cache.set(cache_key, features)
        self.store.record_activity("cache_miss", f"Feature cache miss for {business_id}", business_id=business_id)
        self.store.record_activity("feature_computed", f"Computed feature vector for {business_id}", business_id=business_id)
        return features

    def _compute_features(self, profile: BusinessProfile, events: List[Dict[str, Any]]) -> Dict[str, int]:
        if not events:
            return profile.as_feature_dict()

        now = datetime.now(timezone.utc)
        windows = {
            30: [event for event in events if self._within_days(event["timestamp"], now, 30)],
            90: [event for event in events if self._within_days(event["timestamp"], now, 90)],
            180: [event for event in events if self._within_days(event["timestamp"], now, 180)],
            365: [event for event in events if self._within_days(event["timestamp"], now, 365)],
        }

        monthly_upi_volume = self._sum_amount(windows[30], topic="txn.upi", direction="inflow")
        monthly_bank_volume = self._sum_amount(windows[30], topic="txn.bank", direction="inflow")
        monthly_cash_volume = self._sum_amount(windows[30], topic="cash.withdrawal", direction="outflow")
        gst_events_180 = [event for event in windows[180] if event["topic"] == "gst.filing"]
        gst_turnover = self._sum_amount(windows[365], topic="gst.filing")
        bounce_frequency = sum(1 for event in windows[90] if event["event_type"] == "bounce")
        avg_monthly_balance = self._average_balance(windows[90], profile.opening_balance)
        income_stability = self._income_stability(events, profile)
        seasonality_score = self._seasonality_score(windows[30], windows[90], profile)
        gst_filing_regularity = self._gst_regularity(gst_events_180)

        return {
            "business_age_years": int(profile.business_age_years),
            "monthly_upi_volume": int(round(monthly_upi_volume)),
            "monthly_bank_volume": int(round(monthly_bank_volume)),
            "monthly_cash_volume": int(round(monthly_cash_volume)),
            "gst_filing_regularity": int(round(gst_filing_regularity)),
            "gst_turnover": int(round(gst_turnover)),
            "bounce_frequency": int(round(bounce_frequency)),
            "avg_monthly_balance": int(round(avg_monthly_balance)),
            "income_stability": int(round(income_stability)),
            "seasonality_score": int(round(seasonality_score)),
            "loan_default_history": int(profile.loan_default_history),
        }

    @staticmethod
    def _within_days(timestamp: str, now: datetime, days: int) -> bool:
        event_time = datetime.fromisoformat(timestamp)
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        return (now - event_time).days <= days

    @staticmethod
    def _sum_amount(events: List[Dict[str, Any]], topic: str, direction: Optional[str] = None) -> float:
        total = 0.0
        for event in events:
            if event["topic"] != topic:
                continue
            if direction is not None and event["direction"] != direction:
                continue
            total += float(event["amount"])
        return total

    @staticmethod
    def _average_balance(events: List[Dict[str, Any]], fallback: float) -> float:
        balances = [float(event["balance_after"]) for event in events if event.get("balance_after") is not None]
        if not balances:
            return float(fallback)
        return sum(balances) / len(balances)

    @staticmethod
    def _income_stability(events: List[Dict[str, Any]], profile: BusinessProfile) -> float:
        month_buckets: Dict[str, float] = {}
        for event in events:
            if event["direction"] != "inflow":
                continue
            month_key = event["timestamp"][:7]
            month_buckets[month_key] = month_buckets.get(month_key, 0.0) + float(event["amount"])

        monthly_totals = [value for value in month_buckets.values() if value > 0]
        if len(monthly_totals) < 2:
            return float(profile.income_stability)

        mean = sum(monthly_totals) / len(monthly_totals)
        if mean <= 0:
            return float(profile.income_stability)
        variance = sum((value - mean) ** 2 for value in monthly_totals) / len(monthly_totals)
        variance = max(variance, 0.0)
        cv = (variance ** 0.5) / mean
        return clamp(100.0 - cv * 45.0, 0.0, 100.0)

    @staticmethod
    def _seasonality_score(recent_30: List[Dict[str, Any]], recent_90: List[Dict[str, Any]], profile: BusinessProfile) -> float:
        recent = sum(float(event["amount"]) for event in recent_30 if event["direction"] == "inflow")
        prior = sum(float(event["amount"]) for event in recent_90 if event["direction"] == "inflow") - recent
        prior_months = max(len({event["timestamp"][:7] for event in recent_90}) - 1, 1)
        prior_avg = prior / prior_months if prior_months else prior
        if prior_avg <= 0:
            return float(profile.seasonality_score)
        ratio = abs(recent - prior_avg) / prior_avg
        return clamp(100.0 - ratio * 100.0, 0.0, 100.0)

    @staticmethod
    def _gst_regularity(gst_events: List[Dict[str, Any]]) -> float:
        expected_months = max(1, len({event["timestamp"][:7] for event in gst_events}))
        filing_count = len(gst_events)
        return clamp((filing_count / expected_months) * 100.0, 0.0, 100.0)


class CashFlowPipeline:
    def __init__(self, store: PipelineStore | None = None) -> None:
        self.store = store or PipelineStore()
        self.bus = InMemoryEventBus()
        self.cache = FeatureCache(ttl_seconds=900)
        self.features = FeatureService(self.store, self.cache)
        self.state = PipelineState()
        self.ingestion_queue = self.bus.subscribe("ingestion")
        self.stress_queue = self.bus.subscribe("stress")
        self._workers_started = False
        self.store.record_activity("pipeline_started", f"Pipeline initialized with {self.cache.stats()['cache_backend']} cache")

    def start_workers(self) -> None:
        if self._workers_started:
            return
        self._workers_started = True
        threading.Thread(target=self._ingestion_worker, daemon=True).start()
        threading.Thread(target=self._stress_worker, daemon=True).start()

    def publish_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.bus.publish(event)
        self.store.record_activity(
            "event_queued",
            f"Queued {event.get('event_type')} from {event.get('topic')}",
            business_id=str(event.get("business_id")),
            event_id=str(event.get("event_id")),
        )
        return {"accepted": True, "event_id": event["event_id"]}

    def publish_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        accepted = 0
        for event in events:
            self.bus.publish(event)
            accepted += 1
        return {"accepted": accepted}

    def register_business(self, profile: BusinessProfile | Dict[str, Any]) -> None:
        self.store.register_business(profile)
        self.state.bump("businesses_registered")
        payload = profile.as_record() if isinstance(profile, BusinessProfile) else dict(profile)
        self.store.record_activity(
            "business_registered",
            f"Registered business {payload['business_id']}",
            business_id=str(payload["business_id"]),
        )

    def seed_demo_data(self, count: int = 75, seed: int = 42, months: int = 6) -> Dict[str, Any]:
        bundles = generate_demo_bundle(count=count, seed=seed, months=months)
        queued_events: List[Dict[str, Any]] = []
        for bundle in bundles:
            self.register_business(bundle.profile)
            for event in bundle.events:
                queued_events.append(event.as_record())
        self.publish_events(queued_events)
        return {
            "businesses_registered": len(bundles),
            "events_queued": len(queued_events),
        }

    def wait_until_idle(self, timeout_seconds: float = 10.0) -> bool:
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if self.bus.depth() == 0:
                return True
            threading.Event().wait(0.05)
        return False

    def get_features(self, business_id: str) -> Dict[str, int]:
        return self.features.get_features(business_id)

    def snapshot(self) -> Dict[str, Any]:
        topic_counts = self.store.count_events_by_topic()
        recent_activity = self.store.recent_activity(limit=10)
        redpanda_up = self._probe_host("localhost", 9092)
        redis_up    = self._probe_host("localhost", 6379)
        postgres_up = self._probe_host("localhost", 5432)
        # Real row counts from TimescaleDB and Redis — shown in demo UI
        timescaledb_rows = self.store.postgres_row_count()
        redis_keys       = self.store.redis_key_count()
        return {
            **self.state.snapshot(),
            **self.cache.stats(),
            "queue_depth": self.bus.depth(),
            "event_count": self.store.count_events(),
            "event_count_by_topic": topic_counts,
            "duplicate_event_count": self.state.duplicate_events,
            "stress_flag_count": self.store.count_stress_flags(),
            "business_count": self.store.count_businesses(),
            "last_event_at": self.store.get_last_event_timestamp(),
            "dedup_backend": self.store.dedup_backend(),
            "recent_activity_count": len(recent_activity),
            "recent_activity_sample": recent_activity,
            "redpanda_up": redpanda_up,
            "redis_up": redis_up,
            "postgres_up": postgres_up,
            # Detailed service metrics for the demo page
            "timescaledb_rows": timescaledb_rows,  # actual rows in hypertable
            "redis_keys": redis_keys,               # actual keys in Redis keyspace
        }

    def _ingestion_worker(self) -> None:
        while True:
            event = self.ingestion_queue.get()
            try:
                claimed = self.store.claim_event_id(str(event.get("event_id")))
                if not claimed:
                    self.state.bump("duplicate_events")
                    self.store.record_activity(
                        "duplicate_skipped",
                        f"Skipped duplicate event {event.get('event_id')}",
                        business_id=str(event.get("business_id")),
                        event_id=str(event.get("event_id")),
                    )
                    continue

                inserted = self.store.insert_event(event)
                if inserted:
                    self.state.bump("events_processed")
                    self.state.set_last_event_at(str(event.get("timestamp")))
                    self.store.record_activity(
                        "event_ingested",
                        f"Persisted {event.get('event_type')} from {event.get('topic')}",
                        business_id=str(event.get("business_id")),
                        event_id=str(event.get("event_id")),
                    )
                else:
                    self.state.bump("duplicate_events")
            finally:
                self.ingestion_queue.task_done()

    def _stress_worker(self) -> None:
        while True:
            event = self.stress_queue.get()
            try:
                if self._should_flag(event):
                    reason = self._flag_reason(event)
                    if self.state.mark_stress_event(str(event.get("event_id"))) and self.store.record_stress_flag(event, reason):
                        self.state.bump("stress_flags")
                        self.store.record_activity(
                            "stress_flagged",
                            reason,
                            business_id=str(event.get("business_id")),
                            event_id=str(event.get("event_id")),
                        )
            finally:
                self.stress_queue.task_done()

    @staticmethod
    def _should_flag(event: Dict[str, Any]) -> bool:
        if event.get("event_type") == "bounce":
            return True
        amount = float(event.get("amount", 0.0))
        return event.get("direction") == "outflow" and amount >= 50_000

    @staticmethod
    def _flag_reason(event: Dict[str, Any]) -> str:
        if event.get("event_type") == "bounce":
            return "Bounce detected in live stream"
        return "Large outflow detected in live stream"

    @staticmethod
    def _probe_host(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.35):
                return True
        except OSError:
            return False


_default_pipeline: CashFlowPipeline | None = None


def build_pipeline() -> CashFlowPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = CashFlowPipeline()
        _default_pipeline.start_workers()
    return _default_pipeline
