
import pandas as pd

from modules.validation import validate_sales_data


def test_valid_sales_record_is_accepted():
    data = pd.DataFrame([{
        "transaction_date": "2026-10-20",
        "product_name": "Notebook",
        "quantity": 2,
        "unit_price": 50,
    }])

    accepted, issues = validate_sales_data(data)

    assert len(accepted) == 1
    assert issues.empty
    assert accepted.iloc[0]["total_amount"] == 100


def test_invalid_quantity_is_rejected():
    data = pd.DataFrame([{
        "transaction_date": "2026-10-20",
        "product_name": "Notebook",
        "quantity": -2,
        "unit_price": 50,
    }])

    accepted, issues = validate_sales_data(data)

    assert accepted.empty
    assert not issues.empty
    assert "quantity" in issues["field"].tolist()


def test_invalid_date_is_rejected():
    data = pd.DataFrame([{
        "transaction_date": "not-a-date",
        "product_name": "Notebook",
        "quantity": 1,
        "unit_price": 50,
    }])

    accepted, issues = validate_sales_data(data)

    assert accepted.empty
    assert "transaction_date" in issues["field"].tolist()


def test_duplicate_record_is_flagged():
    row = {
        "transaction_date": "2026-10-20",
        "product_name": "Notebook",
        "quantity": 2,
        "unit_price": 50,
    }

    data = pd.DataFrame([row, row])
    accepted, issues = validate_sales_data(data)

    assert len(accepted) == 1
    assert "record" in issues["field"].tolist()
