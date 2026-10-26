
import pandas as pd
import pytest

from modules import sales_forecasting


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
            "transaction_date": "2026-10-22",
            "product_name": "Coffee",
            "quantity": 1,
            "unit_price": 100,
            "total_amount": 100,
        },
    ])


def test_daily_sales_aggregation(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    daily = sales_forecasting.prepare_daily_sales(1)

    assert len(daily) == 3
    assert daily.loc[0, "revenue"] == 350.0
    assert daily.loc[1, "revenue"] == 0.0
    assert daily.loc[2, "revenue"] == 100.0
    assert daily["transactions"].tolist() == [2, 0, 1]


def test_total_revenue_is_preserved(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    daily = sales_forecasting.prepare_daily_sales(1)

    assert daily["revenue"].sum() == 450.0


def test_date_filter(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    daily = sales_forecasting.prepare_daily_sales(
        1,
        start_date="2026-10-22",
        end_date="2026-10-22",
    )

    assert len(daily) == 1
    assert daily.iloc[0]["revenue"] == 100.0


def test_reversed_date_range_raises_error(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: sample_sales(),
    )

    with pytest.raises(ValueError):
        sales_forecasting.prepare_daily_sales(
            1,
            start_date="2026-10-22",
            end_date="2026-10-20",
        )


def test_empty_sales(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
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

    daily = sales_forecasting.prepare_daily_sales(1)

    assert daily.empty
    assert list(daily.columns) == [
        "date", "revenue", "transactions"
    ]


def test_forecast_returns_insufficient_data(monkeypatch):
    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: pd.DataFrame([
            {
                "transaction_id": i + 1,
                "transaction_date": date,
                "product_name": "Coffee",
                "quantity": 1,
                "unit_price": 100,
                "total_amount": 100,
            }
            for i, date in enumerate(
                pd.date_range("2026-10-01", periods=10, freq="D")
            )
        ]),
    )

    result = sales_forecasting.forecast_sales(1)

    assert result["status"] == "insufficient_data"
    assert result["forecast"].empty
    assert result["random_forest_mae"] is None


def test_forecast_generates_requested_days(monkeypatch):
    historical_sales = pd.DataFrame([
        {
            "transaction_id": i + 1,
            "transaction_date": date,
            "product_name": "Coffee",
            "quantity": 1,
            "unit_price": 100 + (i % 7) * 10,
            "total_amount": 100 + (i % 7) * 10,
        }
        for i, date in enumerate(
            pd.date_range("2026-01-01", periods=90, freq="D")
        )
    ])

    monkeypatch.setattr(
        sales_forecasting,
        "get_sales_data",
        lambda business_id: historical_sales.copy(),
    )

    result = sales_forecasting.forecast_sales(
        1,
        forecast_days=7,
    )

    assert result["status"] == "success"
    assert len(result["forecast"]) == 7
    assert result["forecast"]["random_forest"].notna().all()
    assert (result["forecast"]["random_forest"] >= 0).all()
    assert result["baseline_mae"] >= 0
    assert result["random_forest_mae"] >= 0


def test_forecast_rejects_invalid_horizon():
    with pytest.raises(ValueError):
        sales_forecasting.forecast_sales(1, forecast_days=0)

    with pytest.raises(ValueError):
        sales_forecasting.forecast_sales(1, forecast_days=31)
