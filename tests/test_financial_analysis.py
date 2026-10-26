
import pandas as pd
import pytest

import modules.financial_analysis as financial_analysis


@pytest.fixture
def sample_data(monkeypatch):
    sales = pd.DataFrame(
        {
            "transaction_id": [1, 2, 3],
            "transaction_date": [
                "2026-10-01",
                "2026-10-05",
                "2026-10-10",
            ],
            "product_name": ["Coffee", "Tea", "Cake"],
            "quantity": [2, 3, 1],
            "unit_price": [100.0, 50.0, 200.0],
            "total_amount": [200.0, 150.0, 200.0],
        }
    )

    expenses = pd.DataFrame(
        {
            "expense_id": [1, 2],
            "expense_date": ["2026-10-02", "2026-10-06"],
            "category": ["Utilities", "Rent"],
            "amount": [50.0, 100.0],
            "description": ["Electricity", "Shop rent"],
        }
    )

    def mock_sales(business_id):
        return sales.copy()

    def mock_expenses(business_id, start_date=None, end_date=None):
        result = expenses.copy()

        if start_date is not None:
            result = result[
                result["expense_date"] >= str(start_date)
            ]

        if end_date is not None:
            result = result[
                result["expense_date"] <= str(end_date)
            ]

        return result.reset_index(drop=True)

    monkeypatch.setattr(
        financial_analysis, "get_sales_data", mock_sales
    )
    monkeypatch.setattr(
        financial_analysis, "get_expenses", mock_expenses
    )


# Original tests


def test_calculates_financial_totals(sample_data):
    result = financial_analysis.calculate_financial_summary(1)

    assert result["revenue"] == pytest.approx(550.0)
    assert result["expenses"] == pytest.approx(150.0)
    assert result["operating_result"] == pytest.approx(400.0)
    assert result["operating_margin_pct"] == pytest.approx(
        400 / 550 * 100
    )


def test_filters_sales_and_expenses_by_date(sample_data):
    result = financial_analysis.calculate_financial_summary(
        business_id=1,
        start_date="2026-10-05",
        end_date="2026-10-06",
    )

    assert result["revenue"] == pytest.approx(150.0)
    assert result["sales_records"] == 1
    assert result["expenses"] == pytest.approx(100.0)
    assert result["expense_records"] == 1
    assert result["operating_result"] == pytest.approx(50.0)


def test_margin_is_none_when_revenue_is_zero(monkeypatch):
    monkeypatch.setattr(
        financial_analysis,
        "get_sales_data",
        lambda business_id: pd.DataFrame(
            columns=["transaction_date", "total_amount"]
        ),
    )

    monkeypatch.setattr(
        financial_analysis,
        "get_expenses",
        lambda business_id, start_date=None, end_date=None:
            pd.DataFrame(columns=["expense_date", "amount"]),
    )

    result = financial_analysis.calculate_financial_summary(1)

    assert result["revenue"] == 0
    assert result["operating_result"] == 0
    assert result["operating_margin_pct"] is None


def test_expenses_can_exceed_revenue(monkeypatch):
    monkeypatch.setattr(
        financial_analysis,
        "get_sales_data",
        lambda business_id: pd.DataFrame(
            {
                "transaction_date": ["2026-10-01"],
                "total_amount": [100.0],
            }
        ),
    )

    monkeypatch.setattr(
        financial_analysis,
        "get_expenses",
        lambda business_id, start_date=None, end_date=None:
            pd.DataFrame(
                {
                    "expense_date": ["2026-10-01"],
                    "amount": [150.0],
                }
            ),
    )

    result = financial_analysis.calculate_financial_summary(1)

    assert result["operating_result"] == -50.0
    assert result["operating_margin_pct"] == -50.0


# New Phase 6 tests


def test_includes_expense_category_breakdown(sample_data):
    result = financial_analysis.calculate_financial_summary(1)

    assert "expense_breakdown" in result
    breakdown = result["expense_breakdown"]

    assert breakdown["Utilities"] == pytest.approx(50.0)
    assert breakdown["Rent"] == pytest.approx(100.0)


def test_includes_product_performance(sample_data):
    result = financial_analysis.calculate_financial_summary(1)

    assert "product_performance" in result

    products = result["product_performance"]
    product_map = products.set_index("product_name")

    assert product_map.loc["Coffee", "revenue"] == pytest.approx(200.0)
    assert product_map.loc["Tea", "revenue"] == pytest.approx(150.0)
    assert product_map.loc["Cake", "revenue"] == pytest.approx(200.0)


def test_product_performance_respects_date_range(sample_data):
    result = financial_analysis.calculate_financial_summary(
        business_id=1,
        start_date="2026-10-05",
        end_date="2026-10-06",
    )

    products = result["product_performance"]

    assert len(products) == 1
    assert products.iloc[0]["product_name"] == "Tea"
    assert products.iloc[0]["revenue"] == pytest.approx(150.0)
