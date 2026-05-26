from typing import Literal, Optional

from pydantic import BaseModel


class AnalyticsQuery(BaseModel):

    # Metric name
    metric: str

    # Optional filters
    assigned_to: Optional[str] = None
    assignment_group: Optional[str] = None
    status: Optional[str] = None

    # Optional date filters
    date_from: Optional[str] = None
    date_to: Optional[str] = None

    # Optional grouping
    group_by: Optional[str] = None

    # Filter scope — controls how dimension filters are interpreted:
    #   "at_resolution" — filters apply to the state at the moment of resolution
    #                     (default for resolved_tickets)
    #   "ever"          — ticket was ever in the given state at any point
    #   "current"       — ticket is currently in the given state
    filter_scope: Literal["at_resolution", "ever", "current"] = "at_resolution"