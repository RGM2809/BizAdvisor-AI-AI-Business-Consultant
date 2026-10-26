
import re
import pandas as pd


COLUMN_ALIASES = {
    "transaction_date": {
        "date", "transaction_date", "sale_date", "order_date",
        "invoice_date", "datetime", "timestamp"
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
    """Convert a column label into a predictable format."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def standardize_sales_columns(dataframe):
    """Map recognized column names to the shared sales schema."""
    result = dataframe.copy()

    normalized_names = [
        normalize_column_name(column)
        for column in result.columns
    ]

    # Remove spaces and punctuation differences from column names.
    result.columns = normalized_names

    rename_map = {}

    for standard_name, aliases in COLUMN_ALIASES.items():
        recognized = {standard_name, *aliases}

        matches = [
            column for column in result.columns
            if column in recognized
        ]

        if matches:
            # Prefer the exact standardized name if available.
            chosen = (
                standard_name
                if standard_name in matches
                else matches[0]
            )

            if chosen != standard_name:
                rename_map[chosen] = standard_name

    result = result.rename(columns=rename_map)

    # If both an alias and standard column map to the same field,
    # stop rather than silently merging potentially conflicting data.
    if result.columns.duplicated().any():
        duplicates = result.columns[
            result.columns.duplicated()
        ].tolist()

        raise ValueError(
            "Multiple input columns map to the same field: "
            + ", ".join(duplicates)
        )

    return result
