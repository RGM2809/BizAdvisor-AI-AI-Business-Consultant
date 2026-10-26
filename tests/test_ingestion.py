
from io import BytesIO

import pandas as pd
import pytest

from modules.data_ingestion import load_sales_file


class FakeUpload:
    def __init__(self, name, content):
        self.name = name
        self.content = content

    def getvalue(self):
        return self.content


def test_csv_columns_are_standardized():
    content = (
        "Date,Product,Qty,Price\n"
        "2026-10-20,Notebook,2,50\n"
    ).encode("utf-8")

    uploaded_file = FakeUpload("sales.csv", content)
    result = load_sales_file(uploaded_file)

    assert "transaction_date" in result.columns
    assert "product_name" in result.columns
    assert "quantity" in result.columns
    assert "unit_price" in result.columns
    assert len(result) == 1


def test_unsupported_file_type_is_rejected():
    uploaded_file = FakeUpload("sales.txt", b"sample data")

    with pytest.raises(ValueError, match="Unsupported file type"):
        load_sales_file(uploaded_file)


def test_empty_file_is_rejected():
    uploaded_file = FakeUpload("sales.csv", b"")

    with pytest.raises(ValueError, match="empty"):
        load_sales_file(uploaded_file)
