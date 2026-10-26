
import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import initialize_database
from modules.business_selector import select_business
from modules.storage import get_sales_data


st.set_page_config(
    page_title="Data Overview",
    page_icon="📊",
    layout="wide",
)

initialize_database()

st.title("📈 Data Overview")
st.write("Review your saved sales records for the selected business.")

# Use the shared business selection.
business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar to view its sales records."
    )
    st.stop()

business_id = int(business["business_id"])
business_name = business["business_name"]
currency = business.get("currency") or "INR"

st.caption(f"Showing data for: **{business_name}**")

# --------------------------------------------------
# Load sales records for the selected business
# --------------------------------------------------

try:
    sales = get_sales_data(business_id).copy()
except Exception as error:
    st.error("Unable to load sales records.")
    st.exception(error)
    st.stop()

if sales.empty:
    st.info("No sales records have been saved for this business yet.")
    st.stop()

# --------------------------------------------------
# Prepare data
# --------------------------------------------------

if "transaction_date" in sales.columns:
    sales["transaction_date"] = pd.to_datetime(
        sales["transaction_date"],
        errors="coerce",
    )

for column in ["total_amount", "quantity"]:
    if column in sales.columns:
        sales[column] = pd.to_numeric(
            sales[column],
            errors="coerce",
        ).fillna(0)

# --------------------------------------------------
# Sales KPIs
# --------------------------------------------------

st.subheader("Sales Summary")

col1, col2, col3 = st.columns(3)

total_sales = (
    float(sales["total_amount"].sum())
    if "total_amount" in sales.columns
    else 0.0
)

units_sold = (
    float(sales["quantity"].sum())
    if "quantity" in sales.columns
    else 0.0
)

col1.metric("Total Sales", f"{currency} {total_sales:,.2f}")
col2.metric("Units Sold", f"{units_sold:,.2f}")
col3.metric("Sales Records", f"{len(sales):,}")

# --------------------------------------------------
# Saved sales records
# --------------------------------------------------

st.divider()
st.subheader("Saved Sales Records")

st.dataframe(
    sales,
    use_container_width=True,
    hide_index=True,
)

# --------------------------------------------------
# Sales by date
# --------------------------------------------------

st.divider()
st.subheader("Sales by Date")

if (
    "transaction_date" in sales.columns
    and "total_amount" in sales.columns
):
    daily = (
        sales.dropna(subset=["transaction_date"])
        .groupby("transaction_date", as_index=False)["total_amount"]
        .sum()
        .sort_values("transaction_date")
    )

    if not daily.empty:
        figure = px.line(
            daily,
            x="transaction_date",
            y="total_amount",
            markers=True,
            title="Recorded Sales by Date",
            labels={
                "transaction_date": "Date",
                "total_amount": f"Sales Amount ({currency})",
            },
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )
    else:
        st.info("No valid transaction dates are available to chart.")
else:
    st.info("Date or sales amount columns are unavailable.")

# --------------------------------------------------
# Sales by product
# --------------------------------------------------

st.divider()
st.subheader("Sales by Product")

if (
    "product_name" in sales.columns
    and "total_amount" in sales.columns
):
    aggregations = {
        "total_sales": ("total_amount", "sum"),
    }

    if "quantity" in sales.columns:
        aggregations["units_sold"] = ("quantity", "sum")

    product_summary = (
        sales.groupby("product_name", as_index=False)
        .agg(**aggregations)
        .sort_values("total_sales", ascending=False)
    )

    st.dataframe(
        product_summary,
        use_container_width=True,
        hide_index=True,
    )

    figure = px.bar(
        product_summary.head(10),
        x="product_name",
        y="total_sales",
        title="Top 10 Products by Sales",
        labels={
            "product_name": "Product",
            "total_sales": f"Sales Amount ({currency})",
        },
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )
else:
    st.info("Product or sales amount columns are unavailable.")

# --------------------------------------------------
# Export
# --------------------------------------------------

st.divider()
st.subheader("Export Sales Records")

csv_data = sales.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Sales Data (CSV)",
    data=csv_data,
    file_name=f"sales_data_business_{business_id}.csv",
    mime="text/csv",
)

st.caption(
    "BizAdvisor AI | Data shown belongs to the selected business."
)
