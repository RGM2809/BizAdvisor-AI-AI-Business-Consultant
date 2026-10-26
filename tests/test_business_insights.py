
import pandas as pd

from modules import business_insights


def mock_sales_analysis(business_id, start_date=None, end_date=None):
    return {
        "sales": pd.DataFrame(),
        "daily_sales": pd.DataFrame(),
        "monthly_sales": pd.DataFrame(),
        "product_sales": pd.DataFrame([
            {
                "product_name": "Coffee",
                "units_sold": 5,
                "revenue": 500.0,
                "transaction_count": 3,
            }
        ]),
        "total_revenue": 500.0,
        "total_units": 5.0,
        "transaction_count": 3,
        "best_day": {
            "transaction_date": "2026-10-20",
            "revenue": 500.0,
            "transactions": 3,
        },
        "weakest_day": {
            "transaction_date": "2026-10-20",
            "revenue": 500.0,
            "transactions": 3,
        },
    }


def mock_financial_summary(
    business_id,
    start_date=None,
    end_date=None,
):
    return {
        "revenue": 500.0,
        "expenses": 200.0,
        "operating_result": 300.0,
        "operating_margin_pct": 60.0,
        "sales_records": 3,
        "expense_records": 1,
        "has_expense_data": True,
    }


def test_generates_top_product_insight(monkeypatch):
    monkeypatch.setattr(
        business_insights,
        "get_sales_analysis",
        mock_sales_analysis,
    )
    monkeypatch.setattr(
        business_insights,
        "calculate_financial_summary",
        mock_financial_summary,
    )
    monkeypatch.setattr(
        business_insights,
        "get_expenses",
        lambda *args, **kwargs: pd.DataFrame(
            columns=["expense_id", "expense_date", "category",
                     "amount", "description"]
        ),
    )

    insights = business_insights.generate_business_insights(1)

    assert any(
        item["title"] == "Top revenue-generating product"
        for item in insights
    )


def test_generates_operating_loss_warning(monkeypatch):
    monkeypatch.setattr(
        business_insights,
        "get_sales_analysis",
        mock_sales_analysis,
    )
    monkeypatch.setattr(
        business_insights,
        "calculate_financial_summary",
        lambda *args, **kwargs: {
            **mock_financial_summary(1),
            "revenue": 100.0,
            "expenses": 200.0,
            "operating_result": -100.0,
            "operating_margin_pct": -100.0,
        },
    )
    monkeypatch.setattr(
        business_insights,
        "get_expenses",
        lambda *args, **kwargs: pd.DataFrame(
            columns=["expense_id", "expense_date", "category",
                     "amount", "description"]
        ),
    )

    insights = business_insights.generate_business_insights(1)

    assert any(
        item["title"] == "Recorded expenses exceed revenue"
        for item in insights
    )


def test_handles_no_sales_data(monkeypatch):
    monkeypatch.setattr(
        business_insights,
        "get_sales_analysis",
        lambda *args, **kwargs: {
            "sales": pd.DataFrame(),
            "daily_sales": pd.DataFrame(),
            "monthly_sales": pd.DataFrame(),
            "product_sales": pd.DataFrame(
                columns=["product_name", "units_sold", "revenue",
                         "transaction_count"]
            ),
            "total_revenue": 0.0,
            "total_units": 0.0,
            "transaction_count": 0,
            "best_day": None,
            "weakest_day": None,
        },
    )
    monkeypatch.setattr(
        business_insights,
        "calculate_financial_summary",
        lambda *args, **kwargs: {
            "revenue": 0.0,
            "expenses": 0.0,
            "operating_result": 0.0,
            "operating_margin_pct": None,
            "sales_records": 0,
            "expense_records": 0,
            "has_expense_data": False,
        },
    )
    monkeypatch.setattr(
        business_insights,
        "get_expenses",
        lambda *args, **kwargs: pd.DataFrame(
            columns=["expense_id", "expense_date", "category",
                     "amount", "description"]
        ),
    )

    insights = business_insights.generate_business_insights(1)

    assert any(
        item["title"] == "No sales data available"
        for item in insights
    )
