# train_otif_xgb.py
import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score

import xgboost as xgb
import joblib

CSV = "olist_otif_dataset.csv"
MODEL_OUT = "otif_xgb_pipeline.joblib"

# 1) Load
df = pd.read_csv(CSV, parse_dates=["order_purchase_timestamp"])

# 2) Basic sanity checks
assert "late_delivery" in df.columns, "Target 'late_delivery' missing."
assert df["late_delivery"].isin([0,1]).all(), "Target must be 0/1."

# 3) Keep only features (drop ID/time cols that aren't features)
id_cols = ["order_id"]
time_col = "order_purchase_timestamp"
y = df["late_delivery"].astype(int)
X = df.drop(columns=id_cols + [time_col, "late_delivery"])

# 4) Identify column types
num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

# 5) Preprocess (impute + one-hot encode)
numeric_pipe = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipe = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),  # fills NaN with "most frequent"; alternative: constant "missing"
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])

pre = ColumnTransformer(
    transformers=[
        ("num", numeric_pipe, num_cols),
        ("cat", categorical_pipe, cat_cols),
    ],
    remainder="drop"
)

# 6) Time-based split (sort by actual timestamp)
df_sorted = df.sort_values(time_col).reset_index(drop=True)
split_idx = int(0.8 * len(df_sorted))
train_idx = df_sorted.index[:split_idx]
test_idx  = df_sorted.index[split_idx:]

X_train = X.loc[train_idx]
X_test  = X.loc[test_idx]
y_train = y.loc[train_idx]
y_test  = y.loc[test_idx]

# 7) Handle imbalance (scale_pos_weight = neg/pos on TRAIN only)
pos = (y_train == 1).sum()
neg = (y_train == 0).sum()
scale_pos_weight = max(1.0, neg / max(1, pos))  # avoid div-by-zero

# 8) Build full pipeline (preprocess -> XGBoost)
clf = xgb.XGBClassifier(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.9,
    colsample_bytree=0.9,
    min_child_weight=1.0,
    reg_lambda=1.0,
    tree_method="hist",
    random_state=42,
    scale_pos_weight=scale_pos_weight,
    eval_metric="auc"
)

pipe = Pipeline(steps=[
    ("pre", pre),
    ("xgb", clf)
])

# 9) Train
pipe.fit(X_train, y_train)

# 10) Evaluate
proba = pipe.predict_proba(X_test)[:, 1]
roc = roc_auc_score(y_test, proba)
pr  = average_precision_score(y_test, proba)

# Precision@K (top 20% highest risk)
k = max(1, int(0.20 * len(proba)))
topk_idx = np.argsort(proba)[-k:]
prec_at_k = precision_score(y_test.iloc[topk_idx], np.ones(k))

print(f"\n=== Evaluation (holdout = latest 20%) ===")
print(f"ROC-AUC        : {roc:.3f}")
print(f"PR-AUC         : {pr:.3f}")
print(f"Precision@20%  : {prec_at_k:.3f}")
print(f"Positives in train: {pos} / {pos+neg} ({pos/(pos+neg):.2%})")
print(f"scale_pos_weight used: {scale_pos_weight:.2f}")

# 11) Persist the pipeline (preprocessing + model together)
joblib.dump(pipe, MODEL_OUT)
print(f"\nSaved pipeline to {MODEL_OUT}")

# 12) Optional: quick schema print to help your app later
print("\n[Info] Numeric cols:", num_cols)
print("[Info] Categorical cols:", cat_cols)
