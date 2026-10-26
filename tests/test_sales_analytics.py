
import pandas as pd

from modules import sales_analytics


def sample_sales():
    return pd.DataFrame([
        {
            "transaction_id": 1,
            "transaction_date": "2026-10-20",
            "product_name": "Coffee",
            "quantity": 2,
            "unit_price": 100,
            "total_amount": 200,
        },
        {
            "transaction_id": 2,
            "transaction_date": "2026-10-20",
            "product_name": "Tea",
            "quantity": 3,
            "unit_price": 50,
            "total_amount": 150,
        },
        {
            "transaction_id": 3,
            "transaction_date": "2026-10-21",
            "product_name": "Coffee",
            "quantity": 1,
            "unit_price": 100,
            "total_amount": 100,
        },
    ])


def test_sales_totals(monkeypatch):
    monkeypatch.setattr(
        sales_analytics,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    result = sales_analytics.get_sales_analysis(1)

    assert result["total_revenue"] == 450.0
    assert result["total_units"] == 6.0
    assert result["transaction_count"] == 3


def test_daily_and_monthly_sales(monkeypatch):
    monkeypatch.setattr(
        sales_analytics,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    result = sales_analytics.get_sales_analysis(1)

    assert len(result["daily_sales"]) == 2
    assert result["daily_sales"].iloc[0]["revenue"] == 350
    assert result["monthly_sales"].iloc[0]["revenue"] == 450


def test_product_ranking(monkeypatch):
    monkeypatch.setattr(
        sales_analytics,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    result = sales_analytics.get_sales_analysis(1)

    products = result["product_sales"]

    assert products.iloc[0]["product_name"] == "Coffee"
    assert products.iloc[0]["revenue"] == 300
    assert products.iloc[0]["units_sold"] == 3


def test_date_filter(monkeypatch):
    monkeypatch.setattr(
        sales_analytics,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    result = sales_analytics.get_sales_analysis(
        1,
        start_date="2026-10-21",
        end_date="2026-10-21",
    )

    assert result["total_revenue"] == 100.0
    assert result["transaction_count"] == 1


def test_empty_sales(monkeypatch):
    monkeypatch.setattr(
        sales_analytics,
        "get_sales_data",
        lambda business_id: pd.DataFrame(
            columns=[
                "transaction_id",
                "transaction_date",
                "product_name",
                "quantity",
                "unit_price",
                "total_amount",
            ]
        ),
    )

    result = sales_analytics.get_sales_analysis(1)

    assert result["total_revenue"] == 0.0
    assert result["transaction_count"] == 0
    assert result["best_day"] is None
    assert result["weakest_day"] is None
