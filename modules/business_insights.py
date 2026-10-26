
import pandas as pd

from modules.sales_analytics import get_sales_analysis
from modules.expense_management import get_expenses
from modules.financial_analysis import calculate_financial_summary


def generate_business_insights(
    business_id,
    start_date=None,
    end_date=None,
):
    """Generate rule-based insights from recorded business data."""

    insights = []

    sales_result = get_sales_analysis(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    financial_result = calculate_financial_summary(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    expenses = get_expenses(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    revenue = financial_result["revenue"]
    total_expenses = financial_result["expenses"]
    operating_result = financial_result["operating_result"]
    margin = financial_result["operating_margin_pct"]

    # 1. Check whether sales data exists.
    if sales_result["transaction_count"] == 0:
        insights.append({
            "type": "info",
            "title": "No sales data available",
            "message": (
                "Import or enter sales transactions to receive "
                "sales performance insights."
            ),
            "recommendation": (
                "Add sales records with transaction dates, "
                "products, quantities and amounts."
            ),
        })

    else:
        # 2. Identify the highest-revenue product.
        products = sales_result["product_sales"]

        if not products.empty:
            best_product = products.iloc[0]

            insights.append({
                "type": "positive",
                "title": "Top revenue-generating product",
                "message": (
                    f"{best_product['product_name']} generated "
                    f"₹{best_product['revenue']:,.2f} in recorded revenue."
                ),
                "recommendation": (
                    "Review its sales consistency and availability "
                    "before deciding whether to increase stock."
                ),
            })

        # 3. Identify the strongest recorded sales day.
        best_day = sales_result["best_day"]

        if best_day is not None:
            insights.append({
                "type": "positive",
                "title": "Strongest recorded sales day",
                "message": (
                    f"{best_day['transaction_date']} recorded "
                    f"₹{best_day['revenue']:,.2f} in sales."
                ),
                "recommendation": (
                    "Review staffing, product demand and promotions "
                    "on this day to identify repeatable patterns."
                ),
            })

    # 4. Check operating result.
    if revenue > 0 and operating_result < 0:
        insights.append({
            "type": "warning",
            "title": "Recorded expenses exceed revenue",
            "message": (
                f"Recorded expenses exceed revenue by "
                f"₹{abs(operating_result):,.2f}."
            ),
            "recommendation": (
                "Review expense categories and verify that all sales "
                "and expense records for this period are complete."
            ),
        })

    elif revenue > 0 and operating_result >= 0:
        insights.append({
            "type": "positive",
            "title": "Positive operating result",
            "message": (
                f"Revenue minus recorded expenses is "
                f"₹{operating_result:,.2f}."
            ),
            "recommendation": (
                "Track this result across future periods to determine "
                "whether the performance is consistent."
            ),
        })

    elif revenue == 0 and total_expenses > 0:
        insights.append({
            "type": "warning",
            "title": "Expenses recorded without sales",
            "message": (
                f"₹{total_expenses:,.2f} in expenses were recorded, "
                "but no sales revenue was recorded for this period."
            ),
            "recommendation": (
                "Check whether sales data is missing or whether the "
                "business incurred costs during a no-sales period."
            ),
        })

    # 5. Flag the largest expense category when multiple
    # expense categories are available for comparison.
    if not expenses.empty:
        expenses = expenses.copy()
        expenses["amount"] = pd.to_numeric(
            expenses["amount"],
            errors="coerce",
        ).fillna(0)

        category_totals = (
            expenses.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        if not category_totals.empty and category_totals.sum() > 0:
            largest_category = category_totals.index[0]
            largest_amount = float(category_totals.iloc[0])
            expense_share = (
                largest_amount / category_totals.sum()
            ) * 100

            insights.append({
                "type": "info",
                "title": "Largest recorded expense category",
                "message": (
                    f"{largest_category} accounts for "
                    f"{expense_share:.1f}% of recorded expenses "
                    f"(₹{largest_amount:,.2f})."
                ),
                "recommendation": (
                    "Review this category for possible savings. "
                    "A large share alone does not mean the expense "
                    "is unnecessary."
                ),
            })

    # 6. Warn about a low positive operating margin.
    if margin is not None and 0 <= margin < 10:
        insights.append({
            "type": "warning",
            "title": "Low operating margin",
            "message": (
                f"The operating margin is {margin:.1f}% "
                "based on recorded revenue and expenses."
            ),
            "recommendation": (
                "Review pricing, variable costs and operating "
                "expenses before making changes."
            ),
        })

    return insights
