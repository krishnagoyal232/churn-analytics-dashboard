# Customer Segmentation & Churn Pattern Analytics — Streamlit Dashboard

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```

The app reads `European_Bank.csv` from the same folder, so keep `app.py`,
`requirements.txt`, and `European_Bank.csv` together.

## What's inside
- **Overall Summary** – churn rate, revenue at risk, product/engagement KPIs
- **Geography** – churn by country, geography × gender, geography × age
- **Age & Tenure** – age/tenure segment churn, age×tenure heatmap, credit band churn
- **High-Value Explorer** – high-value vs standard churn, salary vs balance scatter, revenue at risk
- **Drill-Down** – filterable raw table with CSV export and feature correlation chart

All five sidebar segment filters (geography, gender, age, tenure, balance,
customer value, activity status) update every chart and KPI live.
