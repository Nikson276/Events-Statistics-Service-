import asyncio
import json
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer
from aiochclient import ChClient
from aiohttp import ClientSession
from ess.app.schemas.event import Event
from ess.app.config import settings


class AsyncClickHouseBatchWriter:
    def __init__(self, batch_size: int = 5000, flush_timeout: float = 5.0):
        self.batch_size = batch_size
        self.flush_timeout = flush_timeout
        self.queue = asyncio.Queue(maxsize=10000)
        self.session = None
        self.client = None

    async def start(self):
        self.session = ClientSession()
        self.client = ChClient(
            self.session,
            url=f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
        )
        asyncio.create_task(self._batch_writer())

    async def stop(self):
        if self.session:
            await self.session.close()

    async def add_event(self, event: Event):
        await self.queue.put(event)

    async def _batch_writer(self):
        batch = []
        while True:
            try:
                # Ждём событие или таймаут
                event = await asyncio.wait_for(self.queue.get(), timeout=self.flush_timeout)
                batch.append((
                    event.id,
                    event.user_id,
                    event.track_id,
                    event.ingest_time,
                    event.store_time
                ))
                
                if len(batch) >= self.batch_size:
                    await self._flush_batch(batch)
                    batch.clear()
                    
            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)
                    batch.clear()

    async def _flush_batch(self, batch: list):
        try:
            await self.client.execute(
                "INSERT INTO example.events (id, user_id, track_id, ingest_time, store_time) VALUES",
                batch
            )
            print(f"✅ Inserted batch of {len(batch)} events")
        except Exception as e:
            print(f"❌ ClickHouse insert failed: {e}")


class AsyncKafkaConsumerService:
    def __init__(self, writer: AsyncClickHouseBatchWriter):
        self.writer = writer
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="event-statistics-service",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            session_timeout_ms=45000,
            heartbeat_interval_ms=15000,
            max_poll_interval_ms=300000,
        )

    async def start_consuming(self):
        await self.consumer.start()
        print("✅ Async Kafka consumer started")

        try:
            async for msg in self.consumer:
                payload = json.loads(msg.value.decode("utf-8"))
                event = Event.model_validate(payload)
                event.store_time = datetime.now(timezone.utc)
                
                # Немедленно в очередь — без блокировки
                await self.writer.add_event(event)
                
                # Коммитим офсет (можно и реже — например, раз в 100 сообщений)
                await self.consumer.commit()
        finally:
            await self.consumer.stop()
