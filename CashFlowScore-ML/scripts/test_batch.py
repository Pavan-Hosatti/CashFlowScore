from services.batch_scorer import score_excel

output = score_excel(
    "data/sample_businesses.xlsx",
    "data/scored_output.xlsx"
)

print("Saved:", output)