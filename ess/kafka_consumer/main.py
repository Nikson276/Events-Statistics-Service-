# ess/kafka_consumer/main.py
import asyncio
from .async_consumer import AsyncKafkaConsumerService, AsyncClickHouseBatchWriter

async def main():
    writer = AsyncClickHouseBatchWriter(batch_size=5000, flush_timeout=5.0)
    await writer.start()
    
    consumer = AsyncKafkaConsumerService(writer)
    try:
        await consumer.start_consuming()
    finally:
        await writer.stop()

if __name__ == "__main__":
    asyncio.run(main())
