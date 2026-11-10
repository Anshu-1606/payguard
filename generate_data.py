import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 5000
fraud = rng.random(N) < 0.04          # about 4% fraud

df = pd.DataFrame({
    "amount": np.where(fraud, rng.lognormal(5.0, 0.8, N), rng.lognormal(3.6, 0.7, N)),
    "hour": np.where(fraud, rng.choice([0,1,2,3,4,23], N), rng.integers(7, 23, N)),
    "account_age_days": np.where(fraud, rng.integers(0, 20, N), rng.integers(10, 1500, N)),
    "orders_last_hour": np.where(fraud, rng.integers(1, 8, N), rng.integers(0, 3, N)),
    "country_mismatch": np.where(fraud, rng.random(N) < 0.75, rng.random(N) < 0.06).astype(int),
    "past_orders": np.where(fraud, rng.integers(0, 3, N), rng.integers(0, 40, N)),
    "disposable_email": np.where(fraud, rng.random(N) < 0.55, rng.random(N) < 0.03).astype(int),
})
df["is_fraud"] = fraud.astype(int)

# add noise so the task isn't too easy: flip a few labels
flip = rng.random(N) < 0.01
df.loc[flip, "is_fraud"] = 1 - df.loc[flip, "is_fraud"]

df.to_csv("payments.csv", index=False)
print(df["is_fraud"].value_counts())
print("Saved payments.csv")