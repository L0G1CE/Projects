# build_analytics_views.py
# Creates Tableau-ready analytics views from walmart_train_final.csv
# Output folder: ./outputs

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import norm

DATA_DIR = Path("data")
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

# ---------- Load cleaned, merged training data ----------
df = pd.read_csv(DATA_DIR / "walmart_train_final.csv", parse_dates=["Date"])

# Defensive typing
if df["IsHoliday"].dtype != bool:
    df["IsHoliday"] = df["IsHoliday"].astype(int).astype(bool)

# Make sure these exist (created in your finalize step)
for col in ["Promo_Intensity", "Year", "Week"]:
    if col not in df.columns:
        if col == "Promo_Intensity":
            md_cols = [c for c in df.columns if c.startswith("MarkDown")]
            df[col] = df[md_cols].fillna(0).sum(axis=1) if md_cols else 0.0
        if col == "Year":
            df[col] = df["Date"].dt.year
        if col == "Week":
            df[col] = df["Date"].dt.isocalendar().week.astype(int)

# ---------- 1) Overall weekly totals (trend line) ----------
weekly_total = (
    df.groupby("Date", as_index=False)["Weekly_Sales"]
      .sum()
      .sort_values("Date")
)
weekly_total.to_csv(OUT_DIR / "weekly_total_sales.csv", index=False)  # cols: Date, Weekly_Sales

# ---------- 2) Store–Dept weekly series (grain) ----------
store_dept_weekly = (
    df.groupby(["Store", "Dept", "Date"], as_index=False)["Weekly_Sales"]
      .sum()
      .sort_values(["Store", "Dept", "Date"])
)
store_dept_weekly.to_csv(OUT_DIR / "store_dept_weekly.csv", index=False)  # Store, Dept, Date, Weekly_Sales

# ---------- 3) Holiday vs Regular ----------
holiday_comp = (
    df.groupby("IsHoliday")["Weekly_Sales"]
      .agg(Count="count", Total_Sales="sum", Avg_Weekly_Sales="mean")
      .reset_index()
)
holiday_comp.to_csv(OUT_DIR / "holiday_vs_regular.csv", index=False)  # IsHoliday, Count, Total_Sales, Avg_Weekly_Sales

# ---------- 4) Promotion impact (any markdown > 0) ----------
promo_flag = df["Promo_Intensity"] > 0
promo_summary = (
    df.assign(Has_Promo=promo_flag)
      .groupby("Has_Promo")["Weekly_Sales"]
      .agg(Count="count", Total_Sales="sum", Avg_Weekly_Sales="mean")
      .reset_index()
)
promo_summary.to_csv(OUT_DIR / "promo_impact_summary.csv", index=False)  # Has_Promo, Count, Total_Sales, Avg_Weekly_Sales

# ---------- 5) Top Stores & Top Departments ----------
top_stores = (
    df.groupby("Store", as_index=False)["Weekly_Sales"]
      .sum()
      .sort_values("Weekly_Sales", ascending=False)
)
top_stores.to_csv(OUT_DIR / "top_stores_total_sales.csv", index=False)  # Store, Weekly_Sales

top_depts = (
    df.groupby("Dept", as_index=False)["Weekly_Sales"]
      .sum()
      .sort_values("Weekly_Sales", ascending=False)
)
top_depts.to_csv(OUT_DIR / "top_departments_total_sales.csv", index=False)  # Dept, Weekly_Sales

# ---------- 6) Store attributes: Type & Size buckets ----------
# By Type
avg_by_type = (
    df.groupby("Type", as_index=False)["Weekly_Sales"]
      .mean()
      .rename(columns={"Weekly_Sales": "Avg_Weekly_Sales"})
)
avg_by_type.to_csv(OUT_DIR / "avg_sales_by_store_type.csv", index=False)  # Type, Avg_Weekly_Sales

# By Size bucket (Small/Medium/Large)
size_bins = pd.cut(
    df["Size"],
    bins=[0, 80_000, 140_000, 300_000],
    labels=["Small", "Medium", "Large"],
    include_lowest=True
)
by_size = (
    df.assign(StoreSizeBin=size_bins)
      .groupby("StoreSizeBin", as_index=False)["Weekly_Sales"]
      .mean()
      .rename(columns={"Weekly_Sales": "Avg_Weekly_Sales"})
)
# Ensure correct order in CSV
by_size["StoreSizeBin"] = by_size["StoreSizeBin"].astype(str)
order = pd.Categorical(by_size["StoreSizeBin"], ["Small", "Medium", "Large"], ordered=True)
by_size = by_size.sort_values(by="StoreSizeBin", key=lambda s: order)
by_size.to_csv(OUT_DIR / "avg_sales_by_store_size_bucket.csv", index=False)  # StoreSizeBin, Avg_Weekly_Sales

# ---------- 7) Simple inventory lens (per Store–Dept) ----------
LEAD_TIME_WEEKS = 2
Z = norm.ppf(0.95)  # ~1.645 for 95% service level

inv = (
    df.groupby(["Store", "Dept"])["Weekly_Sales"]
      .agg(Demand_Avg="mean", Demand_Std="std")
      .reset_index()
)
inv["Safety_Stock"] = Z * inv["Demand_Std"].fillna(0) * np.sqrt(LEAD_TIME_WEEKS)
inv["ROP"] = inv["Demand_Avg"] * LEAD_TIME_WEEKS + inv["Safety_Stock"]
inv.to_csv(OUT_DIR / "inventory_basics_store_dept.csv", index=False)
# cols: Store, Dept, Demand_Avg, Demand_Std, Safety_Stock, ROP

# ---------- Done ----------
print("Analytics views saved in /outputs:")
for p in sorted(OUT_DIR.glob("*.csv")):
    print(" -", p.name)
