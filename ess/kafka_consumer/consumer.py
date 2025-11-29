import asyncio
import json
from kafka import KafkaConsumer
from ess.app.schemas.event import Event
from ess.app.config import settings
from ess.app.services.clickhouse import ClickHouseService


class KafkaConsumerService:
    """Service for consuming events from Kafka topic and saving to ClickHouse."""

    def __init__(self):
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        self.topic = settings.kafka_topic
        # Используем kafka-python
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            group_id='event-statistics-service',
            enable_auto_commit=False,  # ⚠️ коммитим сами!
            value_deserializer=lambda x: x.decode('utf-8'),  # декодируем байты → строка
        )
        self.clickhouse = ClickHouseService()
        self.running = True

    async def start_consuming(self) -> None:
        """Start consuming messages from Kafka and store them in ClickHouse."""
        print(f"✅ Kafka consumer started. Listening to topic: {self.topic}")

        try:
            # kafka-python consumer — итерируемый объект
            for message in self.consumer:
                if not self.running:
                    break
                await self._process_message(message)

        except Exception as e:
            print(f"💥 Kafka consumer error: {e}")
            raise
        finally:
            self.consumer.close()

    def stop(self) -> None:
        """Gracefully stop the consumer."""
        print("🛑 Stopping Kafka consumer...")
        self.running = False

    async def _process_message(self, message) -> None:
        """Deserialize and store a single message."""
        try:
            # message.value — уже строка (благодаря value_deserializer)
            payload = json.loads(message.value)
            event = Event.model_validate(payload)

            # Запись в ClickHouse (в thread pool)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.clickhouse.insert_events, event)

            # ✅ Подтверждаем обработку
            self.consumer.commit()
            print(f"✅ Processed event: {event.id}")

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            self.consumer.commit()  # или не коммитить — зависит от стратегии

        except Exception as e:
            print(f"❌ Failed to process message: {e}")
            # Для dev — коммитим, чтобы не висеть
            self.consumer.commit()
