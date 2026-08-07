import pandas as pd
from services.predictor import predict_score_batch
from services.explainability import generate_reasons_batch

def score_excel(input_file, output_file):
    df = pd.read_excel(input_file)

    # Remove label if present before predicting
    features_df = df.drop(columns=["score_label"]) if "score_label" in df.columns else df

    # Vectorized batch prediction
    scores, probabilities = predict_score_batch(features_df)

    # Batch explainability
    reasons = generate_reasons_batch(features_df)

    # Append results
    df["credit_score"] = scores
    df["confidence"] = [round(p * 100, 2) for p in probabilities]
    df["top_reasons"] = reasons

    df.to_excel(output_file, index=False)
    print(f"✅ Saved: {output_file}")