import asyncio
import json
from typing import AsyncGenerator
from kafka import KafkaProducer
from fastapi import Depends
from ess.app.schemas.event import Event
from ess.app.config import settings


# Глобальный singleton (создаётся один раз при старте)
_kafka_producer: KafkaProducer | None = None


async def init_kafka_producer() -> None:
    """Initialize Kafka producer at startup."""
    global _kafka_producer
    if _kafka_producer is None:
        loop = asyncio.get_event_loop()
        # Создаём продюсера в thread pool (т.к. KafkaProducer — синхронный)
        _kafka_producer = await loop.run_in_executor(
            None,
            lambda: KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                # Оптимизации для highload:
                linger_ms=5,          # группировать сообщения 5 мс
                batch_size=16384,     # 16 KB batch
                acks=1,               # подтверждение от лидера
                retries=3,
            )
        )


async def close_kafka_producer() -> None:
    """Close Kafka producer at shutdown."""
    global _kafka_producer
    if _kafka_producer is not None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _kafka_producer.close)
        _kafka_producer = None


# Lifespan-хендлеры для подключения к FastAPI
kafka_producer_lifespan = {
    "startup": init_kafka_producer,
    "shutdown": close_kafka_producer,
}


# DI-зависимость для роутеров
async def get_kafka_producer() -> KafkaProducer:
    """Return the global Kafka producer instance."""
    if _kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized")
    return _kafka_producer


# Обновлённый класс-обёртка
class KafkaProducerService:
    """Service wrapper for Kafka producer (singleton)."""
    
    def __init__(self, producer: KafkaProducer):
        self.producer = producer
        self.topic = settings.kafka_topic

    async def send_event(self, event: Event) -> None:
        """Send event to Kafka asynchronously (without flush)."""
        loop = asyncio.get_event_loop()
        # Отправляем БЕЗ flush!
        await loop.run_in_executor(
            None, self.producer.send, self.topic, event.model_dump(mode="json")
        )
        # flush УБРАН! Он убивал производительность и вызывал "too many open files"


# DI-зависимость для класса
async def get_kafka_service(
    producer: KafkaProducer = Depends(get_kafka_producer)
) -> KafkaProducerService:
    """Return Kafka service instance."""
    return KafkaProducerService(producer)