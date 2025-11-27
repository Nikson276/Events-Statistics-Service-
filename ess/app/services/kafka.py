import os
import json
import asyncio
from kafka import KafkaProducer
from ess.app.schemas.event import Event
from ess.app.config import settings


class KafkaProducerService:
    """Service for producing events to Kafka topic."""
    def __init__(self):
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    async def send_event(self, event: Event) -> None:
        """Send event to Kafka asynchronously."""
        loop = asyncio.get_event_loop()
        # Send in thread pool
        await loop.run_in_executor(
            None, self.producer.send, self.topic, event.model_dump()
        )
        # Flush to ensure delivery
        await loop.run_in_executor(None, self.producer.flush)
