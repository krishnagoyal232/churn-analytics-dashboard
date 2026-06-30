import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="European Banking | Customer Churn Analytics", layout="wide", page_icon="🏦")

# ---------- Data loading & enrichment ----------
@st.cache_data
def load_data():
    path = Path(__file__).parent / "European_Bank.csv"
    df = pd.read_csv(path)
    df["AgeGroup"] = pd.cut(df["Age"], bins=[0, 30, 45, 60, 150],
                             labels=["<30", "30-45", "46-60", "60+"])
    df["CreditBand"] = pd.cut(df["CreditScore"], bins=[0, 580, 700, 900],
                               labels=["Low", "Medium", "High"])
    df["TenureGroup"] = pd.cut(df["Tenure"], bins=[-1, 2, 6, 20],
                                labels=["New (0-2y)", "Mid-term (3-6y)", "Long-term (7y+)"])
    df["BalanceSeg"] = pd.cut(df["Balance"], bins=[-1, 0, 100000, 1e9],
                               labels=["Zero-balance", "Low-balance (<100k)", "High-balance (100k+)"])
    bal_75 = df["Balance"].quantile(0.75)
    sal_75 = df["EstimatedSalary"].quantile(0.75)
    df["HighValue"] = np.where((df["Balance"] >= bal_75) | (df["EstimatedSalary"] >= sal_75),
                                "High-Value", "Standard")
    df["ChurnLabel"] = df["Exited"].map({1: "Churned", 0: "Retained"})
    df["ActiveLabel"] = df["IsActiveMember"].map({1: "Active", 0: "Inactive"})
    return df

df = load_data()

PRIMARY = "#1f4e79"
ACCENT = "#d9534f"
SAFE = "#5cb85c"
PALETTE = [PRIMARY, ACCENT, "#f0ad4e", SAFE, "#8e44ad", "#17a2b8"]

# ---------- Sidebar filters ----------
st.sidebar.title("🏦 Filters")
st.sidebar.caption("Customer Segmentation & Churn Pattern Analytics")

geo_sel = st.sidebar.multiselect("Geography", sorted(df["Geography"].unique()),
                                  default=sorted(df["Geography"].unique()))
gender_sel = st.sidebar.multiselect("Gender", sorted(df["Gender"].unique()),
                                     default=sorted(df["Gender"].unique()))
age_sel = st.sidebar.multiselect("Age Group", list(df["AgeGroup"].cat.categories),
                                  default=list(df["AgeGroup"].cat.categories))
tenure_sel = st.sidebar.multiselect("Tenure Group", list(df["TenureGroup"].cat.categories),
                                     default=list(df["TenureGroup"].cat.categories))
balance_sel = st.sidebar.multiselect("Balance Segment", list(df["BalanceSeg"].cat.categories),
                                      default=list(df["BalanceSeg"].cat.categories))
hv_sel = st.sidebar.multiselect("Customer Value", sorted(df["HighValue"].unique()),
                                 default=sorted(df["HighValue"].unique()))
active_sel = st.sidebar.multiselect("Activity Status", sorted(df["ActiveLabel"].unique()),
                                     default=sorted(df["ActiveLabel"].unique()))

fdf = df[
    df["Geography"].isin(geo_sel)
    & df["Gender"].isin(gender_sel)
    & df["AgeGroup"].isin(age_sel)
    & df["TenureGroup"].isin(tenure_sel)
    & df["BalanceSeg"].isin(balance_sel)
    & df["HighValue"].isin(hv_sel)
    & df["ActiveLabel"].isin(active_sel)
]

st.sidebar.markdown("---")
st.sidebar.metric("Customers in view", f"{len(fdf):,}", f"of {len(df):,} total")

if len(fdf) == 0:
    st.warning("No customers match the selected filters. Please broaden your selection.")
    st.stop()

# ---------- Header ----------
st.title("Customer Segmentation & Churn Pattern Analytics")
st.caption("European Banking | France · Germany · Spain — Live Analytics Dashboard")

tabs = st.tabs(["📊 Overall Summary", "🌍 Geography", "👥 Age & Tenure",
                 "💰 High-Value Explorer", "🔎 Drill-Down"])

# ============================================================
# TAB 1: Overall churn summary
# ============================================================
with tabs[0]:
    churn_rate = fdf["Exited"].mean() * 100
    total_customers = len(fdf)
    churned = int(fdf["Exited"].sum())
    retained = total_customers - churned
    revenue_at_risk = fdf.loc[fdf["Exited"] == 1, "Balance"].sum()
    pct_revenue_at_risk = revenue_at_risk / fdf["Balance"].sum() * 100 if fdf["Balance"].sum() else 0
    engagement_drop = fdf.loc[fdf["IsActiveMember"] == 0, "Exited"].mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall Churn Rate", f"{churn_rate:.1f}%")
    c2.metric("Total Customers", f"{total_customers:,}")
    c3.metric("Churned Customers", f"{churned:,}")
    c4.metric("Revenue at Risk", f"€{revenue_at_risk/1e6:,.1f}M", f"{pct_revenue_at_risk:.1f}% of balance book")
    c5.metric("Inactive Member Churn", f"{engagement_drop:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns([1, 1.3])

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=["Retained", "Churned"], values=[retained, churned],
            hole=0.55, marker_colors=[SAFE, ACCENT])])
        fig.update_layout(title="Churn vs Retention", height=380,
                           annotations=[dict(text=f"{churn_rate:.1f}%", x=0.5, y=0.5,
                                              font_size=22, showarrow=False)])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        prod_churn = fdf.groupby("NumOfProducts")["Exited"].mean().reset_index()
        prod_churn["Exited"] *= 100
        fig2 = px.bar(prod_churn, x="NumOfProducts", y="Exited",
                       title="Churn Rate by Number of Products Held",
                       labels={"Exited": "Churn Rate (%)", "NumOfProducts": "Number of Products"},
                       color="Exited", color_continuous_scale=["#1f4e79", "#d9534f"])
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        active_churn = fdf.groupby("ActiveLabel")["Exited"].mean().reset_index()
        active_churn["Exited"] *= 100
        fig3 = px.bar(active_churn, x="ActiveLabel", y="Exited", color="ActiveLabel",
                       title="Engagement Drop Indicator: Active vs Inactive",
                       labels={"Exited": "Churn Rate (%)", "ActiveLabel": ""},
                       color_discrete_sequence=[SAFE, ACCENT])
        fig3.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        gender_churn = fdf.groupby("Gender")["Exited"].mean().reset_index()
        gender_churn["Exited"] *= 100
        fig4 = px.bar(gender_churn, x="Gender", y="Exited", color="Gender",
                       title="Churn Rate by Gender",
                       labels={"Exited": "Churn Rate (%)"},
                       color_discrete_sequence=[PRIMARY, "#8e44ad"])
        fig4.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig4, use_container_width=True)

# ============================================================
# TAB 2: Geography
# ============================================================
with tabs[1]:
    st.subheader("Geographic Risk Index")
    geo_summary = fdf.groupby("Geography").agg(
        Customers=("CustomerId", "count"),
        ChurnRate=("Exited", "mean"),
        AvgBalance=("Balance", "mean"),
        RevenueAtRisk=("Balance", lambda s: s[fdf.loc[s.index, "Exited"] == 1].sum())
    ).reset_index()
    geo_summary["ChurnRate"] *= 100

    col1, col2 = st.columns([1, 1])
    with col1:
        fig = px.bar(geo_summary.sort_values("ChurnRate", ascending=False),
                      x="Geography", y="ChurnRate", color="Geography",
                      title="Churn Rate by Country",
                      labels={"ChurnRate": "Churn Rate (%)"},
                      color_discrete_sequence=PALETTE, text_auto=".1f")
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(geo_summary, x="Geography", y="Customers", color="Geography",
                      title="Customer Base Size by Country",
                      color_discrete_sequence=PALETTE, text_auto=True)
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Geography × Gender Interaction")
    gg = fdf.groupby(["Geography", "Gender"])["Exited"].mean().reset_index()
    gg["Exited"] *= 100
    fig = px.bar(gg, x="Geography", y="Exited", color="Gender", barmode="group",
                 title="Churn Rate by Country and Gender",
                 labels={"Exited": "Churn Rate (%)"},
                 color_discrete_sequence=[PRIMARY, "#8e44ad"])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Geography × Age Interaction")
    ga = fdf.groupby(["Geography", "AgeGroup"], observed=True)["Exited"].mean().reset_index()
    ga["Exited"] *= 100
    fig = px.line(ga, x="AgeGroup", y="Exited", color="Geography", markers=True,
                  title="Churn Rate by Age Group across Countries",
                  labels={"Exited": "Churn Rate (%)", "AgeGroup": "Age Group"},
                  color_discrete_sequence=PALETTE)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Country Risk Table")
    st.dataframe(
        geo_summary.assign(
            ChurnRate=lambda d: d["ChurnRate"].round(2).astype(str) + "%",
            AvgBalance=lambda d: "€" + d["AvgBalance"].round(0).astype(int).astype(str),
            RevenueAtRisk=lambda d: "€" + (d["RevenueAtRisk"]/1e6).round(2).astype(str) + "M"
        ),
        use_container_width=True, hide_index=True
    )

# ============================================================
# TAB 3: Age & Tenure
# ============================================================
with tabs[2]:
    col1, col2 = st.columns(2)
    with col1:
        age_churn = fdf.groupby("AgeGroup", observed=True)["Exited"].agg(["mean", "count"]).reset_index()
        age_churn["mean"] *= 100
        fig = px.bar(age_churn, x="AgeGroup", y="mean", color="AgeGroup",
                      title="Churn Rate by Age Segment",
                      labels={"mean": "Churn Rate (%)", "AgeGroup": "Age Group"},
                      color_discrete_sequence=PALETTE, text_auto=".1f")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        tenure_churn = fdf.groupby("TenureGroup", observed=True)["Exited"].mean().reset_index()
        tenure_churn["Exited"] *= 100
        fig = px.bar(tenure_churn, x="TenureGroup", y="Exited", color="TenureGroup",
                      title="Churn Rate by Tenure Group",
                      labels={"Exited": "Churn Rate (%)", "TenureGroup": "Tenure"},
                      color_discrete_sequence=PALETTE, text_auto=".1f")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Age × Tenure Heatmap")
    pivot = fdf.pivot_table(index="AgeGroup", columns="TenureGroup", values="Exited",
                             aggfunc="mean", observed=True) * 100
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="Reds",
                     labels=dict(color="Churn %"),
                     title="Churn Rate (%) — Age Group vs Tenure Group")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Credit Score Band vs Churn")
    cb = fdf.groupby("CreditBand", observed=True)["Exited"].mean().reset_index()
    cb["Exited"] *= 100
    fig = px.bar(cb, x="CreditBand", y="Exited", color="CreditBand",
                  title="Churn Rate by Credit Score Band",
                  labels={"Exited": "Churn Rate (%)"},
                  color_discrete_sequence=PALETTE, text_auto=".1f")
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 4: High-Value Customer Explorer
# ============================================================
with tabs[3]:
    st.subheader("High-Value Customer Churn Explorer")
    st.caption("High-value = top quartile by account balance OR top quartile by estimated salary")

    hv_churn = fdf.groupby("HighValue")["Exited"].agg(["mean", "count"]).reset_index()
    hv_churn["mean"] *= 100

    c1, c2, c3 = st.columns(3)
    hv_rate = fdf.loc[fdf["HighValue"] == "High-Value", "Exited"].mean() * 100 if "High-Value" in fdf["HighValue"].values else 0
    std_rate = fdf.loc[fdf["HighValue"] == "Standard", "Exited"].mean() * 100 if "Standard" in fdf["HighValue"].values else 0
    hv_revenue = fdf.loc[(fdf["HighValue"] == "High-Value") & (fdf["Exited"] == 1), "Balance"].sum()
    c1.metric("High-Value Churn Ratio", f"{hv_rate:.1f}%")
    c2.metric("Standard Churn Rate", f"{std_rate:.1f}%")
    c3.metric("High-Value Revenue Lost", f"€{hv_revenue/1e6:,.1f}M")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(hv_churn, x="HighValue", y="mean", color="HighValue",
                      title="Churn Rate: High-Value vs Standard Customers",
                      labels={"mean": "Churn Rate (%)"},
                      color_discrete_sequence=[ACCENT, PRIMARY], text_auto=".1f")
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(fdf, x="EstimatedSalary", y="Balance", color="ChurnLabel",
                          title="Salary vs Balance — Churn Pattern",
                          opacity=0.55, color_discrete_sequence=[SAFE, ACCENT],
                          labels={"EstimatedSalary": "Estimated Salary (€)", "Balance": "Account Balance (€)"})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### High-Value Churn by Country")
    hvg = fdf[fdf["HighValue"] == "High-Value"].groupby("Geography")["Exited"].agg(["mean", "count"]).reset_index()
    hvg["mean"] *= 100
    fig = px.bar(hvg, x="Geography", y="mean", color="Geography",
                  title="High-Value Customer Churn Rate by Country",
                  labels={"mean": "Churn Rate (%)"},
                  color_discrete_sequence=PALETTE, text_auto=".1f")
    fig.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Balance Segment Breakdown")
    bseg = fdf.groupby("BalanceSeg", observed=True)["Exited"].agg(["mean", "count"]).reset_index()
    bseg["mean"] *= 100
    fig = px.bar(bseg, x="BalanceSeg", y="mean", color="BalanceSeg",
                  title="Churn Rate by Balance Segment",
                  labels={"mean": "Churn Rate (%)", "BalanceSeg": "Balance Segment"},
                  color_discrete_sequence=PALETTE, text_auto=".1f")
    fig.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 5: Drill-down / raw data
# ============================================================
with tabs[4]:
    st.subheader("Segment Drill-Down")
    st.caption("Use the sidebar filters to narrow this table to any customer segment combination.")

    show_cols = ["CustomerId", "Surname", "Geography", "Gender", "Age", "AgeGroup",
                 "Tenure", "TenureGroup", "Balance", "BalanceSeg", "CreditScore", "CreditBand",
                 "NumOfProducts", "HasCrCard", "IsActiveMember", "EstimatedSalary",
                 "HighValue", "ChurnLabel"]
    sorted_fdf = fdf.sort_values("Exited", ascending=False)
    st.dataframe(sorted_fdf[show_cols],
                 use_container_width=True, hide_index=True, height=420)

    csv = fdf[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered segment as CSV", csv,
                        "churn_segment_export.csv", "text/csv")

    st.markdown("---")
    st.markdown("##### Correlation with Churn (numeric features)")
    num_cols = ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts",
                "HasCrCard", "IsActiveMember", "EstimatedSalary", "Exited"]
    corr = fdf[num_cols].corr()["Exited"].drop("Exited").sort_values()
    fig = px.bar(corr, orientation="h", title="Feature Correlation with Churn (Exited)",
                 labels={"value": "Correlation Coefficient", "index": "Feature"},
                 color=corr.values, color_continuous_scale=["#1f4e79", "#d9534f"])
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Customer Segmentation & Churn Pattern Analytics in European Banking | Built with Streamlit")
