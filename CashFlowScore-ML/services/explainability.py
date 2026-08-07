"""
explainability.py — SHAP-based plain-English reason generation.
All heavy imports and the explainer are initialised lazily so that
importing this module never crashes during static analysis or when
the model file is absent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

import pandas as pd

if TYPE_CHECKING:
    import shap  # noqa: F401 – type-only

# ── lazy explainer singleton ───────────────────────────────────────────────────
_explainer: Any = None  # shap.TreeExplainer | None
_explainer_loaded = False  # tracks whether we already attempted loading


def _get_explainer() -> Any:
    """Return the SHAP TreeExplainer, loading it once on first use."""
    global _explainer, _explainer_loaded
    if _explainer_loaded:
        return _explainer  # may be None if load failed

    _explainer_loaded = True
    try:
        import shap as _shap  # noqa: PLC0415
        from services.predictor import _get_model  # noqa: PLC0415
        _explainer = _shap.TreeExplainer(_get_model())
    except Exception as exc:  # pragma: no cover
        print(f"Warning: Could not initialise SHAP explainer: {exc}")
        _explainer = None

    return _explainer


# ── plain-English template logic ───────────────────────────────────────────────

def _reasons_from_shap(feature_dict: Dict[str, Any], shap_dict: Dict[str, float]) -> List[str]:
    """Convert a dict of {feature: shap_value} into plain-English sentences."""
    sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)

    reasons: List[str] = []
    for feature_name, shap_val in sorted_features[:3]:
        impact = "positive" if shap_val > 0 else "negative"
        val = feature_dict.get(feature_name, 0)
        val_str = f"₹{val:,.0f}" if isinstance(val, (int, float)) and val > 1000 else str(val)

        if feature_name == "gst_filing_regularity":
            reasons.append(f"GST filing regularity: {val}% — strong {impact} factor")
        elif feature_name == "income_stability":
            reasons.append(f"Income stability: {val}% — {impact} factor")
        elif feature_name == "bounce_frequency":
            if val == 0:
                reasons.append("Zero bounces — strong positive factor")
            else:
                reasons.append(f"{val} bounces — {impact} risk factor")
        elif feature_name == "loan_default_history":
            if val == 1:
                reasons.append(f"Prior default history — major {impact} factor")
            else:
                reasons.append(f"Clean default history — {impact} factor")
        elif feature_name == "monthly_upi_volume":
            reasons.append(f"Monthly UPI volume: {val_str} — {impact} factor")
        elif feature_name == "avg_monthly_balance":
            reasons.append(f"Avg monthly balance: {val_str} — {impact} factor")
        else:
            name_clean = feature_name.replace("_", " ").capitalize()
            reasons.append(f"{name_clean}: {val_str} — {impact} factor")

    return reasons


# ── public API ─────────────────────────────────────────────────────────────────

def generate_reasons(feature_dict: Dict[str, Any]) -> List[str]:
    """Generate plain-English SHAP reasons for a single business."""
    explainer = _get_explainer()
    if explainer is None:
        return _fallback_reasons(feature_dict)

    df = pd.DataFrame([feature_dict])
    try:
        shap_values = explainer.shap_values(df)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # binary classification: positive class
        shap_dict = {col: float(shap_values[0][i]) for i, col in enumerate(df.columns)}
        return _reasons_from_shap(feature_dict, shap_dict)
    except Exception as exc:  # pragma: no cover
        print(f"SHAP inference failed: {exc}")
        return _fallback_reasons(feature_dict)


def generate_reasons_batch(df: pd.DataFrame) -> List[str]:
    """Generate plain-English SHAP reasons for every row in a DataFrame."""
    explainer = _get_explainer()
    if explainer is None:
        return [" | ".join(_fallback_reasons(row)) for row in df.to_dict("records")]

    try:
        shap_values = explainer.shap_values(df)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        all_reasons: List[str] = []
        for i in range(len(df)):
            feature_dict = df.iloc[i].to_dict()
            shap_dict = {col: float(shap_values[i][j]) for j, col in enumerate(df.columns)}
            all_reasons.append(" | ".join(_reasons_from_shap(feature_dict, shap_dict)))
        return all_reasons
    except Exception as exc:  # pragma: no cover
        print(f"Batch SHAP inference failed: {exc}")
        return [" | ".join(_fallback_reasons(row)) for row in df.to_dict("records")]


def _fallback_reasons(feature_dict: Dict[str, Any]) -> List[str]:
    """Rule-based fallback when SHAP is unavailable."""
    reasons: List[str] = []
    gst = feature_dict.get("gst_filing_regularity", 0)
    bounces = feature_dict.get("bounce_frequency", 0)
    stability = feature_dict.get("income_stability", 0)

    reasons.append(
        f"GST filing regularity: {gst}% — {'healthy' if gst >= 80 else 'needs improvement'}"
    )
    reasons.append(
        "Zero bounces on record — strong positive signal" if bounces == 0
        else f"{bounces} bounces detected — elevated risk"
    )
    reasons.append(
        f"Income stability: {stability}% — {'stable cash flow' if stability >= 75 else 'variable cash flow'}"
    )
    return reasons
