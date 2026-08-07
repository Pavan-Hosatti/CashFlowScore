import pandas as pd
import numpy as np

# Reproducible random numbers
np.random.seed(42)

NUM_RECORDS = 1000

data = pd.DataFrame({
    "business_age_years": np.random.randint(1, 21, NUM_RECORDS),

    "monthly_upi_volume": np.random.randint(50000, 1000000, NUM_RECORDS),

    "monthly_bank_volume": np.random.randint(100000, 5000000, NUM_RECORDS),

    "monthly_cash_volume": np.random.randint(10000, 500000, NUM_RECORDS),

    "gst_filing_regularity": np.random.randint(50, 101, NUM_RECORDS),

    "gst_turnover": np.random.randint(500000, 50000000, NUM_RECORDS),

    "bounce_frequency": np.random.randint(0, 15, NUM_RECORDS),

    "avg_monthly_balance": np.random.randint(10000, 2000000, NUM_RECORDS),

    "income_stability": np.random.randint(40, 100, NUM_RECORDS),

    "seasonality_score": np.random.randint(30, 100, NUM_RECORDS),

    "loan_default_history": np.random.choice([0, 1], NUM_RECORDS, p=[0.9, 0.1])
})

# ----------------------------
# Business Rules for Approval
# ----------------------------

score = (
    (data["gst_filing_regularity"] * 0.25)
    + (data["income_stability"] * 0.25)
    + (data["business_age_years"] * 2)
    + (data["avg_monthly_balance"] / 50000)
    - (data["bounce_frequency"] * 4)
    - (data["loan_default_history"] * 25)
)

# Add some randomness (noise)
score += np.random.normal(0, 5, NUM_RECORDS)

# Create labels
data["score_label"] = (score >= 50).astype(int)

# Save dataset
output_file = "data/synthetic_msme_data.csv"
data.to_csv(output_file, index=False)

print(f"Dataset saved to {output_file}")
print(data.head())