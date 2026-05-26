from fastapi import FastAPI

from app.api.analytics import router as analytics_router


app = FastAPI()


@app.get("/")
def root():

    return {
        "status": "ok"
    }


# Register analytics routes
app.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"]
)