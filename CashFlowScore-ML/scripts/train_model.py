import os
import json
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

from xgboost import XGBClassifier

# -----------------------
# Load Dataset
# -----------------------
df = pd.read_csv("data/synthetic_msme_data.csv")

# Features & Target
X = df.drop(columns=["score_label"])
y = df["score_label"]

# -----------------------
# Train / Test Split
# -----------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------
# Train Model
# -----------------------
model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    random_state=42,
    eval_metric="logloss"
)

model.fit(X_train, y_train)

# -----------------------
# Predictions
# -----------------------
pred = model.predict(X_test)
prob = model.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, pred)
auc = roc_auc_score(y_test, prob)

print(f"Accuracy : {accuracy:.4f}")
print(f"AUC      : {auc:.4f}")

# -----------------------
# Save Model
# -----------------------
os.makedirs("model", exist_ok=True)

model.save_model("model/xgb_model.json")

metrics = {
    "accuracy": round(float(accuracy), 4),
    "auc": round(float(auc), 4)
}

with open("model/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("\n✅ Model saved to model/xgb_model.json")
print("✅ Metrics saved to model/metrics.json")