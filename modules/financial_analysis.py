
import pandas as pd

from modules.storage import get_sales_data
from modules.expense_management import get_expenses


def calculate_financial_summary(
    business_id,
    start_date=None,
    end_date=None,
):
    """Calculate financial totals, expense breakdown, and product performance."""

    # 1. Validate the date range.
    if (
        start_date is not None
        and end_date is not None
        and str(start_date) > str(end_date)
    ):
        raise ValueError("Start date cannot be after end date.")

    # 2. Fetch sales and expenses.
    sales = get_sales_data(business_id).copy()

    expenses = get_expenses(
        business_id,
        start_date=start_date,
        end_date=end_date,
    ).copy()

    # 3. Filter sales by date and calculate revenue.
    if not sales.empty:
        sales["transaction_date"] = pd.to_datetime(
            sales["transaction_date"],
            errors="coerce",
        )

        sales = sales.dropna(subset=["transaction_date"])

        if start_date is not None:
            sales = sales[
                sales["transaction_date"] >= pd.Timestamp(start_date)
            ]

        if end_date is not None:
            sales = sales[
                sales["transaction_date"]
                < pd.Timestamp(end_date) + pd.Timedelta(days=1)
            ]

        sales["total_amount"] = pd.to_numeric(
            sales["total_amount"],
            errors="coerce",
        ).fillna(0)

        revenue = float(sales["total_amount"].sum())
    else:
        revenue = 0.0

    # 4. Calculate expenses and expense category breakdown.
    expense_breakdown = {}

    if not expenses.empty:
        expenses["amount"] = pd.to_numeric(
            expenses["amount"],
            errors="coerce",
        ).fillna(0)

        total_expenses = float(expenses["amount"].sum())

        # A category column may be missing in some datasets.
        if "category" in expenses.columns:
            expenses["category"] = (
                expenses["category"]
                .fillna("Uncategorized")
                .astype(str)
                .str.strip()
                .replace("", "Uncategorized")
            )

            expense_breakdown = (
                expenses.groupby("category")["amount"]
                .sum()
                .sort_values(ascending=False)
                .to_dict()
            )
    else:
        total_expenses = 0.0

    # 5. Calculate operating result and operating margin.
    operating_result = revenue - total_expenses

    if revenue > 0:
        operating_margin = (operating_result / revenue) * 100
    else:
        operating_margin = None

    # 6. Calculate product-wise performance.
    if not sales.empty and "product_name" in sales.columns:
        product_sales = sales.copy()

        product_sales["product_name"] = (
            product_sales["product_name"]
            .fillna("Unknown Product")
            .astype(str)
            .str.strip()
            .replace("", "Unknown Product")
        )

        if "quantity" in product_sales.columns:
            product_sales["quantity"] = pd.to_numeric(
                product_sales["quantity"],
                errors="coerce",
            ).fillna(0)
        else:
            product_sales["quantity"] = 0

        product_summary = product_sales.groupby("product_name").agg(
            revenue=("total_amount", "sum"),
            units_sold=("quantity", "sum"),
        )

        if "transaction_id" in product_sales.columns:
            transaction_counts = (
                product_sales.groupby("product_name")["transaction_id"]
                .count()
                .rename("transaction_count")
            )
        else:
            transaction_counts = (
                product_sales.groupby("product_name")
                .size()
                .rename("transaction_count")
            )

        product_performance = (
            product_summary.join(transaction_counts)
            .sort_values("revenue", ascending=False)
            .reset_index()
        )
    else:
        product_performance = pd.DataFrame(
            columns=[
                "product_name",
                "revenue",
                "units_sold",
                "transaction_count",
            ]
        )

    # 7. Return all calculated results.
    return {
        "revenue": revenue,
        "expenses": total_expenses,
        "operating_result": operating_result,
        "operating_margin_pct": operating_margin,
        "sales_records": len(sales),
        "expense_records": len(expenses),
        "has_expense_data": not expenses.empty,
        "expense_breakdown": expense_breakdown,
        "product_performance": product_performance,
    }
