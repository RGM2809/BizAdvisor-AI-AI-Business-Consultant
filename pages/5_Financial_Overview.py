
import pandas as pd
import plotly.express as px
import streamlit as st

from modules.business_selector import select_business
from modules.financial_analysis import calculate_financial_summary


st.set_page_config(
    page_title="Financial Overview | BizAdvisor AI",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Financial Overview")
st.caption(
    "Review revenue, recorded expenses, operating results, "
    "and product performance for your business."
)

# --------------------------------------------------
# 1. SHARED BUSINESS SELECTION
# --------------------------------------------------

business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar to view its financial data."
    )
    st.stop()

business_id = int(business["business_id"])
business_name = business["business_name"]
currency = business.get("currency") or "INR"

st.caption(f"Financial data for: **{business_name}**")

# --------------------------------------------------
# 2. DATE FILTERS
# --------------------------------------------------

st.subheader("Analysis Period")

date_col1, date_col2 = st.columns(2)

with date_col1:
    use_start_date = st.checkbox(
        "Set start date",
        value=False,
        key="financial_start_enabled",
    )
    start_date = None

    if use_start_date:
        start_date = st.date_input(
            "Start date",
            key="financial_start_date",
        )

with date_col2:
    use_end_date = st.checkbox(
        "Set end date",
        value=False,
        key="financial_end_enabled",
    )
    end_date = None

    if use_end_date:
        end_date = st.date_input(
            "End date",
            key="financial_end_date",
        )

if (
    start_date is not None
    and end_date is not None
    and start_date > end_date
):
    st.error("Start date cannot be later than end date.")
    st.stop()

# --------------------------------------------------
# 3. CALCULATE FINANCIAL SUMMARY
# --------------------------------------------------

try:
    summary = calculate_financial_summary(
        business_id=business_id,
        start_date=start_date,
        end_date=end_date,
    )
except Exception as exc:
    st.error(f"Unable to calculate the financial summary: {exc}")
    st.stop()

revenue = float(summary.get("revenue", 0) or 0)
expenses = float(summary.get("expenses", 0) or 0)
operating_result = float(
    summary.get("operating_result", revenue - expenses) or 0
)

# Support either margin key returned by the analysis module.
margin_value = summary.get(
    "operating_margin_pct",
    summary.get("operating_margin", 0),
)
operating_margin = float(margin_value or 0)

# --------------------------------------------------
# 4. KEY FINANCIAL METRICS
# --------------------------------------------------

st.subheader("Key Financial Metrics")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.metric("Total Revenue", f"{currency} {revenue:,.2f}")

with col2:
    st.metric("Recorded Expenses", f"{currency} {expenses:,.2f}")

with col3:
    st.metric("Operating Result", f"{currency} {operating_result:,.2f}")

with col4:
    st.metric("Operating Margin", f"{operating_margin:.2f}%")

st.caption(
    "The operating result subtracts recorded expenses from revenue. "
    "It is not necessarily net profit."
)

# --------------------------------------------------
# 5. RECORD COUNTS
# --------------------------------------------------

st.subheader("Records Included")

count_col1, count_col2 = st.columns(2)

with count_col1:
    st.metric(
        "Sales Records",
        int(summary.get("sales_records", 0) or 0),
    )

with count_col2:
    st.metric(
        "Expense Records",
        int(summary.get("expense_records", 0) or 0),
    )

# --------------------------------------------------
# 6. EXPENSE CATEGORY BREAKDOWN
# --------------------------------------------------

st.divider()
st.subheader("Expense Breakdown")

expense_breakdown = summary.get("expense_breakdown", {})

if isinstance(expense_breakdown, pd.Series):
    expense_breakdown = expense_breakdown.to_dict()

if isinstance(expense_breakdown, dict):
    expense_df = pd.DataFrame(
        [
            {"Category": category, "Amount": amount}
            for category, amount in expense_breakdown.items()
        ]
    )
elif isinstance(expense_breakdown, pd.DataFrame):
    expense_df = expense_breakdown.copy()
else:
    expense_df = pd.DataFrame()

if not expense_df.empty:
    if {"Category", "Amount"}.issubset(expense_df.columns):
        pass
    elif {"category", "amount"}.issubset(expense_df.columns):
        expense_df = expense_df.rename(
            columns={
                "category": "Category",
                "amount": "Amount",
            }
        )
    else:
        expense_df = expense_df.reset_index()

        if len(expense_df.columns) >= 2:
            expense_df = expense_df.iloc[:, :2].copy()
            expense_df.columns = ["Category", "Amount"]

    if {"Category", "Amount"}.issubset(expense_df.columns):
        expense_df["Amount"] = pd.to_numeric(
            expense_df["Amount"],
            errors="coerce",
        ).fillna(0)

        expense_df = expense_df[expense_df["Amount"] > 0]

        if not expense_df.empty:
            chart_col, table_col = st.columns(2)

            with chart_col:
                st.plotly_chart(
                    px.pie(
                        expense_df,
                        names="Category",
                        values="Amount",
                        title="Expenses by Category",
                        hole=0.4,
                    ),
                    use_container_width=True,
                )

            with table_col:
                st.dataframe(
                    expense_df.sort_values(
                        "Amount",
                        ascending=False,
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            expense_csv = expense_df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Download Expense Breakdown CSV",
                data=expense_csv,
                file_name=f"expense_breakdown_{business_id}.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "No positive recorded expenses are available "
                "for this analysis period."
            )
    else:
        st.warning("Expense breakdown data has an unexpected structure.")
else:
    st.info(
        "No expense-category data is available for this "
        "business and analysis period."
    )

# --------------------------------------------------
# 7. PRODUCT PERFORMANCE
# --------------------------------------------------

st.divider()
st.subheader("Product Performance")

product_df = summary.get("product_performance")

if isinstance(product_df, pd.DataFrame) and not product_df.empty:
    required_columns = {
        "product_name",
        "revenue",
        "units_sold",
        "transaction_count",
    }

    if required_columns.issubset(product_df.columns):
        display_df = product_df.copy()

        for column in [
            "revenue",
            "units_sold",
            "transaction_count",
        ]:
            display_df[column] = pd.to_numeric(
                display_df[column],
                errors="coerce",
            ).fillna(0)

        display_df = display_df.sort_values(
            "revenue",
            ascending=False,
        )

        chart_col, table_col = st.columns(2)

        with chart_col:
            st.plotly_chart(
                px.bar(
                    display_df.head(10),
                    x="product_name",
                    y="revenue",
                    title="Top 10 Products by Revenue",
                    labels={
                        "product_name": "Product",
                        "revenue": f"Revenue ({currency})",
                    },
                ),
                use_container_width=True,
            )

        with table_col:
            st.dataframe(
                display_df.rename(
                    columns={
                        "product_name": "Product",
                        "revenue": "Revenue",
                        "units_sold": "Units Sold",
                        "transaction_count": "Transactions",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        product_csv = display_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Product Performance CSV",
            data=product_csv,
            file_name=f"product_performance_{business_id}.csv",
            mime="text/csv",
        )
    else:
        st.warning(
            "Product performance data is missing one or more "
            "expected columns."
        )
else:
    st.info(
        "No product performance data is available for this "
        "business and analysis period."
    )

# --------------------------------------------------
# 8. BASIC FINANCIAL INTERPRETATION
# --------------------------------------------------

st.divider()
st.subheader("Financial Interpretation")

if revenue == 0 and expenses == 0:
    st.info(
        "No revenue or expenses were recorded for the selected "
        "business and analysis period."
    )
else:
    if operating_result > 0:
        st.success(
            "Recorded revenue exceeds recorded expenses "
            "for this period."
        )
    elif operating_result < 0:
        st.warning(
            "Recorded expenses exceed revenue for this period. "
            "Review expense categories and sales performance."
        )
    else:
        st.info(
            "Recorded revenue and expenses are equal for this period."
        )

    if revenue > 0:
        st.write(
            f"Recorded expenses account for "
            f"{(expenses / revenue) * 100:.2f}% of revenue."
        )
    else:
        st.write(
            "Revenue is zero, so an expense-to-revenue percentage "
            "cannot be calculated."
        )

st.caption(
    "These indicators use recorded data only. Missing transactions, "
    "unrecorded expenses, taxes, inventory costs, and other business "
    "factors may affect actual profitability."
)
