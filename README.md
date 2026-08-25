
# Customer Retention Prioritizer

A portfolio project that turns transaction data into a **management decision**:

> If the retailer has limited retention budget, which customers should it contact first?
>
> https://customer-retention-analytics-optimal-impact.streamlit.app/

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

## Portfolio talking point

> Built an end-to-end customer retention prioritization tool using 500K+ public
> retail transactions; cleaned transaction data, created RFM customer features,
> queried KPIs in SQL, and developed an interactive dashboard to identify
> high-value customers showing signs of lapse.

## Good extensions

- Build a churn proxy and classification model.
- Add cohort-level retention benchmarks.
- Test alternative priority-weight scenarios.
- Build market-specific retention strategies.
- Add product affinity / next-best-product recommendations.
