
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sqlite3
import zipfile

import numpy as np
import pandas as pd
import requests

DATA_URL = "https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip"
DEFAULT_DATA_DIR = Path("data")


def download_dataset(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    """Download and extract the official UCI Online Retail dataset."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = data_dir / "Online Retail.xlsx"

    if xlsx_path.exists():
        return xlsx_path

    response = requests.get(DATA_URL, timeout=90)
    response.raise_for_status()

    with zipfile.ZipFile(BytesIO(response.content)) as zf:
        candidates = [name for name in zf.namelist() if name.lower().endswith(".xlsx")]
        if not candidates:
            raise FileNotFoundError("No .xlsx file found in the downloaded UCI archive.")
        member = candidates[0]
        with zf.open(member) as src, open(xlsx_path, "wb") as dst:
            dst.write(src.read())

    return xlsx_path


def load_raw_data(path: str | Path | None = None) -> pd.DataFrame:
    """Load the retail transactions from Excel."""
    if path is None:
        path = download_dataset()
    df = pd.read_excel(path, engine="openpyxl")
    return df


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return:
      sales: valid completed transactions with identified customers
      audit: one-row dataframe containing data-quality metrics
    """
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]

    required = {
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    }
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")

    out["InvoiceNo"] = out["InvoiceNo"].astype(str).str.strip()
    out["StockCode"] = out["StockCode"].astype(str).str.strip()
    out["InvoiceDate"] = pd.to_datetime(out["InvoiceDate"], errors="coerce")
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce")
    out["UnitPrice"] = pd.to_numeric(out["UnitPrice"], errors="coerce")

    out["IsCancellation"] = out["InvoiceNo"].str.upper().str.startswith("C")
    out["HasCustomerID"] = out["CustomerID"].notna()
    out["ValidPositiveSale"] = (out["Quantity"] > 0) & (out["UnitPrice"] > 0)
    out["Revenue"] = out["Quantity"] * out["UnitPrice"]

    audit = pd.DataFrame({
        "metric": [
            "raw_rows",
            "missing_customer_rows",
            "cancellation_rows",
            "nonpositive_quantity_or_price_rows",
            "invalid_date_rows",
        ],
        "value": [
            len(out),
            int((~out["HasCustomerID"]).sum()),
            int(out["IsCancellation"].sum()),
            int((~out["ValidPositiveSale"]).sum()),
            int(out["InvoiceDate"].isna().sum()),
        ],
    })

    sales = out.loc[
        (~out["IsCancellation"])
        & out["HasCustomerID"]
        & out["ValidPositiveSale"]
        & out["InvoiceDate"].notna()
    ].copy()

    # Customer IDs often arrive as floats from Excel (e.g. 17850.0).
    sales["CustomerID"] = (
        pd.to_numeric(sales["CustomerID"], errors="coerce")
        .astype("Int64")
        .astype(str)
    )
    sales["InvoiceMonth"] = sales["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    sales["OrderDate"] = sales["InvoiceDate"].dt.date

    return sales, audit


def headline_kpis(sales: pd.DataFrame) -> pd.Series:
    orders = sales["InvoiceNo"].nunique()
    customers = sales["CustomerID"].nunique()
    revenue = sales["Revenue"].sum()

    order_totals = sales.groupby("InvoiceNo", as_index=False)["Revenue"].sum()
    customer_orders = sales.groupby("CustomerID")["InvoiceNo"].nunique()

    repeat_rate = (customer_orders.ge(2).mean()) if len(customer_orders) else np.nan

    return pd.Series({
        "Revenue (£)": revenue,
        "Orders": orders,
        "Customers": customers,
        "Average order value (£)": order_totals["Revenue"].mean() if orders else np.nan,
        "Repeat customer rate": repeat_rate,
    })


def monthly_kpis(sales: pd.DataFrame) -> pd.DataFrame:
    order_month = (
        sales.groupby(["InvoiceMonth", "InvoiceNo", "CustomerID"], as_index=False)
        .agg(OrderRevenue=("Revenue", "sum"))
    )

    monthly = (
        order_month.groupby("InvoiceMonth", as_index=False)
        .agg(
            Revenue=("OrderRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            AOV=("OrderRevenue", "mean"),
        )
        .sort_values("InvoiceMonth")
    )
    monthly["RevenueGrowthPct"] = monthly["Revenue"].pct_change() * 100
    return monthly


def build_customer_rfm(
    sales: pd.DataFrame,
    snapshot_date: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Create RFM features, practical segments, and a retention-priority score."""
    if snapshot_date is None:
        snapshot_date = sales["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    customer = (
        sales.groupby("CustomerID", as_index=False)
        .agg(
            LastPurchase=("InvoiceDate", "max"),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Revenue", "sum"),
            Units=("Quantity", "sum"),
            Products=("StockCode", "nunique"),
            Country=("Country", lambda x: x.mode().iat[0] if not x.mode().empty else x.iloc[0]),
        )
    )

    customer["Recency"] = (snapshot_date - customer["LastPurchase"].dt.normalize()).dt.days
    customer["AverageOrderValue"] = customer["Monetary"] / customer["Frequency"]

    # Percentile ranks are robust to tied values and avoid qcut edge-case failures.
    customer["RecencyPct"] = customer["Recency"].rank(method="average", pct=True)
    customer["FrequencyPct"] = customer["Frequency"].rank(method="average", pct=True)
    customer["MonetaryPct"] = customer["Monetary"].rank(method="average", pct=True)

    # Higher R score = more recent; F/M scores = higher frequency/value.
    customer["R"] = np.ceil((1 - customer["RecencyPct"] + 1e-9) * 5).clip(1, 5).astype(int)
    customer["F"] = np.ceil(customer["FrequencyPct"] * 5).clip(1, 5).astype(int)
    customer["M"] = np.ceil(customer["MonetaryPct"] * 5).clip(1, 5).astype(int)

    def segment(row):
        if row["R"] >= 4 and row["F"] >= 4 and row["M"] >= 4:
            return "Champions"
        if row["R"] >= 3 and row["F"] >= 4:
            return "Loyal"
        if row["R"] <= 2 and row["M"] >= 4:
            return "At Risk - High Value"
        if row["R"] >= 4 and row["F"] >= 2:
            return "Potential Loyalist"
        if row["R"] >= 4 and row["F"] == 1:
            return "New"
        if row["R"] <= 2 and row["F"] <= 2:
            return "Hibernating"
        return "Regular"

    customer["Segment"] = customer.apply(segment, axis=1)

    # Retention priority intentionally rewards high value + signs of lapse.
    customer["RetentionPriority"] = (
        100 * (
            0.50 * customer["MonetaryPct"]
            + 0.20 * customer["FrequencyPct"]
            + 0.30 * customer["RecencyPct"]
        )
    ).round(1)

    # A practical shortlist: above-median lapse and top quartile value.
    customer["PriorityTarget"] = (
        (customer["RecencyPct"] >= 0.50)
        & (customer["MonetaryPct"] >= 0.75)
    )

    return customer.sort_values("RetentionPriority", ascending=False)


def build_segment_summary(customer: pd.DataFrame) -> pd.DataFrame:
    return (
        customer.groupby("Segment", as_index=False)
        .agg(
            Customers=("CustomerID", "nunique"),
            Revenue=("Monetary", "sum"),
            AvgRecencyDays=("Recency", "mean"),
            AvgOrders=("Frequency", "mean"),
            AvgCustomerValue=("Monetary", "mean"),
        )
        .assign(
            RevenueShare=lambda d: d["Revenue"] / d["Revenue"].sum()
        )
        .sort_values("Revenue", ascending=False)
    )


def build_cohort_retention(sales: pd.DataFrame) -> pd.DataFrame:
    """Monthly customer cohort retention matrix."""
    tmp = sales[["CustomerID", "InvoiceNo", "InvoiceDate"]].drop_duplicates().copy()
    tmp["OrderMonth"] = tmp["InvoiceDate"].dt.to_period("M")
    first_month = tmp.groupby("CustomerID")["OrderMonth"].min().rename("CohortMonth")
    tmp = tmp.join(first_month, on="CustomerID")
    tmp["CohortIndex"] = (
        (tmp["OrderMonth"].dt.year - tmp["CohortMonth"].dt.year) * 12
        + (tmp["OrderMonth"].dt.month - tmp["CohortMonth"].dt.month)
        + 1
    )

    cohort_counts = (
        tmp.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
        .nunique()
        .unstack(fill_value=0)
    )

    cohort_sizes = cohort_counts.iloc[:, 0]
    retention = cohort_counts.divide(cohort_sizes, axis=0)
    retention.index = retention.index.astype(str)
    return retention


def save_sqlite(sales: pd.DataFrame, path: str | Path = "outputs/retail.db") -> Path:
    """Save clean transactions to SQLite so the project demonstrates SQL as well."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    sql_df = sales.copy()
    sql_df["InvoiceDate"] = sql_df["InvoiceDate"].astype(str)
    sql_df["InvoiceMonth"] = sql_df["InvoiceMonth"].astype(str)
    sql_df["OrderDate"] = sql_df["OrderDate"].astype(str)

    with sqlite3.connect(path) as conn:
        sql_df.to_sql("transactions", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_customer ON transactions(CustomerID)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoice ON transactions(InvoiceNo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON transactions(InvoiceDate)")

    return path
