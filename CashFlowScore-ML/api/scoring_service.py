from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib import error, request

import pandas as pd
import shap
from xgboost import XGBClassifier

from services.cache import get_cache, set_cache
from services.logger import logger

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

PAVAN_FEATURES_URL = os.getenv("PAVAN_FEATURES_URL", "http://127.0.0.1:8001").rstrip("/")

# Model and explainability are loaded lazily via services.predictor and services.explainability


def _cache_key(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _fetch_features_from_pavan(business_id: str) -> Dict[str, Any]:
    url = f"{PAVAN_FEATURES_URL}/features/{business_id}"
    try:
        with request.urlopen(url, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload
    except error.URLError as exc:
        raise RuntimeError(
            f"Could not load features for business_id={business_id} from Pavan at {url}"
        ) from exc


def _resolve_feature_payload(payload: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    if all(column in payload for column in FEATURE_COLUMNS):
        return {column: payload[column] for column in FEATURE_COLUMNS}, "direct"

    business_id = payload.get("business_id")
    if business_id:
        features = _fetch_features_from_pavan(str(business_id))
        return {column: features[column] for column in FEATURE_COLUMNS}, "pavan"

    missing = [column for column in FEATURE_COLUMNS if column not in payload]
    raise ValueError(
        "score requires either a full feature dict or a business_id. Missing: " + ", ".join(missing)
    )


def score_business(feature_payload):
    resolved_features, source = _resolve_feature_payload(dict(feature_payload))

    # -------------------------
    # Check Redis Cache
    # -------------------------
    cache_key = _cache_key({"source": source, **resolved_features})

    cached = get_cache(cache_key)

    if cached:
        logger.info("Returned response from Redis cache")
        return cached

    # -------------------------
    # Predict Score
    # -------------------------
    from services.predictor import predict_score
    score, probability = predict_score(resolved_features)

    # -------------------------
    # SHAP Explainability — single source of truth in services/explainability.py
    # -------------------------
    from services.explainability import generate_reasons  # deferred to avoid circular import
    reasons = generate_reasons(resolved_features)

    # -------------------------
    # Build Response
    # -------------------------
    response = {
        "score": score,
        "top_reasons": reasons,
        "source": source,
    }

    # -------------------------
    # Save in Redis
    # -------------------------
    set_cache(cache_key, response)

    return response