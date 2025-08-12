
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Supply Chain Scenario Copilot Demo - Ajitesh", page_icon="🚢", layout="wide")

st.title("🚢 Supply Chain Scenario Copilot by Ajitesh Das")
st.write("Upload a SKU list, adjust tariff scenarios and FX, and see landed cost impact and savings opportunities.")
st.link_button("📬 Contact me", "mailto:ajiteshdas@gmail.com")

with st.expander("📄 Expected CSV format"):
    st.code("""sku,product_name,base_cost,supplier_country,hs_code,annual_units
SKU-001,Widget A,12.5,China,850440,20000
SKU-002,Widget B,8.2,Vietnam,850440,15000
...""", language="text")

@st.cache_data
def load_sample():
    return pd.read_csv("sample_data.csv")

uploaded = st.file_uploader("Upload SKU CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    st.caption("No file uploaded — using sample dataset.")
    df = load_sample()

required = {"sku","product_name","base_cost","supplier_country","hs_code","annual_units"}
missing = required - set([c.lower() for c in df.columns])
df.columns = [c.lower() for c in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}. Expected {sorted(list(required))}.")
    st.stop()

# Basic cleaning
df["base_cost"] = pd.to_numeric(df["base_cost"], errors="coerce").fillna(0.0)
df["annual_units"] = pd.to_numeric(df["annual_units"], errors="coerce").fillna(0).astype(int)
df["supplier_country"] = df["supplier_country"].fillna("Unknown")

st.sidebar.header("Scenario Settings")
st.sidebar.caption("Adjust and compare against the baseline.")

# Build default tariff map from common manufacturing countries
default_tariffs = {
    "China": 0.20,
    "Vietnam": 0.08,
    "India": 0.10,
    "Mexico": 0.05,
    "USA": 0.00,
    "Thailand": 0.06,
    "Malaysia": 0.05,
    "Indonesia": 0.07,
    "Taiwan": 0.04,
    "Unknown": 0.00,
}

# Add any countries from data with a sensible default if absent
for c in sorted(df["supplier_country"].unique()):
    default_tariffs.setdefault(c, 0.05)

st.sidebar.subheader("Tariff rates by country")
country_rates = {}
for c in sorted(default_tariffs.keys()):
    country_rates[c] = st.sidebar.number_input(f"{c}", min_value=0.0, max_value=1.0, value=float(default_tariffs[c]), step=0.01, format="%.2f")

fx_adj = st.sidebar.slider("FX impact (global) — multiplier on cost", 0.80, 1.20, 1.00, 0.01)
st.sidebar.caption("Example: 1.05 = currency weakened by 5% (cost up).")

# Calculations
def landed_cost(row, country_map, fx=1.0):
    t = country_map.get(str(row["supplier_country"]), 0.05)
    return float(row["base_cost"]) * (1 + t) * fx

df["baseline_tariff"] = df["supplier_country"].map({k:v for k,v in default_tariffs.items()})
df["baseline_landed_cost"] = df.apply(landed_cost, axis=1, country_map=default_tariffs, fx=1.0)
df["scenario_landed_cost"] = df.apply(landed_cost, axis=1, country_map=country_rates, fx=fx_adj)
df["annual_cost_baseline"] = df["baseline_landed_cost"] * df["annual_units"]
df["annual_cost_scenario"] = df["scenario_landed_cost"] * df["annual_units"]
df["annual_delta"] = df["annual_cost_scenario"] - df["annual_cost_baseline"]

# Alternate supplier recommendation (rule-based): try candidate countries and pick lowest scenario landed cost
candidate_countries = sorted(set(list(default_tariffs.keys()) + ["China","Vietnam","India","Mexico","Thailand","Malaysia","Indonesia","Taiwan","USA"]))
def best_alternative(row):
    current = str(row["supplier_country"])
    current_cost = row["scenario_landed_cost"]
    best_country, best_cost = current, current_cost
    for c in candidate_countries:
        t = country_rates.get(c, 0.05)
        alt_cost = float(row["base_cost"]) * (1 + t) * fx_adj
        if alt_cost < best_cost:
            best_country, best_cost = c, alt_cost
    savings_per_unit = max(0.0, current_cost - best_cost)
    return pd.Series([best_country, best_cost, savings_per_unit])

df[["alt_country","alt_landed_cost","savings_per_unit_if_switch"]] = df.apply(best_alternative, axis=1)
df["annual_savings_if_switch"] = df["savings_per_unit_if_switch"] * df["annual_units"]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("SKUs", len(df))
col2.metric("Annual cost (baseline)", f"${df['annual_cost_baseline'].sum():,.0f}")
col3.metric("Annual cost (scenario)", f"${df['annual_cost_scenario'].sum():,.0f}")
delta_total = df["annual_cost_scenario"].sum() - df["annual_cost_baseline"].sum()
col4.metric("Δ Annual cost", f"${delta_total:,.0f}", delta=f"{(delta_total/df['annual_cost_baseline'].sum()*100 if df['annual_cost_baseline'].sum() else 0):.1f}%")

st.subheader("Impact by SKU (Top 15 increases)")
top_inc = df.sort_values("annual_delta", ascending=False).head(15)
fig1 = px.bar(top_inc, x="sku", y="annual_delta", hover_data=["product_name","supplier_country","annual_units","baseline_landed_cost","scenario_landed_cost"], title="Annual Cost Increase by SKU (Scenario vs Baseline)")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Country Spend Share (Scenario)")
share = df.groupby("supplier_country", as_index=False)["annual_cost_scenario"].sum().sort_values("annual_cost_scenario", ascending=False)
fig2 = px.pie(share, names="supplier_country", values="annual_cost_scenario", title="Spend by Supplier Country (Scenario)")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Recommendations — Switch Sources (Top 15 by Annual Savings)")
recs = df[df["annual_savings_if_switch"] > 0].copy().sort_values("annual_savings_if_switch", ascending=False).head(15)
st.dataframe(
    recs[["sku","product_name","supplier_country","alt_country","savings_per_unit_if_switch","annual_savings_if_switch","baseline_landed_cost","scenario_landed_cost","alt_landed_cost","annual_units"]]
        .rename(columns={
            "supplier_country":"current_country",
            "savings_per_unit_if_switch":"$ saved / unit if switch",
            "annual_savings_if_switch":"Annual $ saved if switch"
        }),
    use_container_width=True, height=360
)

with st.expander("How it works"):
    st.markdown("""
**Baseline** uses default tariff rates per country.  
**Scenario** uses your sidebar rates + a global FX multiplier.

- *Landed cost per unit* = `base_cost × (1 + tariff_rate) × FX`  
- *Annual cost* = `landed_cost × annual_units`  
- *Recommendations* try alternate countries with your scenario rates and show the best option per SKU.

> This is a demo. In production, plug in authoritative tariff tables, real FX feeds, lead-time risk, and supplier constraints.
""")

st.sidebar.markdown("---")
st.sidebar.caption("👋 Built for quick demos. Try editing China/Vietnam/Mexico rates and FX to see portfolio‑ready insights.")
