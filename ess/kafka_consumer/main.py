# main_consumer.py
import asyncio
from .consumer import AsyncKafkaConsumerService

async def main():
    consumer = AsyncKafkaConsumerService()
    await consumer.start_consuming()

if __name__ == "__main__":
    asyncio.run(main())