
import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import initialize_database
from modules.business_selector import select_business
from modules.sales_analytics import get_sales_analysis
from modules.storage import get_sales_data


st.set_page_config(
    page_title="Sales Trends | BizAdvisor AI",
    page_icon="📈",
    layout="wide",
)

initialize_database()

st.title("📈 Sales Trends & Product Performance")
st.caption(
    "Explore recorded sales over time and understand "
    "which products contribute most to revenue."
)

# --------------------------------------------------
# 1. SHARED BUSINESS SELECTION
# --------------------------------------------------

business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar to analyse its sales trends."
    )
    st.stop()

business_id = int(business["business_id"])
currency = business.get("currency") or "INR"

st.caption(f"Analysing sales for: **{business['business_name']}**")

# --------------------------------------------------
# 2. LOAD SALES DATA
# --------------------------------------------------

try:
    all_sales = get_sales_data(business_id)
except Exception as exc:
    st.error(f"Unable to load sales data: {exc}")
    st.stop()

if all_sales.empty:
    st.info(
        "No sales records are available yet. Add sales in Data Import "
        "to start analysing trends."
    )
    st.stop()

if "transaction_date" not in all_sales.columns:
    st.error("The sales data does not contain a transaction_date column.")
    st.stop()

valid_dates = pd.to_datetime(
    all_sales["transaction_date"],
    errors="coerce",
).dropna()

if valid_dates.empty:
    st.warning("No valid sales dates were found.")
    st.stop()

minimum_date = valid_dates.min().date()
maximum_date = valid_dates.max().date()

# --------------------------------------------------
# 3. REPORTING PERIOD
# --------------------------------------------------

st.divider()
st.subheader("Reporting Period")

date_mode = st.radio(
    "Choose a period",
    ["All Recorded Data", "Custom Date Range"],
    horizontal=True,
    key="sales_trends_date_mode",
)

if date_mode == "Custom Date Range":
    date_col1, date_col2 = st.columns(2)

    with date_col1:
        start_date = st.date_input(
            "Start Date",
            value=minimum_date,
            min_value=minimum_date,
            max_value=maximum_date,
            key="sales_trends_start_date",
        )

    with date_col2:
        end_date = st.date_input(
            "End Date",
            value=maximum_date,
            min_value=minimum_date,
            max_value=maximum_date,
            key="sales_trends_end_date",
        )

    if start_date > end_date:
        st.error("Start Date cannot be after End Date.")
        st.stop()
else:
    start_date = None
    end_date = None

# --------------------------------------------------
# 4. SALES ANALYSIS
# --------------------------------------------------

try:
    analysis = get_sales_analysis(
        business_id=business_id,
        start_date=start_date,
        end_date=end_date,
    )
except Exception as exc:
    st.error(f"Unable to analyse sales data: {exc}")
    st.stop()

sales = analysis.get("sales", pd.DataFrame())

if not isinstance(sales, pd.DataFrame) or sales.empty:
    st.info("No sales were recorded in this reporting period.")
    st.stop()

total_revenue = float(analysis.get("total_revenue", 0) or 0)
total_units = float(analysis.get("total_units", 0) or 0)
transaction_count = int(analysis.get("transaction_count", 0) or 0)

# --------------------------------------------------
# 5. SALES SUMMARY
# --------------------------------------------------

st.divider()
st.subheader("Sales Summary")

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "Total Revenue",
    f"{currency} {total_revenue:,.2f}",
)

metric2.metric(
    "Units Sold",
    f"{total_units:,.0f}",
)

metric3.metric(
    "Sales Records",
    f"{transaction_count:,}",
)

# --------------------------------------------------
# 6. DAILY REVENUE TREND
# --------------------------------------------------

st.divider()
st.subheader("Daily Revenue Trend")

daily_sales = analysis.get("daily_sales", pd.DataFrame())

if (
    isinstance(daily_sales, pd.DataFrame)
    and not daily_sales.empty
    and {"transaction_date", "revenue"}.issubset(daily_sales.columns)
):
    fig_daily = px.line(
        daily_sales,
        x="transaction_date",
        y="revenue",
        markers=True,
        title="Revenue by Recorded Sales Day",
    )

    fig_daily.update_layout(
        xaxis_title="Date",
        yaxis_title=f"Revenue ({currency})",
    )

    st.plotly_chart(fig_daily, use_container_width=True)
else:
    st.info("Daily revenue data is not available for this period.")

# --------------------------------------------------
# 7. MONTHLY REVENUE
# --------------------------------------------------

st.divider()
st.subheader("Monthly Revenue")

monthly_sales = analysis.get("monthly_sales", pd.DataFrame())

if isinstance(monthly_sales, pd.DataFrame) and not monthly_sales.empty:
    if {"month", "revenue"}.issubset(monthly_sales.columns):
        if len(monthly_sales) >= 2:
            fig_monthly = px.bar(
                monthly_sales,
                x="month",
                y="revenue",
                text_auto=".2f",
                title="Monthly Revenue Comparison",
            )

            fig_monthly.update_layout(
                xaxis_title="Month",
                yaxis_title=f"Revenue ({currency})",
            )

            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info(
                "At least two recorded months are needed for a meaningful "
                "monthly comparison. The monthly summary is shown below."
            )

        st.dataframe(
            monthly_sales,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Monthly Revenue CSV",
            data=monthly_sales.to_csv(index=False).encode("utf-8"),
            file_name=f"monthly_revenue_{business_id}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Monthly sales data is missing expected columns.")
else:
    st.info("Monthly revenue data is not available for this period.")

# --------------------------------------------------
# 8. PRODUCT PERFORMANCE
# --------------------------------------------------

st.divider()
st.subheader("Product Performance")

product_sales = analysis.get("product_sales", pd.DataFrame())

if isinstance(product_sales, pd.DataFrame) and not product_sales.empty:
    required_columns = {"product_name", "revenue"}

    if required_columns.issubset(product_sales.columns):
        product_sales = product_sales.copy()

        product_sales["revenue"] = pd.to_numeric(
            product_sales["revenue"],
            errors="coerce",
        ).fillna(0)

        product_sales = product_sales.sort_values(
            "revenue",
            ascending=False,
        )

        fig_products = px.bar(
            product_sales.head(10).sort_values("revenue"),
            x="revenue",
            y="product_name",
            orientation="h",
            text_auto=".2f",
            title="Top Products by Recorded Revenue",
        )

        fig_products.update_layout(
            xaxis_title=f"Revenue ({currency})",
            yaxis_title="Product",
        )

        st.plotly_chart(fig_products, use_container_width=True)

        st.dataframe(
            product_sales,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Product Performance CSV",
            data=product_sales.to_csv(index=False).encode("utf-8"),
            file_name=f"product_performance_{business_id}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Product performance data is missing expected columns.")
else:
    st.info("Product performance data is not available for this period.")

# --------------------------------------------------
# 9. SALES INSIGHTS
# --------------------------------------------------

st.divider()
st.subheader("Sales Insights")

best_day = analysis.get("best_day")
weakest_day = analysis.get("weakest_day")

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.markdown("**Highest-revenue recorded day**")

    if best_day is not None:
        st.metric(
            "Date",
            str(best_day["transaction_date"]),
            help="Highest total among dates with recorded sales.",
        )
        st.write(
            f"Revenue: {currency} "
            f"{float(best_day['revenue']):,.2f}"
        )
        st.write(
            f"Sales records: {best_day['transactions']}"
        )
    else:
        st.info("No highest-revenue day is available.")

with insight_col2:
    st.markdown("**Lowest-revenue recorded day**")

    if weakest_day is not None:
        st.metric(
            "Date",
            str(weakest_day["transaction_date"]),
            help="Lowest total among dates with recorded sales.",
        )
        st.write(
            f"Revenue: {currency} "
            f"{float(weakest_day['revenue']):,.2f}"
        )
        st.write(
            f"Sales records: {weakest_day['transactions']}"
        )
    else:
        st.info("No lowest-revenue day is available.")

st.caption(
    "These insights describe recorded data only. Missing sales records "
    "may represent closed days or incomplete data entry."
)
