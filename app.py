import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import initialize_database
from modules.business_selector import select_business
from modules.ui_theme import (
    empty_state,
    page_title,
    recommendation_card,
    render_header,
    style_figure,
)


# =========================================================
# CONFIGURATION, THEME AND BRAND HEADER
# app.py is the entrypoint for every page, so everything
# above navigation.run() is shown on all pages.
# =========================================================

st.set_page_config(
    page_title="BizAdvisor AI",
    page_icon="assets/logo_icon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_header()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

try:
    initialize_database()
except Exception as error:
    st.title("BizAdvisor AI")
    st.error("Unable to initialize the local database.")
    st.exception(error)
    st.stop()


# =========================================================
# HOME DASHBOARD
# =========================================================

def show_home():
    from modules.storage import get_sales_data
    from modules.expense_management import get_expenses
    from modules.financial_analysis import calculate_financial_summary
    from modules.sales_analytics import get_sales_analysis
    from modules.recommendation_engine import generate_recommendations

    page_title(
        "Your business overview",
        "Track recorded sales, understand expenses, and discover "
        "practical opportunities to improve your business.",
    )
    st.caption("Your business. Better decisions.")

    # Existing business-selection mechanism, unchanged.
    try:
        business = select_business()
    except Exception as error:
        st.error("Unable to load the selected business.")
        st.exception(error)
        return

    if business is None:
        empty_state(
            "No business selected",
            "Choose a business from the sidebar to view its dashboard. If you "
            "haven't registered one yet, open Business Management.",
        )
        return

    business_id = int(business["business_id"])
    currency = business.get("currency") or "INR"

    # -----------------------------------------------------
    # Load data
    # -----------------------------------------------------

    try:
        summary = calculate_financial_summary(business_id)
        sales = get_sales_data(business_id).copy()
        expenses = get_expenses(business_id).copy()  # noqa: F841 (kept from original)
    except Exception as error:
        st.error("Unable to load dashboard data.")
        st.exception(error)
        return

    revenue = float(summary.get("revenue", 0) or 0)
    recorded_expenses = float(summary.get("expenses", 0) or 0)
    operating_result = float(
        summary.get("operating_result", revenue - recorded_expenses) or 0
    )
    operating_margin = summary.get("operating_margin_pct")
    sales_records = int(summary.get("sales_records", 0) or 0)

    units_sold = 0.0
    if not sales.empty and "quantity" in sales.columns:
        units_sold = float(
            pd.to_numeric(sales["quantity"], errors="coerce").fillna(0).sum()
        )

    def money(amount):
        return f"{currency} {amount:,.2f}"

    # -----------------------------------------------------
    # Financial KPI cards
    # -----------------------------------------------------

    st.subheader("At a glance")

    col1, col2, col3 = st.columns(3)
    col1.metric("Recorded Revenue", money(revenue))
    col2.metric("Recorded Expenses", money(recorded_expenses))
    col3.metric("Operating Result", money(operating_result))

    col4, col5, col6 = st.columns(3)
    col4.metric(
        "Operating Margin",
        f"{operating_margin:.2f}%" if operating_margin is not None else "N/A",
    )
    col5.metric("Sales Records", f"{sales_records:,}")
    col6.metric("Units Sold", f"{units_sold:,.2f}")

    st.caption(
        "Operating result equals recorded revenue minus recorded "
        "expenses. It is not necessarily net profit; figures depend "
        "on the completeness and period alignment of your records."
    )

    # -----------------------------------------------------
    # Sales trend
    # -----------------------------------------------------

    st.divider()
    st.subheader("Sales performance")

    try:
        analysis = get_sales_analysis(business_id)
        daily_sales = analysis.get("daily_sales", pd.DataFrame())

        if (
            not daily_sales.empty
            and {"transaction_date", "revenue"}.issubset(daily_sales.columns)
        ):
            chart_data = daily_sales.copy()
            chart_data["transaction_date"] = pd.to_datetime(
                chart_data["transaction_date"], errors="coerce"
            )
            chart_data["revenue"] = pd.to_numeric(
                chart_data["revenue"], errors="coerce"
            ).fillna(0)
            chart_data = (
                chart_data.dropna(subset=["transaction_date"])
                .sort_values("transaction_date")
            )

            if not chart_data.empty:
                figure = px.line(
                    chart_data,
                    x="transaction_date",
                    y="revenue",
                    markers=True,
                    labels={
                        "transaction_date": "Date",
                        "revenue": f"Revenue ({currency})",
                    },
                )
                style_figure(figure, title="Daily recorded revenue")
                figure.update_layout(hovermode="x unified")
                st.plotly_chart(figure, use_container_width=True)
            else:
                st.info("No valid sales dates are available to chart.")
        else:
            st.info("Import sales records to see your sales performance trend.")

    except Exception as error:
        st.warning(f"Unable to display the sales trend: {error}")

    # -----------------------------------------------------
    # Expense breakdown
    # -----------------------------------------------------

    st.divider()
    st.subheader("Where your money goes")

    expense_breakdown = summary.get("expense_breakdown", {})
    if isinstance(expense_breakdown, pd.Series):
        expense_breakdown = expense_breakdown.to_dict()

    if isinstance(expense_breakdown, dict) and expense_breakdown:
        expense_df = pd.DataFrame(
            [
                {"Category": category, "Amount": amount}
                for category, amount in expense_breakdown.items()
            ]
        )
        expense_df["Amount"] = pd.to_numeric(
            expense_df["Amount"], errors="coerce"
        ).fillna(0)
        expense_df = expense_df[expense_df["Amount"] > 0]

        if not expense_df.empty:
            chart_col, table_col = st.columns([1.1, 0.9])

            with chart_col:
                expense_figure = px.pie(
                    expense_df,
                    names="Category",
                    values="Amount",
                    hole=0.45,
                )
                style_figure(
                    expense_figure,
                    title="Recorded expenses by category",
                    height=400,
                )
                st.plotly_chart(expense_figure, use_container_width=True)

            with table_col:
                st.markdown("#### Expense details")
                st.dataframe(
                    expense_df.sort_values("Amount", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("No positive recorded expenses are available.")
    else:
        st.info("Record business expenses to see where your money is going.")

    # -----------------------------------------------------
    # Product performance
    # -----------------------------------------------------

    st.divider()
    st.subheader("Product performance")

    product_df = summary.get("product_performance")

    if isinstance(product_df, pd.DataFrame) and not product_df.empty:
        if {"product_name", "revenue"}.issubset(product_df.columns):
            product_df = product_df.copy()
            product_df["revenue"] = pd.to_numeric(
                product_df["revenue"], errors="coerce"
            ).fillna(0)
            product_df = product_df.sort_values(
                "revenue", ascending=False
            ).head(10)

            chart_col, table_col = st.columns([1.1, 0.9])

            with chart_col:
                product_figure = px.bar(
                    product_df,
                    x="product_name",
                    y="revenue",
                    text_auto=".2s",
                    labels={
                        "product_name": "Product",
                        "revenue": f"Revenue ({currency})",
                    },
                )
                style_figure(product_figure, title="Top 10 products by revenue")
                product_figure.update_layout(xaxis_title=None)
                st.plotly_chart(product_figure, use_container_width=True)

            with table_col:
                st.markdown("#### Product details")
                st.dataframe(
                    product_df,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("Product performance data is incomplete.")
    else:
        st.info("No product performance data is available yet.")

    # -----------------------------------------------------
    # Recommendations
    # -----------------------------------------------------

    st.divider()
    st.subheader("Your consultant's suggestions")

    try:
        recommendations = generate_recommendations(business_id)

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        recommendations = sorted(
            recommendations,
            key=lambda item: priority_order.get(item.get("priority", "Low"), 2),
        )

        if recommendations:
            for item in recommendations[:3]:
                st.markdown(
                    recommendation_card(
                        priority=item.get("priority", "Low"),
                        title=item.get("title", "Recommendation"),
                        category=item.get("category", "General"),
                        message=item.get("message", ""),
                        action=item.get("action", ""),
                    ),
                    unsafe_allow_html=True,
                )

            st.caption(
                "Recommendations are data-based suggestions, "
                "not guaranteed business outcomes."
            )
        else:
            st.info("No specific recommendations were generated.")

    except Exception as error:
        st.warning(f"Unable to generate consultant suggestions: {error}")

    st.divider()
    st.caption(
        "BizAdvisor AI · Local-first business analytics · "
        "Figures depend on the completeness of recorded data."
    )


# =========================================================
# GROUPED SIDEBAR NAVIGATION (native Streamlit)
# =========================================================

pages = {
    "Home": [
        st.Page(show_home, title="Home", icon="🏠", default=True),
    ],
    "Business Management": [
        st.Page("pages/1_Business_Profile.py", title="Business Profile", icon="🏢"),
    ],
    "Data": [
        st.Page("pages/2_Data_Import.py", title="Data Import", icon="📥"),
        st.Page("pages/3_Data_Overview.py", title="Data Overview", icon="📊"),
    ],
    "Finance": [
        st.Page("pages/4_Expense_Management.py", title="Expense Management", icon="💸"),
        st.Page("pages/5_Financial_Overview.py", title="Financial Overview", icon="💰"),
        st.Page("pages/6_Sales_Trends.py", title="Sales Trends", icon="📈"),
    ],
    "Insights": [
        st.Page("pages/7_Business_Insights.py", title="Business Insights", icon="💡"),
    ],
    "Forecasting": [
        st.Page("pages/8_Sales_Forecasting.py", title="Sales Forecasting", icon="🔮"),
    ],
    "Assistant": [
        st.Page("pages/9_Business_QA.py", title="Business Q&A", icon="💬"),
    ],
}

navigation = st.navigation(pages)
navigation.run()