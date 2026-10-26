
import math
from datetime import date

import pandas as pd

from database.connection import get_connection


EXPENSE_CATEGORIES = [
    "Rent",
    "Salaries",
    "Inventory / Raw Materials",
    "Utilities",
    "Marketing",
    "Transport",
    "Equipment",
    "Maintenance",
    "Packaging",
    "Other",
]


def add_expense(
    business_id,
    expense_date,
    category,
    amount,
    description="",
):
    """Save one expense for a registered business."""

    if not category or not category.strip():
        raise ValueError("Expense category is required.")

    try:
        amount = float(amount)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Expense amount must be numeric.") from error

    if not math.isfinite(amount):
        raise ValueError("Expense amount must be a finite number.")

    if amount < 0:
        raise ValueError("Expense amount cannot be negative.")

    if isinstance(expense_date, date):
        expense_date = expense_date.isoformat()
    else:
        parsed_date = pd.to_datetime(expense_date, errors="coerce")
        if pd.isna(parsed_date):
            raise ValueError("Enter a valid expense date.")
        expense_date = parsed_date.strftime("%Y-%m-%d")

    description = (description or "").strip()

    with get_connection() as connection:
        business = connection.execute(
            "SELECT business_id FROM businesses WHERE business_id = ?",
            (int(business_id),),
        ).fetchone()

        if business is None:
            raise ValueError("The selected business does not exist.")

        cursor = connection.execute(
            """
            INSERT INTO expenses (
                business_id,
                expense_date,
                category,
                amount,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(business_id),
                expense_date,
                category.strip(),
                amount,
                description,
            ),
        )

        return cursor.lastrowid


def get_expenses(business_id, start_date=None, end_date=None):
    """Return expenses for a business, optionally filtered by date."""

    query = """
        SELECT
            expense_id,
            expense_date,
            category,
            amount,
            description
        FROM expenses
        WHERE business_id = ?
    """

    parameters = [int(business_id)]

    if start_date is not None:
        query += " AND expense_date >= ?"
        parameters.append(str(start_date))

    if end_date is not None:
        query += " AND expense_date <= ?"
        parameters.append(str(end_date))

    query += " ORDER BY expense_date DESC, expense_id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return pd.DataFrame(
        [dict(row) for row in rows],
        columns=[
            "expense_id",
            "expense_date",
            "category",
            "amount",
            "description",
        ],
    )


def delete_expense(expense_id, business_id):
    """Delete an expense only if it belongs to the selected business."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM expenses
            WHERE expense_id = ? AND business_id = ?
            """,
            (int(expense_id), int(business_id)),
        )

        return cursor.rowcount > 0
