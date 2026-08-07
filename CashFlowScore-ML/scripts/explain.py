import shap
import pandas as pd
from xgboost import XGBClassifier

# -----------------------------
# Load Dataset
# -----------------------------
df = pd.read_csv("data/synthetic_msme_data.csv")

X = df.drop(columns=["score_label"])

# -----------------------------
# Load Trained Model
# -----------------------------
model = XGBClassifier()
model.load_model("model/xgb_model.json")

# -----------------------------
# Create SHAP Explainer
# -----------------------------
explainer = shap.TreeExplainer(model)

# -----------------------------
# Example Business
# -----------------------------
sample = X.iloc[[0]]

# -----------------------------
# Compute SHAP Values
# -----------------------------
shap_values = explainer.shap_values(sample)

feature_importance = list(zip(
    sample.columns,
    shap_values[0]
))

feature_importance.sort(
    key=lambda x: abs(x[1]),
    reverse=True
)

print("\nTop Influencing Features:\n")

for feature, value in feature_importance[:5]:
    print(f"{feature}: {value:.4f}")