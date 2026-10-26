
import sqlite3
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "bizadvisor.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


@contextmanager
def get_connection():
    """Open and reliably close a connection to the local SQLite database."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    """Create the database tables if they do not exist."""

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Database schema file not found: {SCHEMA_PATH}"
        )

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.executescript(schema)
