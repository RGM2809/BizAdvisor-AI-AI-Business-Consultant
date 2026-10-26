
import pandas as pd
import streamlit as st

from modules.business_selector import select_business
from modules.sales_analytics import get_sales_data
from modules.expense_management import get_expenses
from modules.business_insights import generate_business_insights
from modules.recommendation_engine import generate_recommendations


st.set_page_config(
    page_title="Business Insights | BizAdvisor AI",
    page_icon="💡",
    layout="wide",
)

st.title("Business Insights & Recommendations")
st.caption(
    "Understand your business performance and discover practical "
    "actions based on your recorded data."
)

# --------------------------------------------------
# 1. SHARED BUSINESS SELECTION
# --------------------------------------------------

business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar to generate its insights "
        "and recommendations."
    )
    st.stop()

business_id = int(business["business_id"])

st.caption(f"Analysing: **{business['business_name']}**")

# --------------------------------------------------
# 2. LOAD SALES AND EXPENSE DATES
# --------------------------------------------------

try:
    sales = get_sales_data(business_id)
    expenses = get_expenses(business_id)
except Exception as exc:
    st.error(f"Unable to load business records: {exc}")
    st.stop()

available_dates = []

if not sales.empty and "transaction_date" in sales.columns:
    sales_dates = pd.to_datetime(
        sales["transaction_date"],
        errors="coerce",
    ).dropna()

    if not sales_dates.empty:
        available_dates.extend(sales_dates.dt.date.tolist())

if not expenses.empty and "expense_date" in expenses.columns:
    expense_dates = pd.to_datetime(
        expenses["expense_date"],
        errors="coerce",
    ).dropna()

    if not expense_dates.empty:
        available_dates.extend(expense_dates.dt.date.tolist())

if not available_dates:
    st.info(
        "No dated sales or expense records were found for this business. "
        "Import sales data or record expenses first."
    )
    st.stop()

min_date = min(available_dates)
max_date = max(available_dates)

# --------------------------------------------------
# 3. SELECT ANALYSIS PERIOD
# --------------------------------------------------

st.subheader("Analysis Period")

date_col1, date_col2 = st.columns(2)

with date_col1:
    start_date = st.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        key="insights_start_date",
    )

with date_col2:
    end_date = st.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        key="insights_end_date",
    )

if start_date > end_date:
    st.error("Start Date cannot be after End Date.")
    st.stop()

# --------------------------------------------------
# 4. GENERATE INSIGHTS AND RECOMMENDATIONS
# --------------------------------------------------

if st.button(
    "Generate Insights & Recommendations",
    type="primary",
    use_container_width=True,
    key="generate_business_insights",
):
    try:
        with st.spinner("Analyzing business performance..."):
            insights = generate_business_insights(
                business_id,
                start_date=start_date,
                end_date=end_date,
            )

            recommendations = generate_recommendations(
                business_id,
                start_date=start_date,
                end_date=end_date,
            )

            st.session_state["business_insights_run"] = {
                "business_id": business_id,
                "start_date": start_date,
                "end_date": end_date,
                "insights": insights,
                "recommendations": recommendations,
            }

    except Exception as exc:
        st.error(f"Unable to generate business insights: {exc}")
        st.stop()

# --------------------------------------------------
# 5. DISPLAY SAVED RESULTS
# --------------------------------------------------

results = st.session_state.get("business_insights_run")

if results and results.get("business_id") == business_id:
    if (
        results.get("start_date") != start_date
        or results.get("end_date") != end_date
    ):
        st.info(
            "Your analysis period changed. Generate insights again "
            "to refresh the results."
        )
        st.stop()

    insights = results.get("insights") or []
    recommendations = results.get("recommendations") or []

    st.divider()

    # ----------------------------------------------
    # BUSINESS INSIGHTS
    # ----------------------------------------------

    st.header("Business Insights")

    if not insights:
        st.info("No additional insights were identified for this period.")
    else:
        positive_count = sum(
            1 for item in insights
            if item.get("type") == "positive"
        )
        warning_count = sum(
            1 for item in insights
            if item.get("type") == "warning"
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Total Insights", len(insights))
        metric2.metric("Positive Insights", positive_count)
        metric3.metric("Warnings", warning_count)

        for insight in insights:
            insight_type = insight.get("type", "info")
            title = insight.get("title", "Business Insight")
            message = insight.get("message", "")
            action = insight.get("recommendation", "")

            with st.container(border=True):
                if insight_type == "positive":
                    st.success(f"**{title}**")
                elif insight_type == "warning":
                    st.warning(f"**{title}**")
                else:
                    st.info(f"**{title}**")

                if message:
                    st.write(message)

                if action:
                    st.write(f"**Suggested action:** {action}")

    # ----------------------------------------------
    # PRIORITIZED RECOMMENDATIONS
    # ----------------------------------------------

    st.divider()
    st.header("Actionable Recommendations")
    st.caption(
        "Recommendations are ranked by priority using your recorded "
        "sales and expense data. They are decision-support suggestions, "
        "not guaranteed outcomes."
    )

    if not recommendations:
        st.info(
            "No specific recommendations were generated for this period."
        )
    else:
        high_count = sum(
            1 for item in recommendations
            if item.get("priority") == "High"
        )
        medium_count = sum(
            1 for item in recommendations
            if item.get("priority") == "Medium"
        )
        low_count = sum(
            1 for item in recommendations
            if item.get("priority") == "Low"
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("High Priority", high_count)
        metric2.metric("Medium Priority", medium_count)
        metric3.metric("Low Priority", low_count)

        priority_styles = {
            "High": st.error,
            "Medium": st.warning,
            "Low": st.info,
        }

        for index, item in enumerate(recommendations, start=1):
            priority = item.get("priority", "Low")
            category = item.get("category", "General")
            title = item.get("title", "Recommendation")
            message = item.get("message", "")
            action = item.get("action", "")

            with st.container(border=True):
                st.subheader(f"{index}. {title}")

                priority_col, category_col = st.columns(2)

                with priority_col:
                    priority_styles.get(priority, st.info)(
                        f"Priority: {priority}"
                    )

                with category_col:
                    st.caption(f"Category: {category}")

                if message:
                    st.write(message)

                if action:
                    st.markdown(f"**Recommended action:** {action}")

    st.divider()
    st.caption(
        f"Analysis period: {start_date} to {end_date}. "
        "Results depend on the completeness and accuracy of your records."
    )

else:
    st.info(
        "Choose an analysis period and click "
        "'Generate Insights & Recommendations' to begin."
    )
