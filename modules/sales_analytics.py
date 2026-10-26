
import pandas as pd

from modules.storage import get_sales_data


def get_sales_analysis(
    business_id,
    start_date=None,
    end_date=None,
):
    """Analyze sales trends and product performance."""

    sales = get_sales_data(business_id).copy()

    if sales.empty:
        return {
            "sales": sales,
            "daily_sales": pd.DataFrame(
                columns=["transaction_date", "revenue", "transactions"]
            ),
            "monthly_sales": pd.DataFrame(
                columns=["month", "revenue", "transactions"]
            ),
            "product_sales": pd.DataFrame(
                columns=[
                    "product_name",
                    "units_sold",
                    "revenue",
                    "transaction_count",
                ]
            ),
            "total_revenue": 0.0,
            "total_units": 0.0,
            "transaction_count": 0,
            "best_day": None,
            "weakest_day": None,
        }

    sales["transaction_date"] = pd.to_datetime(
        sales["transaction_date"],
        errors="coerce",
    )

    sales = sales.dropna(subset=["transaction_date"]).copy()

    sales["total_amount"] = pd.to_numeric(
        sales["total_amount"],
        errors="coerce",
    ).fillna(0)

    sales["quantity"] = pd.to_numeric(
        sales["quantity"],
        errors="coerce",
    ).fillna(0)

    if start_date is not None:
        sales = sales[
            sales["transaction_date"] >= pd.Timestamp(start_date)
        ]

    if end_date is not None:
        sales = sales[
            sales["transaction_date"]
            < pd.Timestamp(end_date) + pd.Timedelta(days=1)
        ]

    if sales.empty:
        return {
            "sales": sales,
            "daily_sales": pd.DataFrame(
                columns=["transaction_date", "revenue", "transactions"]
            ),
            "monthly_sales": pd.DataFrame(
                columns=["month", "revenue", "transactions"]
            ),
            "product_sales": pd.DataFrame(
                columns=[
                    "product_name",
                    "units_sold",
                    "revenue",
                    "transaction_count",
                ]
            ),
            "total_revenue": 0.0,
            "total_units": 0.0,
            "transaction_count": 0,
            "best_day": None,
            "weakest_day": None,
        }

    # Daily revenue and number of recorded sales transactions.
    sales["sales_day"] = sales["transaction_date"].dt.strftime(
        "%Y-%m-%d"
    )

    daily_sales = (
        sales.groupby("sales_day", as_index=False)
        .agg(
            revenue=("total_amount", "sum"),
            transactions=("transaction_id", "count"),
        )
        .rename(columns={"sales_day": "transaction_date"})
        .sort_values("transaction_date")
        .reset_index(drop=True)
    )

    # Monthly revenue and transaction counts.
    sales["sales_month"] = sales["transaction_date"].dt.strftime(
        "%Y-%m"
    )

    monthly_sales = (
        sales.groupby("sales_month", as_index=False)
        .agg(
            revenue=("total_amount", "sum"),
            transactions=("transaction_id", "count"),
        )
        .rename(columns={"sales_month": "month"})
        .sort_values("month")
        .reset_index(drop=True)
    )

    # Product performance.
    product_sales = (
        sales.groupby("product_name", dropna=False, as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
        )
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )

    # The best and weakest days are based on recorded sales days only.
    best_day = daily_sales.loc[
        daily_sales["revenue"].idxmax()
    ].to_dict()

    weakest_day = daily_sales.loc[
        daily_sales["revenue"].idxmin()
    ].to_dict()

    return {
        "sales": sales,
        "daily_sales": daily_sales,
        "monthly_sales": monthly_sales,
        "product_sales": product_sales,
        "total_revenue": float(sales["total_amount"].sum()),
        "total_units": float(sales["quantity"].sum()),
        "transaction_count": int(len(sales)),
        "best_day": best_day,
        "weakest_day": weakest_day,
    }
