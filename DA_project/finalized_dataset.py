import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
train = pd.read_csv(DATA_DIR / "walmart_train_merged.csv", parse_dates=["Date"])
test  = pd.read_csv(DATA_DIR / "walmart_test_merged.csv", parse_dates=["Date"])

def coalesce_holiday(df):
    # Some dumps label True/False inconsistently; coalesce then cast to bool
    hcols = [c for c in df.columns if c.startswith("IsHoliday")]
    if len(hcols) == 2:
        df["IsHoliday"] = (df[hcols[0]].astype(int) | df[hcols[1]].astype(int)).astype(bool)
        df.drop(columns=hcols, inplace=True)
    elif "IsHoliday" not in df.columns:
        # fallback: rename the single one to IsHoliday
        df.rename(columns={hcols[0]: "IsHoliday"}, inplace=True)
    return df

train = coalesce_holiday(train)
test  = coalesce_holiday(test)

# Promo intensity (sum of MarkDowns). NA already filled as 0 in your previous script.
md_cols = [c for c in train.columns if c.startswith("MarkDown")]
for df in [train, test]:
    df["Promo_Intensity"] = df[md_cols].sum(axis=1)

# Reorder columns for readability
ordered = ["Store","Dept","Date","Weekly_Sales","IsHoliday","Type","Size",
           "Temperature","Fuel_Price","CPI","Unemployment","Promo_Intensity"] + md_cols + ["Year","Week"]
train = train[[c for c in ordered if c in train.columns]]
test  = test[[c for c in ordered if c in test.columns and c != "Weekly_Sales"]]

# Save cleaned versions
train.to_csv(DATA_DIR / "walmart_train_final.csv", index=False)
test.to_csv(DATA_DIR / "walmart_test_final.csv", index=False)

print("Saved:")
print(" - data/walmart_train_final.csv")
print(" - data/walmart_test_final.csv")
