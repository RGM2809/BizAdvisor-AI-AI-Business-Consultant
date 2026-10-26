
"""Rule-based business recommendations for BizAdvisor AI."""

from datetime import timedelta

import pandas as pd

from modules.sales_analytics import get_sales_analysis
from modules.expense_management import get_expenses
from modules.financial_analysis import calculate_financial_summary


def generate_recommendations(
    business_id,
    start_date=None,
    end_date=None,
):
    """Generate prioritized recommendations from recorded data."""

    recommendations = []

    # --------------------------------------------------
    # 1. Load current-period business data
    # --------------------------------------------------
    sales_result = get_sales_analysis(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    financial = calculate_financial_summary(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    expenses = get_expenses(
        business_id,
        start_date=start_date,
        end_date=end_date,
    )

    revenue = float(financial.get("revenue", 0) or 0)
    total_expenses = float(financial.get("expenses", 0) or 0)
    operating_result = float(
        financial.get("operating_result", revenue - total_expenses)
        or 0
    )

    # --------------------------------------------------
    # 2. Missing-data recommendation
    # --------------------------------------------------
    if sales_result["transaction_count"] == 0:
        recommendations.append({
            "priority": "High",
            "category": "Sales",
            "title": "Add sales records",
            "message": (
                "No sales transactions were found for the selected "
                "business and reporting period."
            ),
            "action": (
                "Import or enter dated sales records, including "
                "product names, quantities, and transaction amounts."
            ),
        })

    # --------------------------------------------------
    # 3. Compare revenue with the preceding period
    # --------------------------------------------------
    if start_date is not None and end_date is not None:
        current_start = pd.Timestamp(start_date).normalize()
        current_end = pd.Timestamp(end_date).normalize()

        period_days = (current_end - current_start).days + 1

        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(
            days=period_days - 1
        )

        previous_result = get_sales_analysis(
            business_id,
            start_date=previous_start.date(),
            end_date=previous_end.date(),
        )

        previous_revenue = float(
            previous_result.get("total_revenue", 0) or 0
        )

        current_revenue = float(
            sales_result.get("total_revenue", 0) or 0
        )

        if previous_revenue > 0:
            change_pct = (
                (current_revenue - previous_revenue)
                / previous_revenue
            ) * 100

            if change_pct <= -10:
                recommendations.append({
                    "priority": "High",
                    "category": "Sales",
                    "title": "Revenue has declined",
                    "message": (
                        f"Revenue changed by {change_pct:.1f}% "
                        "compared with the preceding period of "
                        f"{period_days} days."
                    ),
                    "action": (
                        "Review changes in product demand, transaction "
                        "volume, pricing, stock availability, and "
                        "promotions before deciding on corrective action."
                    ),
                })

            elif change_pct >= 10:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Growth",
                    "title": "Revenue is growing",
                    "message": (
                        f"Revenue increased by {change_pct:.1f}% "
                        "compared with the preceding period."
                    ),
                    "action": (
                        "Identify which products or sales activities "
                        "contributed to the increase and check whether "
                        "the trend continues."
                    ),
                })

            else:
                recommendations.append({
                    "priority": "Low",
                    "category": "Sales",
                    "title": "Revenue is relatively stable",
                    "message": (
                        f"Revenue changed by {change_pct:.1f}% "
                        "compared with the preceding period."
                    ),
                    "action": (
                        "Monitor revenue and transaction counts to "
                        "identify meaningful changes over time."
                    ),
                })

        elif current_revenue > 0:
            recommendations.append({
                "priority": "Medium",
                "category": "Sales",
                "title": "Sales recorded in the current period",
                "message": (
                    "Current-period revenue is positive, but the "
                    "preceding period has no positive recorded revenue "
                    "for a percentage comparison."
                ),
                "action": (
                    "Check whether the preceding period's records are "
                    "complete before drawing conclusions about growth."
                ),
            })

    # --------------------------------------------------
    # 4. Operating result
    # --------------------------------------------------
    if revenue > 0 and operating_result < 0:
        recommendations.append({
            "priority": "High",
            "category": "Finance",
            "title": "Review operating shortfall",
            "message": (
                f"Recorded expenses exceed revenue by "
                f"{abs(operating_result):,.2f}."
            ),
            "action": (
                "Review expense records and major cost categories. "
                "Check data completeness before changing prices or "
                "cutting business-critical spending."
            ),
        })

    elif revenue == 0 and total_expenses > 0:
        recommendations.append({
            "priority": "High",
            "category": "Finance",
            "title": "Expenses recorded without revenue",
            "message": (
                f"{total_expenses:,.2f} in expenses were recorded "
                "without recorded sales revenue."
            ),
            "action": (
                "Verify that sales transactions are complete and "
                "review whether these costs were expected for "
                "the selected period."
            ),
        })

    # --------------------------------------------------
    # 5. Product performance
    # --------------------------------------------------
    products = sales_result.get("product_sales")

    if isinstance(products, pd.DataFrame) and not products.empty:
        product_data = products.copy()

        if {"product_name", "revenue"}.issubset(
            product_data.columns
        ):
            product_data["revenue"] = pd.to_numeric(
                product_data["revenue"],
                errors="coerce",
            ).fillna(0)

            product_data = product_data.sort_values(
                "revenue",
                ascending=False,
            )

            if len(product_data) >= 2:
                top_product = product_data.iloc[0]
                lowest_product = product_data.iloc[-1]

                recommendations.append({
                    "priority": "Low",
                    "category": "Products",
                    "title": "Review product performance",
                    "message": (
                        f"{top_product['product_name']} has the highest "
                        f"recorded product revenue "
                        f"({top_product['revenue']:,.2f}), while "
                        f"{lowest_product['product_name']} has the "
                        f"lowest ({lowest_product['revenue']:,.2f})."
                    ),
                    "action": (
                        "Review units sold, margins, stock availability, "
                        "and customer demand before deciding whether "
                        "to promote or change either product."
                    ),
                })

            elif len(product_data) == 1:
                product = product_data.iloc[0]

                recommendations.append({
                    "priority": "Low",
                    "category": "Products",
                    "title": "Track your recorded product",
                    "message": (
                        f"{product['product_name']} generated "
                        f"{product['revenue']:,.2f} in recorded revenue."
                    ),
                    "action": (
                        "Continue tracking sales over time. More product "
                        "data is needed for a meaningful comparison."
                    ),
                })

    # --------------------------------------------------
    # 6. Expense category review
    # --------------------------------------------------
    if (
        isinstance(expenses, pd.DataFrame)
        and not expenses.empty
        and {"category", "amount"}.issubset(expenses.columns)
    ):
        expense_data = expenses.copy()

        expense_data["amount"] = pd.to_numeric(
            expense_data["amount"],
            errors="coerce",
        ).fillna(0)

        category_totals = (
            expense_data.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        total_recorded = float(category_totals.sum())

        if not category_totals.empty and total_recorded > 0:
            category = category_totals.index[0]
            amount = float(category_totals.iloc[0])
            share = amount / total_recorded * 100

            recommendations.append({
                "priority": "Medium" if share >= 50 else "Low",
                "category": "Expenses",
                "title": "Review your largest expense category",
                "message": (
                    f"{category} accounts for {share:.1f}% of "
                    f"recorded expenses ({amount:,.2f})."
                ),
                "action": (
                    "Check invoices, recurring charges, and supplier "
                    "terms to identify potential savings. A large "
                    "expense category is not automatically wasteful."
                ),
            })

    # --------------------------------------------------
    # 7. Prioritize recommendations
    # --------------------------------------------------
    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    recommendations.sort(
        key=lambda item: priority_order[item["priority"]]
    )

    return recommendations
