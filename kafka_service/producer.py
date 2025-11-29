from kafka import KafkaProducer
from time import sleep


producer = KafkaProducer(bootstrap_servers=['localhost:9094'])

while True:
    message_text = input("Write your message: ")
    message_bytes = message_text.encode()

    producer.send(
        topic='nikson-test',
        value=message_bytes,
        key=b'python-message',
    )

    sleep(1)
