from fastapi import APIRouter, Depends, HTTPException

from ess.app.schemas.event import Event
from ess.app.services.kafka_producer import KafkaProducerService, get_kafka_service
from ess.app.services.clickhouse import ClickHouseService


router = APIRouter()

@router.post("/", response_model=dict)
async def create_event(
    event: Event,
    kafka_service: KafkaProducerService = Depends(get_kafka_service),
):
    """Receive event and send to Kafka"""
    try:
        await kafka_service.send_event(event)
        # await kafka_service.put(event)  # ← очередь в памяти
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "queued"}

@router.get("/", response_model=list[Event])
def list_events(
    limit: int = 10,
    offset: int = 0,
    clickhouse_service: ClickHouseService = Depends(),
):
    """Retrieve events from ClickHouse"""
    try:
        events = clickhouse_service.get_events(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return events
