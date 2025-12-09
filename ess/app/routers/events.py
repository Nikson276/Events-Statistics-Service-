import asyncio
from fastapi import APIRouter, Depends, HTTPException
from ess.app.schemas.event import Event
from ess.app.main import kafka_service
from ess.app.services.clickhouse import ClickHouseService


router = APIRouter()

@router.post("/", response_model=dict)
async def create_event(event: Event):
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
