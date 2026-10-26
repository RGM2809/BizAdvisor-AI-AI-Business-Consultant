
import pandas as pd

from modules import recommendation_engine


def mock_sales_analysis(
    business_id,
    start_date=None,
    end_date=None,
):
    current_revenue = 1000.0

    if start_date is not None and end_date is not None:
        # Simulate the previous period with lower revenue.
        if pd.Timestamp(end_date) < pd.Timestamp("2026-10-01"):
            current_revenue = 1000.0
        else:
            current_revenue = 800.0

    return {
        "sales": pd.DataFrame(),
        "daily_sales": pd.DataFrame(),
        "monthly_sales": pd.DataFrame(),
        "product_sales": pd.DataFrame([
            {
                "product_name": "Coffee",
                "units_sold": 10,
                "revenue": current_revenue,
                "transaction_count": 5,
            },
            {
                "product_name": "Tea",
                "units_sold": 4,
                "revenue": 200.0,
                "transaction_count": 2,
            },
        ]),
        "total_revenue": current_revenue,
        "total_units": 14.0,
        "transaction_count": 7,
        "best_day": None,
        "weakest_day": None,
    }


def mock_financial_summary(
    business_id,
    start_date=None,
    end_date=None,
):
    return {
        "revenue": 800.0,
        "expenses": 300.0,
        "operating_result": 500.0,
        "operating_margin_pct": 62.5,
        "sales_records": 7,
        "expense_records": 2,
        "has_expense_data": True,
    }


def mock_expenses(
    business_id,
    start_date=None,
    end_date=None,
):
    return pd.DataFrame([
        {
            "expense_id": 1,
            "expense_date": "2026-10-20",
            "category": "Rent",
            "amount": 200.0,
            "description": "Monthly rent",
        },
        {
            "expense_id": 2,
            "expense_date": "2026-10-21",
            "category": "Supplies",
            "amount": 100.0,
            "description": "Business supplies",
        },
    ])


def setup_mocks(monkeypatch):
    monkeypatch.setattr(
        recommendation_engine,
        "get_sales_analysis",
        mock_sales_analysis,
    )
    monkeypatch.setattr(
        recommendation_engine,
        "calculate_financial_summary",
        mock_financial_summary,
    )
    monkeypatch.setattr(
        recommendation_engine,
        "get_expenses",
        mock_expenses,
    )


def test_generates_product_recommendation(monkeypatch):
    setup_mocks(monkeypatch)

    recommendations = (
        recommendation_engine.generate_recommendations(1)
    )

    assert any(
        item["category"] == "Products"
        for item in recommendations
    )


def test_generates_expense_category_recommendation(monkeypatch):
    setup_mocks(monkeypatch)

    recommendations = (
        recommendation_engine.generate_recommendations(1)
    )

    assert any(
        item["category"] == "Expenses"
        for item in recommendations
    )


def test_generates_operating_loss_warning(monkeypatch):
    setup_mocks(monkeypatch)

    monkeypatch.setattr(
        recommendation_engine,
        "calculate_financial_summary",
        lambda *args, **kwargs: {
            "revenue": 100.0,
            "expenses": 200.0,
            "operating_result": -100.0,
            "operating_margin_pct": -100.0,
            "sales_records": 1,
            "expense_records": 2,
            "has_expense_data": True,
        },
    )

    recommendations = (
        recommendation_engine.generate_recommendations(1)
    )

    assert any(
        item["priority"] == "High"
        and item["category"] == "Finance"
        for item in recommendations
    )


def test_handles_missing_sales(monkeypatch):
    setup_mocks(monkeypatch)

    monkeypatch.setattr(
        recommendation_engine,
        "get_sales_analysis",
        lambda *args, **kwargs: {
            "sales": pd.DataFrame(),
            "daily_sales": pd.DataFrame(),
            "monthly_sales": pd.DataFrame(),
            "product_sales": pd.DataFrame(),
            "total_revenue": 0.0,
            "total_units": 0.0,
            "transaction_count": 0,
            "best_day": None,
            "weakest_day": None,
        },
    )

    recommendations = (
        recommendation_engine.generate_recommendations(1)
    )

    assert any(
        item["title"] == "Add sales records"
        for item in recommendations
    )


def test_high_priority_recommendations_come_first(monkeypatch):
    setup_mocks(monkeypatch)

    monkeypatch.setattr(
        recommendation_engine,
        "calculate_financial_summary",
        lambda *args, **kwargs: {
            "revenue": 100.0,
            "expenses": 200.0,
            "operating_result": -100.0,
            "operating_margin_pct": -100.0,
            "sales_records": 1,
            "expense_records": 2,
            "has_expense_data": True,
        },
    )

    recommendations = (
        recommendation_engine.generate_recommendations(1)
    )

    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    positions = [
        priority_order[item["priority"]]
        for item in recommendations
    ]

    assert positions == sorted(positions)
