import sys
import pandas as pd
import sys
import os

# Ensure the parent directory is in the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.predictor import predict_score_batch
from services.explainability import generate_reasons_batch

def main():
    if len(sys.argv) != 2:
        print("Usage: python offline/offline_score.py <excel_file>")
        return

    input_file = sys.argv[1]

    df = pd.read_excel(input_file, engine="openpyxl")

    # Remove label column if present
    features_df = df.drop(columns=["score_label"]) if "score_label" in df.columns else df

    scores, probabilities = predict_score_batch(features_df)
    reasons = generate_reasons_batch(features_df)
    
    decisions = ["Approved" if s >= 70 else "Rejected" for s in scores]

    df["Score"] = scores
    df["Decision"] = decisions
    df["Top Reasons"] = reasons

    output_file = "offline/scored_output.xlsx"
    df.to_excel(output_file, index=False, engine="openpyxl")

    print(f"✅ Offline scoring complete!")
    print(f"📄 Output saved to: {output_file}")


if __name__ == "__main__":
    main()