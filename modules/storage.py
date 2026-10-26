
import hashlib

import pandas as pd

from database.connection import get_connection


SALES_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "product_name",
    "quantity",
    "unit_price",
    "total_amount",
]

REQUIRED_SALES_INPUT_COLUMNS = [
    "transaction_date",
    "product_name",
    "quantity",
    "unit_price",
    "total_amount",
]


def get_file_sha256(file_bytes):
    """Return a SHA-256 fingerprint for an uploaded file."""
    return hashlib.sha256(file_bytes).hexdigest()


def has_imported_sales_file(business_id, file_hash):
    """Check whether this exact file was imported for this business."""
    if not file_hash:
        return False

    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT 1
            FROM imported_sales_files
            WHERE business_id = ? AND file_hash = ?
            LIMIT 1
            """,
            (int(business_id), file_hash),
        ).fetchone()

    return result is not None


def save_sales_data(
    business_id,
    dataframe,
    file_hash=None,
    original_filename=None,
):
    """Save sales records and, for uploads, record the file fingerprint."""

    if business_id is None:
        raise ValueError("Select a business before saving sales data.")

    try:
        business_id = int(business_id)
    except (TypeError, ValueError):
        raise ValueError("The selected business ID is invalid.")

    if dataframe is None or dataframe.empty:
        return 0

    missing_columns = [
        column
        for column in REQUIRED_SALES_INPUT_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Sales data is missing required columns: "
            + ", ".join(missing_columns)
        )

    records = []

    for row in dataframe.to_dict(orient="records"):
        try:
            transaction_date = str(row["transaction_date"]).strip()
            product_name = str(row["product_name"]).strip()
            quantity = float(row["quantity"])
            unit_price = float(row["unit_price"])
            total_amount = float(row["total_amount"])
        except (TypeError, ValueError):
            raise ValueError(
                "Sales data contains a record with invalid numeric values."
            )

        if not transaction_date or not product_name:
            raise ValueError(
                "Transaction date and product name cannot be empty."
            )

        if (
            pd.isna(quantity)
            or pd.isna(unit_price)
            or pd.isna(total_amount)
            or quantity <= 0
            or unit_price < 0
            or total_amount < 0
        ):
            raise ValueError(
                "Sales data contains invalid quantity, price, or total values."
            )

        records.append(
            (
                business_id,
                transaction_date,
                product_name,
                quantity,
                unit_price,
                total_amount,
            )
        )

    with get_connection() as connection:
        business = connection.execute(
            """
            SELECT business_id
            FROM businesses
            WHERE business_id = ?
            """,
            (business_id,),
        ).fetchone()

        if business is None:
            raise ValueError("The selected business does not exist.")

        if file_hash:
            already_imported = connection.execute(
                """
                SELECT 1
                FROM imported_sales_files
                WHERE business_id = ? AND file_hash = ?
                LIMIT 1
                """,
                (business_id, file_hash),
            ).fetchone()

            if already_imported:
                raise ValueError(
                    "This exact file has already been imported "
                    "for this business. No records were saved again."
                )

        connection.executemany(
            """
            INSERT INTO sales_transactions (
                business_id,
                transaction_date,
                product_name,
                quantity,
                unit_price,
                total_amount
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )

        if file_hash:
            connection.execute(
                """
                INSERT INTO imported_sales_files (
                    business_id,
                    file_hash,
                    original_filename,
                    record_count
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    business_id,
                    file_hash,
                    original_filename or "uploaded_file",
                    len(records),
                ),
            )

    return len(records)


def get_sales_data(business_id):
    """Return sales records for one business as a DataFrame."""

    if business_id is None:
        return pd.DataFrame(columns=SALES_COLUMNS)

    try:
        business_id = int(business_id)
    except (TypeError, ValueError):
        raise ValueError("The selected business ID is invalid.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                transaction_id,
                transaction_date,
                product_name,
                quantity,
                unit_price,
                total_amount
            FROM sales_transactions
            WHERE business_id = ?
            ORDER BY transaction_date DESC, transaction_id DESC
            """,
            (business_id,),
        ).fetchall()

    return pd.DataFrame(
        [dict(row) for row in rows],
        columns=SALES_COLUMNS,
    )
