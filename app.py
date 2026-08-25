import plotly.express as px
import streamlit as st

from retention_analysis import (
    load_raw_data,
    clean_transactions,
    headline_kpis,
    monthly_kpis,
    build_customer_rfm,
    build_segment_summary,
    build_cohort_retention,
)


st.set_page_config(
    page_title="Customer Retention Prioritizer",
    layout="wide"
)

st.title("Customer Retention Prioritizer")

st.caption(
    "Using retail transaction data to identify high-value customers "
    "who may be worth re-engaging."
)


@st.cache_data(show_spinner=False)
def get_data():
    raw = load_raw_data()
    sales, audit = clean_transactions(raw)
    customer = build_customer_rfm(sales)
    monthly = monthly_kpis(sales)

    return sales, audit, customer, monthly


with st.spinner("Loading public UCI data..."):
    sales, audit, customer, monthly = get_data()


# -------------------------
# Filters
# -------------------------

countries = ["All"] + sorted(
    sales["Country"].dropna().unique().tolist()
)

country = st.sidebar.selectbox(
    "Country",
    countries
)

segments = ["All"] + sorted(
    customer["Segment"].unique().tolist()
)

segment = st.sidebar.selectbox(
    "Customer segment",
    segments
)


sales_view = (
    sales
    if country == "All"
    else sales[sales["Country"] == country]
)

customer_view = (
    customer
    if country == "All"
    else customer[customer["Country"] == country]
)

if segment != "All":
    customer_view = customer_view[
        customer_view["Segment"] == segment
    ]


# -------------------------
# Overall KPIs
# -------------------------

kpis = headline_kpis(sales_view)

cols = st.columns(5)

cols[0].metric(
    "Revenue",
    f"£{kpis['Revenue (£)']:,.0f}"
)

cols[1].metric(
    "Orders",
    f"{kpis['Orders']:,.0f}"
)

cols[2].metric(
    "Customers",
    f"{kpis['Customers']:,.0f}"
)

cols[3].metric(
    "AOV",
    f"£{kpis['Average order value (£)']:,.2f}"
)

cols[4].metric(
    "Repeat rate",
    f"{kpis['Repeat customer rate']:.1%}"
)


# -------------------------
# 1. Revenue trend
# -------------------------

st.subheader("1. Revenue trend")

monthly_view = monthly_kpis(sales_view)

fig = px.line(
    monthly_view,
    x="InvoiceMonth",
    y="Revenue",
    markers=True,
    labels={
        "InvoiceMonth": "Month",
        "Revenue": "Revenue (£)"
    },
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# -------------------------
# 2 & 3. Customer analysis
# -------------------------

left, right = st.columns(2)


with left:

    st.subheader("2. Customer mix")

    segment_summary = build_segment_summary(
        customer_view
    )

    fig2 = px.bar(
        segment_summary,
        x="Segment",
        y="Customers",
        hover_data=[
            "Revenue",
            "AvgRecencyDays",
            "AvgOrders"
        ],
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


with right:

    st.subheader("3. Value vs. inactivity")

    sample = customer_view.nlargest(
        min(1500, len(customer_view)),
        "Monetary"
    )

    fig3 = px.scatter(
        sample,
        x="Recency",
        y="Monetary",
        size="Frequency",
        color="Segment",
        hover_data=[
            "CustomerID",
            "RetentionPriority"
        ],
        labels={
            "Recency": "Days since last purchase",
            "Monetary": "Historical customer value (£)",
        },
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


# -------------------------
# 4. Retention targets
# -------------------------

st.subheader(
    "4. Recommended retention targets"
)

targets = (
    customer_view.loc[
        customer_view["PriorityTarget"]
    ]
    .sort_values(
        "RetentionPriority",
        ascending=False
    )
    .loc[:, [
        "CustomerID",
        "Country",
        "Recency",
        "Frequency",
        "Monetary",
        "AverageOrderValue",
        "Segment",
        "RetentionPriority"
    ]]
)

st.dataframe(
    targets.head(100),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Monetary":
            st.column_config.NumberColumn(
                "Historical value",
                format="£%.2f"
            ),

        "AverageOrderValue":
            st.column_config.NumberColumn(
                "AOV",
                format="£%.2f"
            ),

        "RetentionPriority":
            st.column_config.ProgressColumn(
                "Priority score",
                min_value=0,
                max_value=100
            ),
    },
)

st.info(
    "Customers are shortlisted if they are high-value "
    "and relatively inactive. Within that group, they are "
    "ranked using inactivity and past purchase frequency."
)


# -------------------------
# 5. Retention over time
# -------------------------

st.subheader("5. Retention over time")

retention = build_cohort_retention(
    sales_view
)

fig4 = px.imshow(
    retention,
    aspect="auto",
    labels={
        "x": "Months since first purchase",
        "y": "Customer cohort",
        "color": "Retention rate"
    },
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

st.caption(
    "Each row groups customers by the month of their "
    "first purchase and shows the share that returned "
    "in later months."
)


# -------------------------
# 6. Key findings
# -------------------------

st.subheader("6. Key findings")

total_customers = customer[
    "CustomerID"
].nunique()

priority_count = customer[
    "PriorityTarget"
].sum()

priority_share = (
    priority_count / total_customers
)

priority_value = customer.loc[
    customer["PriorityTarget"],
    "Monetary"
].sum()

total_value = customer[
    "Monetary"
].sum()

priority_value_share = (
    priority_value / total_value
)


st.write(
    f"Out of {total_customers:,} customers, "
    f"{priority_count:,} ({priority_share:.1%}) "
    f"were identified as priority retention targets."
)

st.write(
    f"These customers account for approximately "
    f"£{priority_value:,.0f}, or "
    f"{priority_value_share:.1%} of historical "
    f"customer value."
)

st.write(
    "This suggests that retention efforts could focus "
    "on a relatively small group of previously valuable "
    "customers rather than targeting everyone equally."
)
