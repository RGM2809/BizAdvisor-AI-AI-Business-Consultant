
from modules.financial_analysis import calculate_financial_summary
from modules.storage import get_sales_data
from modules.expense_management import get_expenses


def answer_business_question(business_id, question):
    """Answer common business questions using recorded business data."""

    if business_id is None:
        return "Please select a business first."

    question = (question or "").strip().lower()

    if not question:
        return "Please enter a question about your business."

    try:
        summary = calculate_financial_summary(business_id)
        sales = get_sales_data(business_id).copy()
        expenses = get_expenses(business_id).copy()
    except Exception:
        return "I couldn't retrieve your business data. Please try again."

    revenue = float(summary.get("revenue", 0) or 0)
    total_expenses = float(summary.get("expenses", 0) or 0)
    operating_result = float(
        summary.get("operating_result", revenue - total_expenses) or 0
    )
    currency = "INR"

    def money(amount):
        return f"{currency} {amount:,.2f}"

    # Product-specific questions must come before general revenue questions.
    products = summary.get("product_performance")

    asks_for_units = any(
        phrase in question
        for phrase in [
            "most units",
            "highest quantity",
            "most quantity",
            "quantity sold",
            "units sold",
            "sell the most",
            "sells the most",
            "best selling",
            "best-selling",
            "best seller",
            "top selling",
            "top-selling",
        ]
    )

    asks_for_lowest = any(
        phrase in question
        for phrase in [
            "least revenue",
            "lowest revenue",
            "least sales",
            "lowest sales",
            "generates the least",
            "generates the lowest",
            "worst performing",
            "worst-performing",
        ]
    )

    asks_for_product = (
        any(word in question for word in ["product", "item"])
        or any(
            phrase in question
            for phrase in [
                "best seller",
                "best-selling",
                "best selling",
                "top selling",
                "top-selling",
            ]
        )
    )

    if asks_for_product or (asks_for_units and "revenue" not in question):
        if sales.empty or products is None or products.empty:
            return "No product sales data is available yet."

        if asks_for_units:
            top_units = products.sort_values(
                "units_sold", ascending=False
            ).iloc[0]

            return (
                f"Your best-selling product by quantity is "
                f"{top_units['product_name']}, with "
                f"{float(top_units['units_sold']):,.0f} units sold."
            )

        if asks_for_lowest:
            product = products.sort_values(
                "revenue", ascending=True
            ).iloc[0]

            return (
                f"Your product with the lowest recorded revenue is "
                f"{product['product_name']}, generating "
                f"{money(float(product['revenue']))}."
            )

        top = products.sort_values(
            "revenue", ascending=False
        ).iloc[0]

        return (
            f"Your top product by recorded revenue is "
            f"{top['product_name']}, generating "
            f"{money(float(top['revenue']))}."
        )

    if any(word in question for word in ["revenue", "sales", "turnover"]):
        if sales.empty:
            return "No sales records are available yet."

        return (
            f"Your recorded revenue is {money(revenue)}, "
            f"across {summary['sales_records']} sales records."
        )

    if any(
        word in question
        for word in ["expense", "expenses", "spent", "spending", "cost"]
    ):
        if expenses.empty:
            return "No expenses have been recorded yet."

        breakdown = summary.get("expense_breakdown", {})
        answer = f"Your total recorded expenses are {money(total_expenses)}."

        if breakdown:
            category, amount = max(
                breakdown.items(), key=lambda item: item[1]
            )
            answer += (
                f" Your largest expense category is {category}, "
                f"at {money(amount)}."
            )

        return answer

    if any(word in question for word in ["profit", "loss", "operating result"]):
        if sales.empty and expenses.empty:
            return "There are no recorded sales or expenses to assess yet."

        if operating_result > 0:
            return (
                f"Your recorded operating result is a surplus of "
                f"{money(operating_result)}."
            )

        if operating_result < 0:
            return (
                f"Your recorded operating result is a shortfall of "
                f"{money(abs(operating_result))}. "
                "Your recorded expenses exceed your recorded revenue."
            )

        return "Your recorded revenue and expenses are equal."

    if any(
        phrase in question
        for phrase in [
            "how can i improve",
            "recommend",
            "suggestion",
            "advice",
            "improve my business",
        ]
    ):
        if sales.empty and expenses.empty:
            return (
                "Start by recording your sales and expenses. "
                "I'll use those records to suggest practical improvements."
            )

        suggestions = []

        if operating_result < 0:
            suggestions.append(
                "Review major expenses and look for ways to increase sales "
                "without compromising product quality."
            )

        if products is not None and len(products) >= 2:
            ranked = products.sort_values("revenue", ascending=False)
            top = ranked.iloc[0]
            lowest = ranked.iloc[-1]

            suggestions.append(
                f"Review why {lowest['product_name']} generates less revenue "
                f"than {top['product_name']}; consider demand, pricing, "
                "and promotion before changing stock."
            )

        breakdown = summary.get("expense_breakdown", {})
        if breakdown:
            category, amount = max(
                breakdown.items(), key=lambda item: item[1]
            )
            suggestions.append(
                f"Review the {category} category, currently "
                f"{money(float(amount))}, to identify possible savings."
            )

        if not suggestions:
            suggestions.append(
                "Continue recording sales and expenses consistently so "
                "future recommendations can be based on more evidence."
            )

        return "Based on your recorded data:\n\n- " + "\n\n- ".join(suggestions)

    if any(word in question for word in ["margin", "percentage"]):
        margin = summary.get("operating_margin_pct")

        if margin is None:
            return (
                "An operating margin cannot be calculated because "
                "recorded revenue is zero."
            )

        return f"Your recorded operating margin is {margin:.2f}%."

    return (
        "I can answer questions about revenue, sales, expenses, "
        "operating profit or loss, operating margin, product performance, "
        "and business improvement suggestions. Try asking one of these."
    )
