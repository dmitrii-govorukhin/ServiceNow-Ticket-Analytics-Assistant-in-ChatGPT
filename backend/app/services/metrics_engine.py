import pandas as pd

from app.etl.load_sample_data import (
    load_excel,
    standardize_columns
)

from app.etl.event_engine import (
    build_events
)


def first_event_time(events_df, case_id, event_type):
    """
    Return the first occurrence timestamp
    for a specific event type and case.
    """

    filtered = events_df[
        (events_df["case"] == case_id)
        &
        (events_df["event_type"] == event_type)
    ]

    if filtered.empty:
        return None

    return filtered["event_time"].min()


def build_ticket_metrics(events_df, states_df=None):
    """
    Build ticket-level metrics dataframe
    from canonical events dataframe.

    states_df — optional ticket_states dataframe (SCD Type 2).
    When provided, enriches metrics with dimension columns
    from the resolution state (assignment_group, assigned_to).
    """

    metrics = []

    # Get unique ticket IDs
    case_ids = events_df["case"].unique()

    for case_id in case_ids:

        # Get important lifecycle timestamps
        created_time = first_event_time(
            events_df,
            case_id,
            "ticket_created"
        )

        opened_time = first_event_time(
            events_df,
            case_id,
            "ticket_opened"
        )

        resolved_time = first_event_time(
            events_df,
            case_id,
            "ticket_resolved"
        )

        first_assignment_time = first_event_time(
            events_df,
            case_id,
            "assigned_to_changed"
        )

        # Append calculated timestamps
        metrics.append({
            "case": case_id,
            "created_time": created_time,
            "opened_time": opened_time,
            "first_assignment_time": first_assignment_time,
            "resolved_time": resolved_time
        })

    # Convert list to dataframe
    metrics_df = pd.DataFrame(metrics)

    # Ensure timestamp columns are datetime
    datetime_columns = [
        "created_time",
        "opened_time",
        "first_assignment_time",
        "resolved_time"
    ]

    for column in datetime_columns:
        metrics_df[column] = pd.to_datetime(metrics_df[column])

    # Calculate durations
    metrics_df["time_to_open"] = (
        metrics_df["opened_time"]
        - metrics_df["created_time"]
    )

    metrics_df["time_to_first_assignment"] = (
        metrics_df["first_assignment_time"]
        - metrics_df["created_time"]
    )

    metrics_df["time_to_resolution"] = (
        metrics_df["resolved_time"]
        - metrics_df["created_time"]
    )

    # ----------------------------------------------------------
    # Enrich with resolution-state dimensions from ticket_states
    # ----------------------------------------------------------
    if states_df is not None:
        resolution_dims = (
            states_df[states_df["status"] == "Resolved"]
            [[
                "case",
                "assignment_group",
                "assigned_to"
            ]]
            .rename(columns={
                "assignment_group": "resolved_assignment_group",
                "assigned_to":      "resolved_assigned_to"
            })
        )

        metrics_df = metrics_df.merge(
            resolution_dims,
            on="case",
            how="left"
        )

    return metrics_df


if __name__ == "__main__":

    # Load source Excel data
    df = load_excel()

    # Normalize column names
    df = standardize_columns(df)

    # Build canonical events dataframe
    events_df = build_events(df)

    # Build ticket metrics dataframe
    metrics_df = build_ticket_metrics(events_df)

    # Display result
    print(metrics_df.head())

    # Save metrics to CSV
    metrics_df.to_csv(
        "data/ticket_metrics.csv",
        index=False
    )

    print("\nTicket metrics saved successfully.")