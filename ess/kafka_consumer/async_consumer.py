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

    def _format_datetime(self, dt: datetime) -> str:
        """Форматирует datetime в строку без временной зоны для ClickHouse"""
        # Убедимся, что дата в UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        # Формат: '2025-12-22 23:20:55.474'
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # обрезаем до миллисекунд

    async def _flush_batch(self, batch: list):
        try:
            print(f"📤 Flushing batch of {len(batch)} events to ClickHouse...")
            # # Преобразуем datetime в int перед отправкой
            # converted_batch = [
            #     (
            #         event_id,
            #         user_id,
            #         track_id,
            #         self._format_datetime(ingest_time),
            #         self._format_datetime(store_time)
            #     )
            #     for (event_id, user_id, track_id, ingest_time, store_time) in batch
            # ]
            json_data = [
                {
                    "id": event_id,
                    "user_id": user_id,
                    "track_id": track_id,
                    "ingest_time": ingest_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "store_time": store_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                }
                for (event_id, user_id, track_id, ingest_time, store_time) in batch
            ]
            await self.client.execute(
                "INSERT INTO example.events_local FORMAT JSONEachRow",
                json_data
            )
            # await self.client.execute(
            #     "INSERT INTO example.events_local (id, user_id, track_id, ingest_time, store_time) VALUES",
            #     converted_batch
            # )
            print(f"✅ Successfully inserted batch of {len(batch)} events")
        except Exception as e:
            print(f"❌ ClickHouse insert failed: {e}")
            # Для отладки
            if batch:
                print(f"   Sample raw event: {batch[0]}")
                print(f"   Converted event: {converted_batch[0] if converted_batch else 'N/A'}")


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
        print(f"✅ Kafka consumer started. Topic: {settings.kafka_topic}, Group: event-statistics-service")
        print(f"✅ ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")

        processed_count = 0
        try:
            async for msg in self.consumer:
                try:
                    payload = json.loads(msg.value.decode("utf-8"))
                    event = Event.model_validate(payload)
                    event.store_time = datetime.now(timezone.utc)
                    
                    print(f"📥 Received event {event.id} from partition {msg.partition}, offset {msg.offset}")
                    await self.writer.add_event(event)
                    await self.consumer.commit()
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        print(f"📊 Processed {processed_count} events")
                        
                except Exception as e:
                    print(f"❗ Error processing message: {e}")
                    # Не коммитим — Kafka повторит
                    
        except Exception as e:
            print(f"💥 Kafka consumer error: {e}")
            raise
        finally:
            await self.consumer.stop()
