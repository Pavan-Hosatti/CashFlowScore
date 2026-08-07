"""
predictor.py — XGBoost inference module.
Model is loaded lazily on first use so that importing this module
never raises FileNotFoundError when the model file is not on the
current working directory (e.g. during type-checking or testing).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import pandas as pd

if TYPE_CHECKING:
    from xgboost import XGBClassifier  # noqa: F401 – type-only

# ── lazy model singleton ───────────────────────────────────────────────────────
_model: Any = None  # xgboost.Booster | None


def _get_model() -> Any:
    """Return the XGBoost model, loading it once on first access."""
    global _model
    if _model is not None:
        return _model

    try:
        import xgboost as xgb  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "xgboost is not installed. Run: pip install xgboost"
        ) from exc

    # Support running from any working directory
    model_path = Path(__file__).resolve().parents[1] / "model" / "xgb_model.json"
    if not model_path.exists():
        # fallback: try relative path (original behaviour)
        model_path = Path("model") / "xgb_model.json"

    # Use Booster directly to avoid sklearn wrapper _estimator_type bugs
    _model = xgb.Booster(model_file=str(model_path))
    return _model


# ── public API ─────────────────────────────────────────────────────────────────

def predict_score(feature_dict: Dict[str, Any]) -> Tuple[int, float]:
    """
    Score a single business.
    Returns (score_0_to_100, probability_0_to_1).
    """
    import xgboost as xgb
    model = _get_model()
    df = pd.DataFrame([feature_dict])
    dmatrix = xgb.DMatrix(df)
    
    # Booster.predict returns probability of positive class for binary classification
    preds = model.predict(dmatrix)
    probability: float = float(preds[0])
    score: int = round(probability * 100)
    return score, probability


def predict_score_batch(df: pd.DataFrame) -> Tuple[List[int], List[float]]:
    """
    Vectorised batch scoring.
    Takes a DataFrame of feature rows.
    Returns (scores_list, probabilities_list).
    """
    import xgboost as xgb
    model = _get_model()
    dmatrix = xgb.DMatrix(df)
    probabilities = model.predict(dmatrix)
    
    scores = (probabilities * 100).round().astype(int)
    return list(scores), list(probabilities)