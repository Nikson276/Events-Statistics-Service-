# main_consumer.py
import asyncio
from .consumer import KafkaConsumerService

async def main():
    consumer = KafkaConsumerService()
    try:
        await consumer.start_consuming()
    except KeyboardInterrupt:
        consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())