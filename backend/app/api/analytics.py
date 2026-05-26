from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.schemas.analytics_query import AnalyticsQuery
from app.services.query_service import execute_analytics_query


API_KEY = ""
api_key_header = APIKeyHeader(name="X-API-Key")


def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


router = APIRouter()


@router.post("/query", dependencies=[Depends(verify_api_key)])
def analytics_query(query: AnalyticsQuery):
    """
    Execute analytics query.
    """
    result = execute_analytics_query(query)
    return {
        "query": query.model_dump(),
        "result": result
    }