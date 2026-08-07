from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

FEATURE_COLUMNS = [
    "business_age_years",
    "monthly_upi_volume",
    "monthly_bank_volume",
    "monthly_cash_volume",
    "gst_filing_regularity",
    "gst_turnover",
    "bounce_frequency",
    "avg_monthly_balance",
    "income_stability",
    "seasonality_score",
    "loan_default_history",
]

DEFAULT_TOPICS = ("txn.upi", "txn.bank", "gst.filing")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def parse_timestamp(value: str | datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class BusinessProfile:
    business_id: str
    business_age_years: int
    monthly_upi_volume: int
    monthly_bank_volume: int
    monthly_cash_volume: int
    gst_filing_regularity: int
    gst_turnover: int
    bounce_frequency: int
    avg_monthly_balance: int
    income_stability: int
    seasonality_score: int
    loan_default_history: int
    opening_balance: int = 0
    target_monthly_growth: float = 0.0

    def as_feature_dict(self) -> Dict[str, int]:
        return {column: int(getattr(self, column)) for column in FEATURE_COLUMNS}

    def as_record(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "BusinessProfile":
        normalized = {key: int(round(float(payload[key]))) for key in FEATURE_COLUMNS}
        return cls(
            business_id=str(payload["business_id"]),
            opening_balance=int(round(float(payload.get("opening_balance", normalized["avg_monthly_balance"])))),
            target_monthly_growth=float(payload.get("target_monthly_growth", 0.0)),
            **normalized,
        )


@dataclass(frozen=True)
class RawEvent:
    event_id: str
    business_id: str
    topic: str
    event_type: str
    amount: float
    timestamp: str
    direction: str = "inflow"
    balance_after: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RawEvent":
        return cls(
            event_id=str(payload["event_id"]),
            business_id=str(payload["business_id"]),
            topic=str(payload.get("topic", "txn.bank")),
            event_type=str(payload.get("event_type", "credit")),
            amount=float(payload.get("amount", 0.0)),
            timestamp=str(payload.get("timestamp", utc_now_iso())),
            direction=str(payload.get("direction", "inflow")),
            balance_after=float(payload.get("balance_after", 0.0)),
            metadata=dict(payload.get("metadata", {})),
        )
