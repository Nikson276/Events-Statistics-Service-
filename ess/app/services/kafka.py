# ess/app/services/kafka.py
from fastapi import APIRouter, Depends, HTTPException
from aiokafka import AIOKafkaProducer
import json
from ess.app.config import settings


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

# ЕДИНСТВЕННАЯ глобальная переменная
_kafka_service: AsyncKafkaProducerService | None = None

async def init_kafka():
    """Вызывается из lifespan в main.py"""
    global _kafka_service
    _kafka_service = AsyncKafkaProducerService()
    await _kafka_service.start()

async def close_kafka():
    """Вызывается из lifespan в main.py"""
    global _kafka_service
    if _kafka_service:
        await _kafka_service.stop()

async def get_kafka_service():
    """Используется в Depends() в роутерах"""
    if _kafka_service is None:
        raise RuntimeError("Kafka service not initialized")
    return _kafka_service