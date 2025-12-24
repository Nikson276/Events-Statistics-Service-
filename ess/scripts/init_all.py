# ess/scripts/init_all.py
import time
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
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

def wait_for_clickhouse(host: str):
    print("⏳ Waiting for ClickHouse...")
    while True:
        try:
            client = Client(host=host, port=9000)
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
        num_partitions=36,
        replication_factor=3,
        topic_configs={
            "min.insync.replicas": "2",
            "retention.ms": "604800000",  # 7 дней
        }
    )
    try:
        admin.create_topics([topic])
        print("✅ Kafka topic created")
    except TopicAlreadyExistsError:
        print("ℹ️  Kafka topic already exists — skipping")
    except Exception as e:
        print(f"❌ Failed to create Kafka topic: {e}")
        raise

# def create_clickhouse_schema():
#     print("🗃️ Creating ClickHouse schema...")
#     client = Client(host="clickhouse-node1", port=9000)
#     client.execute("CREATE DATABASE IF NOT EXISTS example ON CLUSTER company_cluster")
#     client.execute("""
#         CREATE TABLE IF NOT EXISTS example.events ON CLUSTER company_cluster (
#             id String,
#             user_id String,
#             track_id String,
#             ingest_time DateTime64(3, 'UTC'),
#             store_time DateTime64(3, 'UTC')
#         ) ENGINE = MergeTree
#         ORDER BY (ingest_time, id)
#         PARTITION BY toYYYYMM(ingest_time)
#     """)

def create_clickhouse_schema():
    print("🗃️ Creating ClickHouse schema on all shards...")

    # Подключаемся к КАЖДОЙ ноде и создаём таблицы
    nodes = ["clickhouse-node1", "clickhouse-node2", "clickhouse-node3", "clickhouse-node4"]
    for host in nodes:
        wait_for_clickhouse(host)
        client = Client(host=host, port=9000 )

        print(f"Creating DB & Tables on node {host}")
        # 1. Локальная реплицируемая таблица
        client.execute("""
            CREATE DATABASE IF NOT EXISTS example
        """)
        client.execute("""
            CREATE TABLE IF NOT EXISTS example.events_local (
                id String,
                user_id String,
                track_id String,
                ingest_time DateTime64(3, 'UTC'),
                store_time DateTime64(3, 'UTC')
            ) ENGINE = ReplicatedReplacingMergeTree(
                '/clickhouse/company_cluster/tables/{shard}/events_local',
                '{replica}',
                store_time
            )
            ORDER BY (id, store_time)
        """)

        # 2. Распределённая таблица (на каждой ноде)
        client.execute("""
            CREATE TABLE IF NOT EXISTS example.events AS example.events_local
            ENGINE = Distributed(
                company_cluster,
                example,
                events_local,
                cityHash64(user_id)
            )
        """)
        print(f"DB & Tables on node {host} were created")

    print("✅ ClickHouse schema created on all nodes")

if __name__ == "__main__":
    wait_for_kafka()
    create_kafka_topic()
    create_clickhouse_schema()
    print("✅ All schemas initialized!")
