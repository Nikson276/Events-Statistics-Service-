# ess/kafka_consumer/consumer.py
import asyncio
import json
from typing import List
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer
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
            # Критически важные таймауты:
            session_timeout_ms=45000,
            heartbeat_interval_ms=15000,
            max_poll_interval_ms=300000,  # 5 минут — с запасом
        )
        self.clickhouse = ClickHouseService()
        # self.batch: List[Event] = []
        # self.batch_size = 1000  # ← размер батча
        # self.batch_timeout = 5.0  # ← максимальное время ожидания (сек)
        # self.batch_lock = asyncio.Lock()
        # self._batch_timer = None

    async def start_consuming(self):
        await self.consumer.start()
        print("✅ Kafka consumer started (no batching)")

        try:
            async for msg in self.consumer:
                await self._process_message(msg)
        finally:
            await self.consumer.stop()

    async def _process_message(self, msg):
        try:
            payload = json.loads(msg.value.decode("utf-8"))
            event = Event.model_validate(payload)
            event.store_time = datetime.now(timezone.utc)

            # Пишем СРАЗУ — без батчинга
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.clickhouse.insert_events, event)

            # Коммитим офсет
            await self.consumer.commit()
            print(f"✅ Processed event: {event.id}")

        except Exception as e:
            print(f"❌ Failed to process message: {e}")
            await self.consumer.commit() # для dev — коммитим, В продакшене: отправка в DLQ

    async def _flush_batch(self):
        async with self.batch_lock:
            if not self.batch:
                return
            batch_to_flush = self.batch.copy()
            self.batch.clear()
            if self._batch_timer:
                self._batch_timer.cancel()
                self._batch_timer = None

        try:
            # Вставка в ClickHouse (в thread pool)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.clickhouse.insert_events, batch_to_flush)
            await self.consumer.commit()  # коммитим офсеты после успешной вставки
            print(f"✅ Flushed batch of {len(batch_to_flush)} events")
        except Exception as e:
            print(f"❌ Failed to flush batch: {e}")
            # В продакшене: отправка в DLQ, повторная попытка
            # Для dev — коммитим, чтобы не застревать
            await self.consumer.commit()