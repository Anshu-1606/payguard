import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                             precision_score, recall_score, f1_score,
                             roc_auc_score, RocCurveDisplay)

df = pd.read_csv("payments.csv")
X = df.drop(columns=["is_fraud"])
y = df["is_fraud"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(
    n_estimators=200, class_weight="balanced", random_state=42)
model.fit(X_train, y_train)

proba = model.predict_proba(X_test)[:, 1]
THRESHOLD = 0.30                       # lower = catch more fraud (higher recall)
pred = (proba >= THRESHOLD).astype(int)

print("Confusion matrix:\n", confusion_matrix(y_test, pred))
print("Precision:", round(precision_score(y_test, pred), 3))
print("Recall:   ", round(recall_score(y_test, pred), 3))
print("F1:       ", round(f1_score(y_test, pred), 3))
print("ROC-AUC:  ", round(roc_auc_score(y_test, proba), 3))

RocCurveDisplay.from_predictions(y_test, proba)
plt.title("PayGuard ROC curve")
plt.savefig("roc_curve.png", dpi=150)

joblib.dump({"model": model, "threshold": THRESHOLD, "features": list(X.columns)},
            "fraud_model.joblib")
print("Saved fraud_model.joblib and roc_curve.png")