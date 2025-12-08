import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .services.kafka_producer import kafka_producer_lifespan
from .routers import events
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await kafka_producer_lifespan["startup"]()
    yield
    # Shutdown
    await kafka_producer_lifespan["shutdown"]()

app = FastAPI(
    title="ESS Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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
