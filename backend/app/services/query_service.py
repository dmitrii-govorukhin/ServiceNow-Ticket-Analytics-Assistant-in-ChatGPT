from app.schemas.analytics_query import AnalyticsQuery
from app.services.duckdb_service import run_query


# ============================================================
# Metric Registry
# ============================================================

METRIC_REGISTRY = {

    # ----------------------------------------------------------
    # resolved_tickets
    # Тикеты, достигшие статуса Resolved.
    # Фильтры assignment_group / assigned_to применяются
    # к той же строке состояния (т.е. «закрыто в этой группе»).
    # ----------------------------------------------------------
    "resolved_tickets": {
        "table":      "ticket_states",
        "select":     'COUNT(DISTINCT "case") AS resolved_tickets',
        "base_where": "status = 'Resolved' AND is_current = true",
    },

    # ----------------------------------------------------------
    # closed_tickets
    # Тикеты со статусом Closed (административное закрытие,
    # отличается от Resolved в ServiceNow).
    # ----------------------------------------------------------
    "closed_tickets": {
        "table":      "ticket_states",
        "select":     'COUNT(DISTINCT "case") AS closed_tickets',
        "base_where": "status = 'Closed' AND is_current = true",
    },

    # ----------------------------------------------------------
    # total_tickets
    # Общее количество уникальных тикетов.
    # default_scope = "current" — считаем каждый тикет один раз
    # (по его текущей строке состояния).
    # ----------------------------------------------------------
    "total_tickets": {
        "table":         "ticket_states",
        "select":        'COUNT(DISTINCT "case") AS total_tickets',
        "default_scope": "current",
    },

    # ----------------------------------------------------------
    # tickets_in_progress
    # Тикеты, находящиеся в работе прямо сейчас:
    # все текущие состояния кроме: New, Resolved, Closed, Cancelled.
    # ----------------------------------------------------------
    "tickets_in_progress": {
        "table":         "ticket_states",
        "select":        'COUNT(DISTINCT "case") AS tickets_in_progress',
        "base_where":    "status NOT IN ('New', 'Resolved', 'Closed', 'Cancelled') AND is_current = true",
        "default_scope": "current",
    },
    
    # ----------------------------------------------------------
    # avg_resolution_time
    # Средняя продолжительность от создания до резолюции.
    # Результат — в минутах.
    # Поддерживает group_by: resolved_assignment_group,
    # resolved_assigned_to (из состояния тикета на момент резолюции).
    # ----------------------------------------------------------
    "avg_resolution_time": {
        "table":     "ticket_metrics",
        "select":    """
            ROUND(
                AVG(EXTRACT(EPOCH FROM time_to_resolution)) / 60
            ) AS avg_resolution_minutes
        """,
        "base_where": "time_to_resolution IS NOT NULL",
    },
}



# ============================================================
# Allowed Group By Fields
# ============================================================

ALLOWED_GROUP_FIELDS = {
    # ticket_states fields
    "assigned_to",
    "assignment_group",
    "status",
    # ticket_metrics fields (resolution-state dimensions)
    "resolved_assignment_group",
    "resolved_assigned_to",
}


# ============================================================
# Public API
# ============================================================

def execute_analytics_query(query: AnalyticsQuery):
    sql = build_sql_query(query)

    result_df = run_query(sql)

    return result_df.to_dict(orient="records")


# ============================================================
# Main SQL Builder
# ============================================================

def build_sql_query(query: AnalyticsQuery) -> str:
    metric_config = METRIC_REGISTRY.get(query.metric)

    if not metric_config:
        raise ValueError(f"Unsupported metric: {query.metric}")

    # Use the metric's default scope if the caller did not specify one
    effective_scope = query.filter_scope or metric_config.get("default_scope", "at_resolution")

    select_clause   = build_select_clause(query, metric_config)
    from_clause     = build_from_clause(metric_config)
    where_clause    = build_where_clause(query, metric_config, effective_scope)
    group_by_clause = build_group_by_clause(query)

    sql = f"""
        {select_clause}
        {from_clause}
        {where_clause}
        {group_by_clause}
    """

    return clean_sql(sql)


# ============================================================
# SELECT
# ============================================================

def build_select_clause(query: AnalyticsQuery, metric_config: dict) -> str:
    metric_select = metric_config["select"]

    if query.group_by:
        validate_group_by(query.group_by)
        return f"""
            SELECT
                {query.group_by},
                {metric_select}
        """

    return f"""
        SELECT
            {metric_select}
    """


# ============================================================
# FROM
# ============================================================

def build_from_clause(metric_config: dict) -> str:
    return f"""
        FROM {metric_config["table"]} main
    """


# ============================================================
# WHERE
# ============================================================

def build_where_clause(
    query: AnalyticsQuery,
    metric_config: dict,
    effective_scope: str,
) -> str:
    conditions = []
    table = metric_config["table"]

    # ----------------------------------------------------------
    # Base metric filter (e.g. status = 'Resolved')
    # ----------------------------------------------------------
    base_where = metric_config.get("base_where")
    if base_where:
        conditions.append(base_where)

    # ----------------------------------------------------------
    # ticket_states filters
    # ----------------------------------------------------------
    if table == "ticket_states":

        # Scope filter — narrows which state rows to consider
        if effective_scope == "current":
            conditions.append("is_current = true")

        elif effective_scope == "at_resolution":
            # The base_where already pins status = 'Resolved',
            # so no extra scope condition is needed here:
            # we are already looking at the resolution-state row.
            pass

        # "ever" scope → no additional row filter; all state rows
        # are considered, and COUNT(DISTINCT case) deduplicates.

        # Dimension filters — applied directly as column conditions
        # because ticket_states has one column per tracked field.
        if query.assignment_group:
            conditions.append(
                f"assignment_group = '{query.assignment_group}'"
            )

        if query.assigned_to:
            conditions.append(
                f"assigned_to = '{query.assigned_to}'"
            )

        if query.status and not base_where:
            # Only add status filter when the metric does not
            # already set it via base_where (avoids duplication).
            conditions.append(
                f"status = '{query.status}'"
            )

        # Date filters — applied to valid_from of the state row
        if query.date_from:
            conditions.append(
                f"valid_from >= '{query.date_from}'"
            )

        if query.date_to:
            conditions.append(
                f"valid_from <= '{query.date_to}'"
            )

    # ----------------------------------------------------------
    # ticket_metrics filters
    # ----------------------------------------------------------
    elif table == "ticket_metrics":

        # Dimension filters — resolved_* columns added by metrics_engine
        # when ticket_states is passed to build_ticket_metrics().
        if query.assignment_group:
            conditions.append(
                f"resolved_assignment_group = '{query.assignment_group}'"
            )

        if query.assigned_to:
            conditions.append(
                f"resolved_assigned_to = '{query.assigned_to}'"
            )

        if query.date_from:
            conditions.append(
                f"created_time >= '{query.date_from}'"
            )

        if query.date_to:
            conditions.append(
                f"created_time <= '{query.date_to}'"
            )

    # ----------------------------------------------------------
    # Final WHERE
    # ----------------------------------------------------------
    if not conditions:
        return ""

    return f"""
        WHERE {" AND ".join(conditions)}
    """


# ============================================================
# GROUP BY
# ============================================================

def build_group_by_clause(query: AnalyticsQuery) -> str:
    if not query.group_by:
        return ""

    validate_group_by(query.group_by)

    return f"""
        GROUP BY {query.group_by}
    """


# ============================================================
# Validation
# ============================================================

def validate_group_by(group_by: str):
    if group_by not in ALLOWED_GROUP_FIELDS:
        raise ValueError(f"Unsupported group_by field: {group_by}")


# ============================================================
# Utilities
# ============================================================

def clean_sql(sql: str) -> str:
    return "\n".join(
        line.strip()
        for line in sql.splitlines()
        if line.strip()
    )