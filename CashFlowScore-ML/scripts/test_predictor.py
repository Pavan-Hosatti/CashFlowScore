from services.predictor import predict_score

business = {
    "business_age_years": 12,
    "monthly_upi_volume": 600000,
    "monthly_bank_volume": 1800000,
    "monthly_cash_volume": 100000,
    "gst_filing_regularity": 95,
    "gst_turnover": 18000000,
    "bounce_frequency": 1,
    "avg_monthly_balance": 350000,
    "income_stability": 90,
    "seasonality_score": 80,
    "loan_default_history": 0
}

score, probability = predict_score(business)

print("Score:", score)
print("Probability:", probability)