
# Customer Retention Prioritizer

A portfolio project that turns transaction data into a **management decision**:

> If the retailer has limited retention budget, which customers should it contact first?
>
> Try the live demo here : https://customer-retention-analytics-optimal-impact.streamlit.app/

This project uses the UCI Online Retail dataset to identify which customers may be worth re-engaging.

Data note: The UCI Online Retail dataset was chosen because it provides a large, well-structured public transaction dataset suitable for customer-level analysis. The data covers 2010–2011, so the findings should not be interpreted as reflecting current retail trends. The purpose of the project is to demonstrate the analytical approach and decision framework rather than draw conclusions about today’s market.

## Why this project exists

Many analytics portfolios stop at charts. This project is designed around a real decision. It:

1. downloads a real public retail dataset;
2. audits and cleans transaction-level data;
3. calculates management KPIs;
4. demonstrates SQL analysis;
5. builds customer RFM features;
6. creates practical customer segments;
7. ranks customers by retention priority;
8. visualizes the output in a small Streamlit decision tool.

## Data

**UCI Machine Learning Repository — Online Retail (ID 352)**

- 541,909 transaction rows
- UK-based non-store retailer
- Transactions from Dec 2010 to Dec 2011
- Variables include invoice, product, quantity, date, unit price, customer and country
- License: CC BY 4.0

Citation:
Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository.
DOI: 10.24432/C5BW33

The project downloads the dataset automatically from UCI on first run.

## Skills demonstrated

- Python / pandas
- Data cleaning and quality controls
- Feature engineering
- RFM customer analytics
- KPI design
- Cohort retention
- SQL / SQLite
- Data visualization
- Streamlit
- Business prioritization

## Project structure

```text
customer_retention_portfolio/
├── app.py
├── analysis.ipynb
├── queries.sql
├── requirements.txt
├── README.md
├── src/
│   └── retention_analysis.py
├── data/
└── outputs/
```

## Run it

```bash
pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

To launch the app:

```bash
streamlit run app.py
```

## Business logic

The tool calculates customer-level:

- **Recency** — days since last purchase
- **Frequency** — unique orders
- **Monetary value** — historical revenue
- **Average order value**
- **Product breadth**
- **Retention priority**

The priority score is intentionally interpretable:

```text
50% historical value
20% frequency
30% inactivity/lapse risk
```

A customer becomes a `PriorityTarget` when they are:

- in the top 25% by historical value; and
- in the less-recent half of the customer base.

This is a **business rule**, not a causal claim. A stronger future version could validate the weights through campaign outcomes.

## Project summary

Built a customer retention prioritization tool using 500K+ public retail transactions. The project combines data cleaning, RFM analysis, SQL-based KPI reporting, cohort analysis, and an interactive Streamlit dashboard to identify high-value customers who may be worth re-engaging.

## Possible next steps

Add a churn model if suitable outcome labels can be defined
- Compare retention patterns across countries or customer groups
- Explore product affinities and repeat-purchase behavior
- Test different prioritization rules against campaign-response data
- Add next-best-product recommendations
