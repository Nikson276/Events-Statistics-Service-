from kafka import KafkaConsumer


consumer = KafkaConsumer(
    'nikson-test',
    bootstrap_servers=['localhost:9094'],
    auto_offset_reset='earliest',
    group_id='echo-messages-to-stdout',
)

for message in consumer:
    output = f"""
Topic: `{message.topic}`;
Partition: `{message.partition}`;
Offset: `{message.offset}`;
---
Message: {message.value.decode('utf-8')}
"""
    print(output)