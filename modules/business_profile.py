
from database.connection import get_connection


def create_business(
    business_name,
    business_type,
    location="",
    currency="INR",
):
    """Create a business profile and return its new ID."""

    business_name = (business_name or "").strip()
    business_type = (business_type or "").strip()
    location = (location or "").strip()
    currency = (currency or "INR").strip().upper()

    if not business_name:
        raise ValueError("Business name is required.")

    if not business_type:
        raise ValueError("Business type is required.")

    if not currency:
        currency = "INR"

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO businesses (
                business_name,
                business_type,
                location,
                currency
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                business_name,
                business_type,
                location,
                currency,
            ),
        )

        return cursor.lastrowid


def get_businesses():
    """Return all registered business profiles."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                business_id,
                business_name,
                business_type,
                location,
                currency,
                created_at
            FROM businesses
            ORDER BY business_id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_business(business_id):
    """Return one business profile, or None if it does not exist."""

    if business_id is None:
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                business_id,
                business_name,
                business_type,
                location,
                currency,
                created_at
            FROM businesses
            WHERE business_id = ?
            """,
            (business_id,),
        ).fetchone()

    return dict(row) if row else None
