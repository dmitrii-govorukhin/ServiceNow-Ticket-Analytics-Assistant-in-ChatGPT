import pandas as pd


TRACKED_FIELDS = [
    "status",
    "assigned_to",
    "assignment_group"
]

STATUS_EVENT_MAP = {
    "New": "ticket_created",
    "Open": "ticket_opened",
    "Closed": "ticket_closed",
    "Resolved": "ticket_resolved"
}


# ============================================================
# Canonical Events
# ============================================================

def build_events(df):
    events = []
    grouped = df.groupby("case")

    for case_id, group in grouped:
        group = group.sort_values("start")
        previous_row = None

        for _, row in group.iterrows():
            if previous_row is None:

                for field in TRACKED_FIELDS:
                    new_value = row[field]

                    if field == "status":
                        special_event = STATUS_EVENT_MAP.get(str(new_value))

                        if special_event:
                            events.append({
                                "case": case_id,
                                "event_time": row["start"],
                                "event_type": special_event,
                                "field_name": field,
                                "old_value": None,
                                "new_value": new_value
                            })

                previous_row = row
                continue

            for field in TRACKED_FIELDS:
                old_value = previous_row[field]
                new_value = row[field]

                if old_value != new_value:
                    event_type = f"{field}_changed"
                    events.append({
                        "case": case_id,
                        "event_time": row["start"],
                        "event_type": event_type,
                        "field_name": field,
                        "old_value": old_value,
                        "new_value": new_value
                    })

                    if field == "status":
                        special_event = STATUS_EVENT_MAP.get(str(new_value))

                        if special_event:
                            events.append({
                                "case": case_id,
                                "event_time": row["start"],
                                "event_type": special_event,
                                "field_name": field,
                                "old_value": old_value,
                                "new_value": new_value
                            })

            previous_row = row

    return pd.DataFrame(events)


# ============================================================
# Ticket States (SCD Type 2)
# ============================================================

def build_ticket_states(df):
    """
    Build a full state history for each ticket (SCD Type 2).

    Each row represents a period during which all tracked fields
    (status, assigned_to, assignment_group) remained unchanged.

    Columns:
        case             — ticket identifier
        valid_from       — start of this state (inclusive)
        valid_to         — end of this state (exclusive); NULL = current state
        is_current       — True if this is the latest known state
        status           — ticket status during this period
        assigned_to      — assignee during this period
        assignment_group — assignment group during this period
    """
    states = []
    grouped = df.groupby("case")

    for case_id, group in grouped:
        group = group.sort_values("start").reset_index(drop=True)

        for _, row in group.iterrows():
            valid_to = row["end"] if pd.notna(row["end"]) else None
            is_current = bool(row["active"]) and pd.isna(row["end"])

            states.append({
                "case":             case_id,
                "valid_from":       row["start"],
                "valid_to":         valid_to,
                "is_current":       is_current,
                "status":           row["status"]           if pd.notna(row["status"])           else None,
                "assigned_to":      row["assigned_to"]      if pd.notna(row["assigned_to"])      else None,
                "assignment_group": row["assignment_group"] if pd.notna(row["assignment_group"]) else None,
            })

    states_df = pd.DataFrame(states)

    # Ensure timestamp columns are datetime
    states_df["valid_from"] = pd.to_datetime(states_df["valid_from"])
    states_df["valid_to"]   = pd.to_datetime(states_df["valid_to"])

    return states_df


if __name__ == "__main__":

    from load_sample_data import (
        load_excel,
        standardize_columns
    )

    df = load_excel()
    df = standardize_columns(df)
    df = df.sort_values(
        by=["case", "start"]
    ).reset_index(drop=True)

    # Build and save canonical events
    events_df = build_events(df)
    print("=== Canonical Events ===")
    print(events_df.head(20))
    events_df.to_csv(
        "data/canonical_events.csv",
        index=False
    )
    print("Canonical events saved.\n")

    # Build and save ticket states
    states_df = build_ticket_states(df)
    print("=== Ticket States ===")
    print(states_df.head(20))
    states_df.to_csv(
        "data/ticket_states.csv",
        index=False
    )
    print("Ticket states saved.")