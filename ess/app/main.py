import uvicorn
import pyroscope
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .services.kafka import init_kafka, close_kafka
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

kafka_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # global kafka_service
    # kafka_service = AsyncKafkaProducerService()
    # print(f"kafka_service= {kafka_service}")
    # Startup
    await init_kafka()
    print("✅ Kafka producer started")
    yield
    # Shutdown
    await close_kafka()

async def get_kafka_service():
    if kafka_service is None:
        raise RuntimeError("kafka_service Not ready")
    return kafka_service

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
