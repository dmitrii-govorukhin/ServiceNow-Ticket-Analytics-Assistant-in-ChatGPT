import duckdb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "data" / "db" / "ticket_analytics.duckdb"

print("DUCKDB ABS PATH =", Path(DATABASE_PATH).resolve())


def run_query(sql: str):
    """
    Execute SQL query using a fresh DuckDB connection each time.
    Ensures stateless execution (no caching issues).
    """

    with duckdb.connect(str(DATABASE_PATH)) as conn:
        result = conn.execute(sql).fetchdf()
        return result


def run_scalar_query(sql: str):
    """
    Execute query returning a single scalar value.
    """

    with duckdb.connect(str(DATABASE_PATH)) as conn:
        result = conn.execute(sql).fetchone()
        return result[0] if result else None