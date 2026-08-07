from typing import List, Dict, Any


def get_mock_businesses() -> List[Dict[str, Any]]:
    return [
        {
            "id": "BIZ-1001",
            "name": "Aarav Traders",
            "segment": "Retail",
            "score": 72,
            "status": "approved",
            "credit_unlocked": 480000,
            "risk_band": "medium",
            "recent_activity": "GST filing posted 2 days ago",
            "reasons": [
                "GST filing regularity is strong",
                "Cash inflow trend is stable",
                "Bounce frequency remains low"
            ],
            "editable_inputs": {
                "business_age_years": 8,
                "monthly_upi_volume": 320000,
                "monthly_bank_volume": 450000,
                "monthly_cash_volume": 20000,
                "gst_filing_regularity": 98,
                "gst_turnover": 4500000,
                "bounce_frequency": 0,
                "avg_monthly_balance": 180000,
                "income_stability": 0.85,
                "seasonality_score": 0.3,
                "loan_default_history": 0
            }
        },
        {
            "id": "BIZ-1002",
            "name": "Sree Foods",
            "segment": "Food Services",
            "score": 41,
            "status": "rejected",
            "credit_unlocked": 0,
            "risk_band": "high",
            "recent_activity": "Cash outflow spike detected",
            "reasons": [
                "Large unexplained outflow",
                "GST filing irregularity detected",
                "Bounce frequency elevated"
            ],
            "editable_inputs": {
                "business_age_years": 3,
                "monthly_upi_volume": 180000,
                "monthly_bank_volume": 250000,
                "monthly_cash_volume": 10000,
                "gst_filing_regularity": 60,
                "gst_turnover": 2500000,
                "bounce_frequency": 4,
                "avg_monthly_balance": 40000,
                "income_stability": 0.5,
                "seasonality_score": 0.8,
                "loan_default_history": 1
            }
        },
        {
            "id": "BIZ-1003",
            "name": "Nila Pharma",
            "segment": "Healthcare",
            "score": 84,
            "status": "approved",
            "credit_unlocked": 760000,
            "risk_band": "low",
            "recent_activity": "Supplier payment consistency improved",
            "reasons": [
                "Revenue stability is above median",
                "Supplier payments are dependable",
                "Seasonality pattern is healthy"
            ],
            "editable_inputs": {
                "business_age_years": 8,
                "monthly_upi_volume": 320000,
                "monthly_bank_volume": 450000,
                "monthly_cash_volume": 20000,
                "gst_filing_regularity": 98,
                "gst_turnover": 4500000,
                "bounce_frequency": 0,
                "avg_monthly_balance": 180000,
                "income_stability": 0.85,
                "seasonality_score": 0.3,
                "loan_default_history": 0
            }
        },
    ]


def get_mock_status() -> Dict[str, Any]:
    return {
        "events_processed": 12480,
        "queue_depth": 38,
        "cache_hit_rate": 0.89,
        "services": {
            "redpanda": "up",
            "redis": "up",
            "postgres": "up"
        },
        "timestamp": "2026-08-04T10:00:00Z"
    }
