# ess/app/services/kafka.py
from fastapi import APIRouter, Depends, HTTPException
from aiokafka import AIOKafkaProducer
import json
from ess.app.config import settings


# async def get_kafka_service():
#     if kafka_service is None:
#         raise HTTPException(status_code=503, detail="kafka_service unavailable")
#     return kafka_service


class AsyncKafkaProducerService:
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_event(self, event: dict):
        await self.producer.send(settings.kafka_topic, event)
        # send_and_wait() — если нужна гарантия доставки,
        # send() — если fire-and-forget.

# # Глобальный singleton (создаётся в lifespan)
# kafka_service: AsyncKafkaProducerService | None = None

_kafka_service: AsyncKafkaProducerService | None = None

async def init_kafka():
    global _kafka_service
    _kafka_service = AsyncKafkaProducerService()
    await _kafka_service.start()

async def close_kafka():
    global _kafka_service
    if _kafka_service:
        await _kafka_service.stop()

async def get_kafka_service():
    if _kafka_service is None:
        raise RuntimeError("Not initialized")
    return _kafka_service