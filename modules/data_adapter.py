
import re

import pandas as pd

from modules.validation import validate_sales_data


COLUMN_ALIASES = {
    "transaction_id": {
        "transaction_id", "transactionid", "sale_id", "sales_id",
        "invoice_id", "order_id", "receipt_id", "bill_no"
    },
    "transaction_date": {
        "date", "transaction_date", "transactiondate", "sale_date",
        "order_date", "invoice_date", "datetime", "timestamp"
    },
    "product_name": {
        "product", "product_name", "item", "item_name",
        "product_title", "description"
    },
    "quantity": {
        "quantity", "qty", "units", "unit_sold", "units_sold"
    },
    "unit_price": {
        "unit_price", "price", "selling_price",
        "sale_price", "price_per_unit"
    },
    "total_amount": {
        "total", "total_amount", "sales", "sales_amount",
        "revenue", "amount", "total_sales"
    },
}


def normalize_column_name(name):
    """Normalize a column label for reliable matching."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def standardize_columns(dataframe):
    """
    Standardize recognized column names.

    Raises an error if multiple source columns map to the same field.
    """
    if dataframe is None or dataframe.empty:
        raise ValueError("The uploaded file contains no data rows.")

    result = dataframe.copy()
    rename_map = {}
    used_targets = {}

    for column in result.columns:
        normalized = normalize_column_name(column)

        target = next(
            (
                standard_name
                for standard_name, aliases in COLUMN_ALIASES.items()
                if normalized == standard_name
                or normalized in aliases
            ),
            None,
        )

        if target is None:
            continue

        if target in used_targets:
            raise ValueError(
                f"Both '{used_targets[target]}' and '{column}' "
                f"appear to represent '{target}'. "
                "Please keep only one of these columns."
            )

        used_targets[target] = column
        rename_map[column] = target

    return result.rename(columns=rename_map)


def adapt_sales_data(dataframe):
    """
    Adapt uploaded sales data into BizAdvisor's standard format.

    Returns a dictionary containing:
      accepted: records passing validation
      issues: validation issues
      summary: import counts
      preview: standardized input preview

    This function never writes to the database.
    """
    original_count = 0 if dataframe is None else len(dataframe)

    standardized = standardize_columns(dataframe)

    accepted, issues = validate_sales_data(standardized)

    # A row may produce multiple issues, so count distinct rejected rows.
    rejected_rows = set()

    if not issues.empty and "row" in issues.columns:
        for row_number in issues["row"]:
            if isinstance(row_number, int):
                rejected_rows.add(row_number)

    accepted_count = len(accepted)
    rejected_count = len(rejected_rows)

    summary = {
        "input_records": original_count,
        "accepted_records": accepted_count,
        "rejected_records": rejected_count,
        "issue_count": len(issues),
    }

    return {
        "accepted": accepted,
        "issues": issues,
        "summary": summary,
        "preview": standardized.head(20),
    }
