#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build OTIF Early-Warning modeling dataset from the Kaggle Olist Brazilian E-Commerce CSVs.
This version is aligned to the exact column names from the dataset.

OUTPUT:
  ./olist_otif_dataset.csv

Reads from FOLDER:
  - olist_orders_dataset.csv
  - olist_order_items_dataset.csv
  - olist_customers_dataset.csv
  - olist_sellers_dataset.csv
  - olist_geolocation_dataset.csv
  - olist_products_dataset.csv
  - olist_order_reviews_dataset.csv  (for historical seller review features)

Leakage guard:
- Only use order_delivered_customer_date for the label.
- Historical seller delay/review features are cumulative and shifted to exclude the current order.
"""

import os
import pandas as pd
import numpy as np

FOLDER = r"./archive"     # <-- change to your CSV folder
OUTFILE = "olist_otif_dataset.csv"

# ---------------------
# Helpers
# ---------------------
def parse_dt(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def to_days(td):
    return td.dt.total_seconds() / 86400.0

def haversine_np(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371.0 * c  # km

def safe_mode(series):
    if series.empty:
        return np.nan
    m = series.mode()
    return m.iloc[0] if not m.empty else np.nan

# ---------------------
# Load
# ---------------------
orders = pd.read_csv(os.path.join(FOLDER, "olist_orders_dataset.csv"))
orders = parse_dt(orders, [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
])

order_items = pd.read_csv(os.path.join(FOLDER, "olist_order_items_dataset.csv"))
order_items = parse_dt(order_items, ["shipping_limit_date"])

customers = pd.read_csv(os.path.join(FOLDER, "olist_customers_dataset.csv"))
sellers = pd.read_csv(os.path.join(FOLDER, "olist_sellers_dataset.csv"))
geoloc = pd.read_csv(os.path.join(FOLDER, "olist_geolocation_dataset.csv"))
products = pd.read_csv(os.path.join(FOLDER, "olist_products_dataset.csv"))

# Optional reviews for historical seller quality
reviews = pd.read_csv(os.path.join(FOLDER, "olist_order_reviews_dataset.csv"))
reviews = parse_dt(reviews, ["review_creation_date", "review_answer_timestamp"])

# ---------------------
# Geolocation: average lat/lng per zip prefix to join
# ---------------------
geo_zip = (geoloc.groupby("geolocation_zip_code_prefix", as_index=False)
           .agg(geo_lat=("geolocation_lat", "mean"),
                geo_lng=("geolocation_lng", "mean")))

cust_geo = (customers.merge(geo_zip, left_on="customer_zip_code_prefix",
                            right_on="geolocation_zip_code_prefix", how="left")
            .rename(columns={"geo_lat": "cust_lat", "geo_lng": "cust_lng"})
            [["customer_id","customer_unique_id","customer_zip_code_prefix",
              "customer_city","customer_state","cust_lat","cust_lng"]])

sell_geo = (sellers.merge(geo_zip, left_on="seller_zip_code_prefix",
                          right_on="geolocation_zip_code_prefix", how="left")
            .rename(columns={"geo_lat": "sell_lat", "geo_lng": "sell_lng"})
            [["seller_id","seller_city","seller_state","sell_lat","sell_lng"]])

# ---------------------
# Order-item aggregates
# ---------------------
order_items_enriched = (order_items
    .merge(sell_geo, on="seller_id", how="left")
    .merge(products[["product_id","product_weight_g","product_length_cm",
                     "product_height_cm","product_width_cm","product_category_name"]],
           on="product_id", how="left")
)

item_agg = (order_items_enriched
    .groupby("order_id")
    .agg(
        n_items=("order_item_id","count"),
        n_sellers=("seller_id", pd.Series.nunique),
        total_price=("price","sum"),
        total_freight=("freight_value","sum"),
        avg_product_weight_g=("product_weight_g","mean"),
        avg_product_length_cm=("product_length_cm","mean"),
        avg_product_height_cm=("product_height_cm","mean"),
        avg_product_width_cm=("product_width_cm","mean"),
        product_category_mode=("product_category_name", safe_mode),
        seller_state_mode=("seller_state", safe_mode)
    )
    .reset_index()
)

tmp = order_items_enriched.merge(orders[["order_id","order_purchase_timestamp"]],
                                 on="order_id", how="left")
tmp["shipping_limit_gap_days"] = to_days(tmp["shipping_limit_date"] - tmp["order_purchase_timestamp"])
ship_gap = (tmp.groupby("order_id", as_index=False)["shipping_limit_gap_days"]
            .mean().rename(columns={"shipping_limit_gap_days":"avg_shipping_limit_gap_days"}))

# ---------------------
# Base frame and label
# ---------------------
df = orders[[
    "order_id","customer_id","order_status",
    "order_purchase_timestamp","order_approved_at",
    "order_delivered_carrier_date","order_delivered_customer_date",
    "order_estimated_delivery_date"
]].copy()

# Keep only delivered to compute a clean label (you can relax this if needed)
df = df[df["order_status"]=="delivered"].copy()

df["order_weekday"] = df["order_purchase_timestamp"].dt.weekday
df["order_month"] = df["order_purchase_timestamp"].dt.month
df["is_weekend_purchase"] = df["order_weekday"].isin([5,6]).astype("int8")
df["SLA_days"] = to_days(df["order_estimated_delivery_date"] - df["order_purchase_timestamp"])
df["approval_delay_days"] = to_days(df["order_approved_at"] - df["order_purchase_timestamp"])

df["late_delivery"] = (df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]).astype("int8")

# Join aggregates
df = (df.merge(item_agg, on="order_id", how="left")
        .merge(ship_gap, on="order_id", how="left"))

# ---------------------
# Customer geos, seller state, distance
# ---------------------
df = df.merge(cust_geo, on="customer_id", how="left")

# If single seller, use its state; otherwise mark MULTI
df["seller_state"] = np.where(df["n_sellers"].fillna(0)==1, df["seller_state_mode"], "MULTI")
df["same_state"] = (df["seller_state"] == df["customer_state"]).astype("int8")

seller_loc_per_order = (order_items_enriched.groupby("order_id", as_index=False)
                        .agg(sell_lat_mean=("sell_lat","mean"),
                             sell_lng_mean=("sell_lng","mean")))
df = df.merge(seller_loc_per_order, on="order_id", how="left")
df["geo_distance_km"] = haversine_np(df["cust_lat"], df["cust_lng"],
                                     df["sell_lat_mean"], df["sell_lng_mean"])

# ---------------------
# Historical seller delay rate (cumulative, shifted)
# ---------------------
order_sellers = (order_items[["order_id","seller_id"]].drop_duplicates()
                 .merge(df[["order_id","order_purchase_timestamp","late_delivery"]],
                        on="order_id", how="left")
                 .sort_values(["seller_id","order_purchase_timestamp"]))

order_sellers["cum_orders"] = order_sellers.groupby("seller_id").cumcount()
order_sellers["cum_late"] = order_sellers.groupby("seller_id")["late_delivery"].cumsum().shift(1).fillna(0)
order_sellers["cum_total"] = order_sellers["cum_orders"].replace(0, np.nan).astype(float)
order_sellers["seller_delay_rate_hist"] = (order_sellers["cum_late"] / order_sellers["cum_total"]).fillna(0.0)

seller_hist = (order_sellers.groupby("order_id", as_index=False)["seller_delay_rate_hist"].mean())
df = df.merge(seller_hist, on="order_id", how="left")

# ---------------------
# Historical review features (per seller, as of order time)
# ---------------------
rev = (reviews.merge(orders[["order_id","order_purchase_timestamp"]], on="order_id", how="left")
             .merge(order_items[["order_id","seller_id"]].drop_duplicates(), on="order_id", how="left")
             .dropna(subset=["seller_id"]))

rev = rev.sort_values(["seller_id","review_creation_date"])
rev["cum_n"] = rev.groupby("seller_id").cumcount()
rev["cum_sum"] = rev.groupby("seller_id")["review_score"].cumsum().shift(1).fillna(0)
rev["seller_avg_review_hist"] = (rev["cum_sum"] / rev["cum_n"].replace(0, np.nan)).fillna(0.0)

rev["is_bad"] = (rev["review_score"]<=2).astype(int)
rev["cum_bad"] = rev.groupby("seller_id")["is_bad"].cumsum().shift(1).fillna(0)
rev["seller_bad_review_rate_hist"] = (rev["cum_bad"] / rev["cum_n"].replace(0, np.nan)).fillna(0.0)

# asof per seller
features = []
for sid, grp in df[["order_id","order_purchase_timestamp"]].merge(
        order_items[["order_id","seller_id"]].drop_duplicates(), on="order_id", how="left"
    ).groupby("seller_id"):
    hist = rev[rev["seller_id"]==sid][["review_creation_date","seller_avg_review_hist","seller_bad_review_rate_hist"]]
    if hist.empty:
        g = grp.copy()
        g["seller_avg_review_hist_at_order"] = 0.0
        g["seller_bad_review_rate_hist_at_order"] = 0.0
    else:
        tmp = pd.merge_asof(
            grp.sort_values("order_purchase_timestamp"),
            hist.sort_values("review_creation_date"),
            left_on="order_purchase_timestamp",
            right_on="review_creation_date",
            direction="backward"
        )
        g = tmp.copy()
        g["seller_avg_review_hist_at_order"] = g["seller_avg_review_hist"].fillna(0.0)
        g["seller_bad_review_rate_hist_at_order"] = g["seller_bad_review_rate_hist"].fillna(0.0)
    features.append(g[["order_id","seller_avg_review_hist_at_order","seller_bad_review_rate_hist_at_order"]])

rev_order = (pd.concat(features, ignore_index=True)
               .groupby("order_id", as_index=False)
               .agg(avg_review_score_hist=("seller_avg_review_hist_at_order","mean"),
                    bad_review_rate_hist=("seller_bad_review_rate_hist_at_order","mean")))
df = df.merge(rev_order, on="order_id", how="left")

# ---------------------
# Final feature clean-up
# ---------------------
df["avg_product_volume_cm3"] = df["avg_product_length_cm"] * df["avg_product_height_cm"] * df["avg_product_width_cm"]
df["is_holiday_period"] = (df["order_month"]==12).astype("int8")

final_cols = [
    "order_id",
    "order_purchase_timestamp",
    "order_weekday","order_month","SLA_days","approval_delay_days",
    "n_items","n_sellers","total_price","total_freight","avg_shipping_limit_gap_days",
    "customer_state","seller_state","same_state","geo_distance_km",
    "avg_product_weight_g","avg_product_volume_cm3","product_category_mode",
    "seller_delay_rate_hist","avg_review_score_hist","bad_review_rate_hist",
    "is_weekend_purchase","is_holiday_period",
    "late_delivery"
]
final = df[final_cols].copy()

final.to_csv(OUTFILE, index=False, encoding="utf-8")
print(f"Saved dataset with shape {final.shape} to {OUTFILE}")
