import io
import joblib
import numpy as np
import pandas as pd
import streamlit as st
import shap
import matplotlib.pyplot as plt

st.set_page_config(page_title="OTIF Early-Warning Dashboard", layout="wide")

# ---------- Load model pipeline ----------
@st.cache_resource(show_spinner=False)
def load_pipeline(path="otif_xgb_pipeline.joblib"):
    pipe = joblib.load(path)  # sklearn Pipeline: preprocessor + XGBClassifier
    pre = pipe.named_steps["pre"]
    model = pipe.named_steps["xgb"]
    # feature names after preprocessing (OHE expands columns)
    try:
        feat_names = pre.get_feature_names_out()
    except Exception:
        # fallback if older sklearn
        feat_names = None
    return pipe, pre, model, feat_names

with st.spinner("Loading model..."):
    pipe, pre, model, feat_names = load_pipeline("otif_xgb_pipeline.joblib")

st.title("🚚 OTIF Early-Warning Dashboard")
st.caption("Score upcoming orders, prioritize high-risk cases, and explain predictions.")

# ---------- Sidebar controls ----------
st.sidebar.header("Upload & Settings")

uploaded = st.sidebar.file_uploader("Upload NEW orders CSV", type=["csv"])
topk_pct = st.sidebar.slider("Review capacity — Top-K% risky orders", 5, 50, 20, step=5)
use_prob_cutoff = st.sidebar.checkbox("Use probability cutoff instead of Top-K", value=False)
prob_cut = st.sidebar.slider("Probability cutoff (late risk ≥)", 0.10, 0.90, 0.50, step=0.05) if use_prob_cutoff else None

# Optional filters will appear after scoring
filter_container = st.sidebar.container()

st.sidebar.markdown("---")
dl_placeholder = st.sidebar.empty()

# ---------- Helper: SHAP explainer (cached) ----------
@st.cache_resource(show_spinner=False)
def get_shap_explainer(_xgb_model):   # leading underscore tells Streamlit not to hash this arg
    return shap.TreeExplainer(_xgb_model)

explainer = get_shap_explainer(model)

# ---------- Main logic ----------
if uploaded is None:
    st.info("Upload a CSV with the **same feature columns** used in training (except `late_delivery`). "
            "It’s okay to include `order_id` and `order_purchase_timestamp` for display.")
    st.markdown("**Tip:** Use your generated `olist_otif_dataset.csv` as a template and drop the `late_delivery` column.")
else:
    # Read data
    new_df = pd.read_csv(uploaded)
    display_cols = [c for c in ["order_id", "order_purchase_timestamp"] if c in new_df.columns]
    st.subheader("Uploaded Data Preview")
    st.dataframe(new_df.head(10), use_container_width=True)

    # Keep a copy for download
    original_df = new_df.copy()

    # Compute probabilities using the same preprocessing + model
    with st.spinner("Scoring orders..."):
        # pipeline handles impute/encode internally
        proba = pipe.predict_proba(new_df.drop(columns=["late_delivery"], errors="ignore"))[:, 1]
        scored = new_df.copy()
        scored["late_risk"] = proba

    # Sidebar filters (dynamic, based on uploaded data)
    with filter_container:
        st.sidebar.subheader("Filters")
        seller_state = st.sidebar.multiselect("Seller state", sorted(scored["seller_state"].dropna().unique().tolist())) if "seller_state" in scored.columns else []
        customer_state = st.sidebar.multiselect("Customer state", sorted(scored["customer_state"].dropna().unique().tolist())) if "customer_state" in scored.columns else []
        product_cat = st.sidebar.multiselect("Product category", sorted(scored["product_category_mode"].dropna().unique().tolist())) if "product_category_mode" in scored.columns else []

    # Apply filters
    filt = pd.Series(True, index=scored.index)
    if seller_state:
        filt &= scored["seller_state"].isin(seller_state)
    if customer_state:
        filt &= scored["customer_state"].isin(customer_state)
    if product_cat:
        filt &= scored["product_category_mode"].isin(product_cat)
    scored_f = scored.loc[filt].reset_index(drop=True)

    # Determine flagged set
    if use_prob_cutoff:
        flagged = scored_f[scored_f["late_risk"] >= prob_cut].copy()
    else:
        k = max(1, int(len(scored_f) * (topk_pct / 100.0)))
        flagged = scored_f.nlargest(k, "late_risk").copy()

    # ---------- KPIs ----------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Orders Scored", f"{len(scored):,}")
    col2.metric("After Filters", f"{len(scored_f):,}")
    col3.metric(("Flagged (≥p)" if use_prob_cutoff else f"Flagged (Top {topk_pct}%)"), f"{len(flagged):,}")
    col4.metric("Avg Risk (Flagged)", f"{flagged['late_risk'].mean():.2f}" if len(flagged) else "—")

    # ---------- Risk leaderboard ----------
    st.subheader("Risk Leaderboard")
    cols_to_show = display_cols + [
        "late_risk", "SLA_days", "geo_distance_km", "seller_delay_rate_hist",
        "n_items", "total_freight", "product_category_mode", "seller_state", "customer_state"
    ]
    cols_to_show = [c for c in cols_to_show if c in flagged.columns]
    st.dataframe(flagged[cols_to_show].sort_values("late_risk", ascending=False), use_container_width=True)

    # Download scored results
    out_csv = scored.sort_values("late_risk", ascending=False).to_csv(index=False).encode("utf-8")
    dl_placeholder.download_button(
        label="⬇️ Download scored results (CSV)",
        data=out_csv,
        file_name="scored_orders_with_risk.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # ---------- SHAP: Global importance ----------
    st.subheader("Global Drivers (Feature Importance via SHAP)")
    # Build a small background sample for SHAP speed
    # Transform features via preprocessor to match model input space
    X_trans = pre.transform(scored_f.drop(columns=["late_delivery"], errors="ignore"))
    # SHAP values for a manageable subset (to keep UI snappy)
    sample_idx = np.random.RandomState(42).choice(X_trans.shape[0], size=min(500, X_trans.shape[0]), replace=False)
    X_plot = X_trans[sample_idx]

    with st.spinner("Computing SHAP values (global)…"):
        shap_vals = explainer.shap_values(X_plot)
        plt.figure()
        shap.summary_plot(shap_vals, X_plot, feature_names=feat_names, show=False, max_display=15)
        st.pyplot(plt.gcf(), clear_figure=True)

    # ---------- SHAP: Per-order explanation ----------
    st.subheader("Per-Order Explanation")
    if len(flagged) == 0:
        st.info("No flagged rows with current filters/threshold.")
    else:
        # Pick an order to explain
        choice = st.selectbox(
            "Select an order to explain",
            options=flagged.index.tolist(),
            format_func=lambda i: f"{flagged.loc[i, 'order_id'] if 'order_id' in flagged.columns else i} | risk={flagged.loc[i, 'late_risk']:.2f}"
        )

        row = flagged.loc[[choice]].drop(columns=["late_delivery"], errors="ignore")
        # Transform with the same preprocessor
        x_row = pre.transform(row)
        with st.spinner("Computing SHAP values (single order)…"):
            sv = explainer.shap_values(x_row)
            # Waterfall/force plot
            st.markdown("**Top feature contributions** (how each feature pushed risk up/down)")
            try:
                shap.plots.waterfall(shap.Explanation(values=sv[0], base_values=explainer.expected_value, data=x_row[0], feature_names=feat_names), max_display=12, show=False)
                st.pyplot(plt.gcf(), clear_figure=True)
            except Exception:
                # Fallback: bar plot of absolute contributions
                contrib = pd.Series(sv[0], index=feat_names if feat_names is not None else np.arange(len(sv[0])))
                top_abs = contrib.abs().sort_values(ascending=False).head(12)
                fig, ax = plt.subplots()
                top_abs.plot.bar(ax=ax)
                ax.set_title("Top absolute SHAP contributions")
                st.pyplot(fig)

        # Show the raw row too
        st.markdown("**Order details**")
        st.dataframe(row.assign(late_risk=flagged.loc[choice, "late_risk"]), use_container_width=True)

    st.markdown("---")
    with st.expander("Data Dictionary (key fields)"):
        st.write("""
        - **late_risk**: model probability that the order will be late
        - **SLA_days**: days from purchase to promised delivery
        - **geo_distance_km**: haversine distance between seller & customer
        - **seller_delay_rate_hist**: historical late rate of seller up to order time
        - **n_items / total_freight**: basket composition & shipping cost proxy
        - **product_category_mode / seller_state / customer_state**: categorical context
        """)
