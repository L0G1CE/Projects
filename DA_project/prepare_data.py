import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# ---------- Load ----------
print("Loading CSVs…")
train = pd.read_csv(DATA_DIR / "train.csv")
test  = pd.read_csv(DATA_DIR / "test.csv")
features = pd.read_csv(DATA_DIR / "features.csv")
stores   = pd.read_csv(DATA_DIR / "stores.csv")

# ---------- Basic hygiene ----------
# Ensure column name consistency (strip spaces just in case)
for df in [train, test, features, stores]:
    df.columns = df.columns.str.strip()

# Parse dates
for df in [train, test, features]:
    df["Date"] = pd.to_datetime(df["Date"])

# Ensure expected columns exist
expected_train_cols = {"Store","Dept","Date","Weekly_Sales","IsHoliday"}
expected_test_cols  = {"Store","Dept","Date","IsHoliday"}
expected_features_cols = {"Store","Date","Temperature","Fuel_Price",
                          "CPI","Unemployment",
                          "MarkDown1","MarkDown2","MarkDown3","MarkDown4","MarkDown5"}
expected_stores_cols = {"Store","Type","Size"}

missing = []
if not expected_train_cols.issubset(train.columns): missing.append(("train", expected_train_cols - set(train.columns)))
if not expected_test_cols.issubset(test.columns): missing.append(("test", expected_test_cols - set(test.columns)))
if not expected_features_cols.issubset(features.columns): missing.append(("features", expected_features_cols - set(features.columns)))
if not expected_stores_cols.issubset(stores.columns): missing.append(("stores", expected_stores_cols - set(stores.columns)))
if missing:
    raise ValueError(f"Missing expected columns: {missing}")

# Make IsHoliday boolean (some dumps use True/False, others 0/1)
for df in [train, test]:
    if df["IsHoliday"].dtype != bool:
        df["IsHoliday"] = df["IsHoliday"].astype(int).astype(bool)

# ---------- Merge ----------
print("Merging store attributes…")
train_m = train.merge(stores, on="Store", how="left")
test_m  = test.merge(stores,  on="Store", how="left")

print("Merging external features…")
# Many-to-one on (Store, Date)
train_m = train_m.merge(features, on=["Store","Date"], how="left")
test_m  = test_m.merge(features,  on=["Store","Date"], how="left")

# ---------- Clean / feature engineering ----------
md_cols = ["MarkDown1","MarkDown2","MarkDown3","MarkDown4","MarkDown5"]

# MarkDowns are often NA when no promo — fill with 0
for df in [train_m, test_m]:
    df[md_cols] = df[md_cols].fillna(0)

# Optional: forward-fill CPI/Unemployment by Store (they’re slow-moving)
for df in [train_m, test_m]:
    df.sort_values(["Store","Date"], inplace=True)
    for col in ["CPI", "Unemployment"]:
        df[col] = df.groupby("Store")[col].ffill().bfill()

# Add handy time columns
for df in [train_m, test_m]:
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)

# Sanity checks
print("\nRow counts:")
print("  train:", len(train), "→ merged:", len(train_m))
print("  test :", len(test),  "→ merged:", len(test_m))

# Duplicates on the grain (Store, Dept, Date) can break modeling
dup_train = train_m.duplicated(subset=["Store","Dept","Date"]).sum()
dup_test  = test_m.duplicated(subset=["Store","Dept","Date"]).sum()
print(f"Duplicate keys — train: {dup_train}, test: {dup_test}")

# ---------- Save ----------
OUT_DIR = DATA_DIR
train_out_csv = OUT_DIR / "walmart_train_merged.csv"
test_out_csv  = OUT_DIR / "walmart_test_merged.csv"
train_out_parquet = OUT_DIR / "walmart_train_merged.parquet"
test_out_parquet  = OUT_DIR / "walmart_test_merged.parquet"

print("\nSaving merged datasets…")
train_m.to_csv(train_out_csv, index=False)
test_m.to_csv(test_out_csv, index=False)

# Also save compact Parquet versions
train_m.to_parquet(train_out_parquet, index=False)
test_m.to_parquet(test_out_parquet, index=False)

print("\nDone ✅")
print(f"- {train_out_csv}")
print(f"- {test_out_csv}")
print(f"- {train_out_parquet}")
print(f"- {test_out_parquet}")

# ---------- Quick profiling prints ----------
print("\nMerged schema (train):")
print(train_m.dtypes)

print("\nMissing values (train - top 12):")
print(train_m.isna().sum().sort_values(ascending=False).head(12))

# Small preview
print("\nSample rows (train):")
print(train_m.head(5).to_string(index=False))
