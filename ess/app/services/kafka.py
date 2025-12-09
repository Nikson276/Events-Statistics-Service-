# ess/app/services/kafka.py
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
        # send_and_wait() — если нужна гарантия доставки,
        # send() — если fire-and-forget.

# Глобальный singleton (создаётся в lifespan)
kafka_service: AsyncKafkaProducerService | None = None