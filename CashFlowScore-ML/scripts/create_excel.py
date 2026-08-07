import pandas as pd

# Read the CSV you already generated
df = pd.read_csv("data/synthetic_msme_data.csv")

# Take the first 100 rows (or use all rows)
df.head(100).to_excel(
    "data/sample_businesses.xlsx",
    index=False,
    engine="openpyxl"
)

print("✅ Excel file created successfully!")