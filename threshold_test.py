import pandas as pd, joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, confusion_matrix

df = pd.read_csv("payments.csv")
X, y = df.drop(columns=["is_fraud"]), df["is_fraud"]
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = joblib.load("fraud_model.joblib")["model"]
proba = model.predict_proba(X_test)[:, 1]

for t in [0.1, 0.2, 0.3, 0.4, 0.5]:
    pred = (proba >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    print(f"t={t}: recall={recall_score(y_test, pred):.2f} "
          f"precision={precision_score(y_test, pred):.2f} missed={fn} false_alarms={fp}")