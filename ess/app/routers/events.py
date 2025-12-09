import asyncio
from fastapi import APIRouter, Depends, HTTPException
from ess.app.schemas.event import Event
from ess.app.services.kafka import kafka_service
from ess.app.services.clickhouse import ClickHouseService


async def get_kafka_service():
    if kafka_service is None:
        raise RuntimeError("Not initialized")
    return kafka_service

router = APIRouter()

@router.post("/", response_model=dict)
async def create_event(event: Event, kafka = Depends(get_kafka_service)):
    """Receive event and send to Kafka"""
    await kafka_service.send_event(event.model_dump(mode="json"))
    return {"status": "queued"}

@router.get("/", response_model=list[Event])
async def list_events(
    limit: int = 10,
    offset: int = 0,
    clickhouse_service: ClickHouseService = Depends(),
):
    """Retrieve events from ClickHouse"""
    try:
        loop = asyncio.get_event_loop()
        events = await loop.run_in_executor(
            None, clickhouse_service.get_events, limit, offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return events
