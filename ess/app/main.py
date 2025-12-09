import uvicorn
import pyroscope
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .services.kafka_producer import kafka_producer_lifespan
from .routers import events
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Pyroscope (до FastAPI)
try:
    pyroscope.configure(
        application_name="ess.fastapi",
        server_address="http://pyroscope:4040",
        tags={"host": "fastapi"},
    )
    logger.info("✅ Pyroscope agent initialized")
except Exception as e:
    logger.error(f"❌ Pyroscope init failed: {e}")

# pyroscope.configure(
#     application_name = "ess.fastapi.app", # replace this with some name for your application
#     server_address   = "https://profiles-prod-015.grafana.net", # replace this with the address of your Pyroscope server
#     basic_auth_username = '1457000',
#     basic_auth_password = settings.grafana_pyroscope,
# )

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
