import sys
from pathlib import Path

import duckdb
import pandas as pd

# Add backend folder to Python path
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent.parent

sys.path.append(str(BACKEND_DIR))

from app.services.metrics_engine import build_ticket_metrics

from app.etl.load_sample_data import standardize_columns

from app.etl.event_engine import (
    build_events,
    build_ticket_states
)

# Paths
DATA_FILE        = BACKEND_DIR / "data" / "sample_data.xlsx"
NORMALIZED_CSV   = BACKEND_DIR / "data" / "normalized_sample.csv"
EVENTS_CSV       = BACKEND_DIR / "data" / "canonical_events.csv"
STATES_CSV       = BACKEND_DIR / "data" / "ticket_states.csv"
DUCKDB_FILE      = BACKEND_DIR / "data" / "db" / "ticket_analytics.duckdb"


def main():
    print("========================================")
    print("Ticket Analytics Data Refresh Started")
    print("========================================")

    # --------------------------------------------------
    # Step 1. Load and normalize Excel
    # --------------------------------------------------
    print("\n[1/5] Loading Excel file...")

    df = pd.read_excel(DATA_FILE)
    df = standardize_columns(df)

    df.to_csv(NORMALIZED_CSV, index=False)

    print(f"      {len(df)} rows loaded and normalized.")
    print(f"      Saved → {NORMALIZED_CSV.relative_to(BACKEND_DIR)}")

    # --------------------------------------------------
    # Step 2. Build canonical events
    # --------------------------------------------------
    print("\n[2/5] Building canonical events...")

    events_df = build_events(df)
    events_df.to_csv(EVENTS_CSV, index=False)

    print(f"      {len(events_df)} events generated.")
    print(f"      Saved → {EVENTS_CSV.relative_to(BACKEND_DIR)}")

    # --------------------------------------------------
    # Step 3. Build ticket states (SCD Type 2)
    # --------------------------------------------------
    print("\n[3/5] Building ticket states...")

    states_df = build_ticket_states(df)
    states_df.to_csv(STATES_CSV, index=False)

    print(f"      {len(states_df)} state rows generated.")
    print(f"      Saved → {STATES_CSV.relative_to(BACKEND_DIR)}")

    # --------------------------------------------------
    # Step 4. Build ticket metrics
    # --------------------------------------------------
    print("\n[4/5] Building ticket metrics...")

    metrics_df = build_ticket_metrics(events_df, states_df)

    print(f"      {len(metrics_df)} metric rows generated.")

    # --------------------------------------------------
    # Step 5. Write all tables to DuckDB
    # --------------------------------------------------
    print("\n[5/5] Writing to DuckDB...")

    conn = duckdb.connect(str(DUCKDB_FILE))

    tables = {
        "canonical_events": events_df,
        "ticket_states":    states_df,
        "ticket_metrics":   metrics_df,
    }

    for table_name, frame in tables.items():
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.register(f"_{table_name}", frame)
        conn.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM _{table_name}
        """)
        print(f"      ✓ {table_name} ({len(frame)} rows)")

    conn.close()

    print(f"\n      Database → {DUCKDB_FILE.relative_to(BACKEND_DIR)}")
    print("\n========================================")
    print("Data refresh completed successfully")
    print("========================================")


if __name__ == "__main__":
    main()