# ess/kafka_consumer/consumer.py
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from datetime import datetime, timezone
from ess.app.schemas.event import Event
from ess.app.config import settings
from ess.app.services.clickhouse import ClickHouseService


class AsyncKafkaConsumerService:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="event-statistics-service",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        self.clickhouse = ClickHouseService()

    async def start_consuming(self):
        await self.consumer.start()
        print(f"✅ Async Kafka consumer started. Listening to topic: {settings.kafka_topic}")

        try:
            async for msg in self.consumer:
                await self._process_message(msg)
        finally:
            await self.consumer.stop()

    async def _process_message(self, msg):
        try:
            payload = json.loads(msg.value.decode("utf-8"))
            event = Event.model_validate(payload)

            # Устанавливаем время записи
            event.store_time = datetime.now(timezone.utc)

            # Запись в ClickHouse (в thread pool)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.clickhouse.insert_events, event)

            # Коммит офсета
            await self.consumer.commit()
            print(f"✅ Processed event: {event.id}")

        except Exception as e:
            print(f"❌ Failed to process message: {e}")
            # В продакшене: отправка в DLQ
            await self.consumer.commit()  # для dev — коммитим