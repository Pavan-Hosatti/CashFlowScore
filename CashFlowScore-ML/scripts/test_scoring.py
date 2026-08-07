from api.scoring_service import score_business

business = {

    "business_age_years":12,

    "monthly_upi_volume":600000,

    "monthly_bank_volume":1800000,

    "monthly_cash_volume":100000,

    "gst_filing_regularity":95,

    "gst_turnover":18000000,

    "bounce_frequency":1,

    "avg_monthly_balance":350000,

    "income_stability":90,

    "seasonality_score":80,

    "loan_default_history":0

}

print(score_business(business))