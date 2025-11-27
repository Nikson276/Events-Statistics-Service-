import uvicorn
from fastapi import FastAPI
from .routers import events
from .config import settings


app = FastAPI(
    title="ESS Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(events.router, prefix="/events", tags=["events"])

@app.get("/")
async def root():
    return {"message": "ESS Service is running"}

@app.get("/config")
def get_config():
    return {
        "kafka": settings.kafka_bootstrap_servers,
        "topic": settings.kafka_topic,
        "clickhouse": f"{settings.clickhouse_host}:{settings.clickhouse_port}"
    }

if __name__ == "__main__":
    uvicorn.run("ess.app.main:app", host="0.0.0.0", port=8000, reload=True)
