import time
from kafka.admin import KafkaAdminClient, NewTopic
from clickhouse_driver import Client

def wait_for_kafka():
    print("⏳ Waiting for Kafka...")
    while True:
        try:
            admin = KafkaAdminClient(bootstrap_servers="kafka-0:9092")
            admin.list_topics()
            break
        except Exception as e:
            print(f"Kafka not ready: {e}")
            time.sleep(2)

def wait_for_clickhouse():
    print("⏳ Waiting for ClickHouse...")
    while True:
        try:
            client = Client(host="clickhouse-node1", port=9000)
            client.execute("SELECT 1")
            break
        except Exception as e:
            print(f"ClickHouse not ready: {e}")
            time.sleep(2)

def create_kafka_topic():
    print("📦 Creating Kafka topic...")
    admin = KafkaAdminClient(bootstrap_servers="kafka-0:9092")
    topic = NewTopic(
        name="nikson-test",
        num_partitions=12,  # достаточно для 500+ RPS
        replication_factor=3,
        topic_configs={
            "min.insync.replicas": "2",
            "compression.type": "lz4",
            "retention.ms": "604800000",  # 7 дней
        }
    )
    admin.create_topics([topic])

def create_clickhouse_schema():
    print("🗃️ Creating ClickHouse schema...")
    client = Client(host="clickhouse-node1", port=9000)
    client.execute("CREATE DATABASE IF NOT EXISTS example ON CLUSTER company_cluster")
    client.execute("""
        CREATE TABLE IF NOT EXISTS example.events ON CLUSTER company_cluster (
            id String,
            user_id String,
            track_id String,
            timestamp DateTime64(3, 'UTC')
        ) ENGINE = MergeTree
        ORDER BY (timestamp, id)
        PARTITION BY toYYYYMM(timestamp)
    """)

if __name__ == "__main__":
    wait_for_kafka()
    wait_for_clickhouse()
    create_kafka_topic()
    create_clickhouse_schema()
    print("✅ All schemas initialized!")
