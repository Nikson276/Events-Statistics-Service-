# scripts/init_clickhouse.py
from clickhouse_driver import Client

def main():
    client = Client(host='localhost', port=9000)
    client.execute('CREATE DATABASE IF NOT EXISTS example ON CLUSTER company_cluster')
    client.execute('''
        CREATE TABLE IF NOT EXISTS example.events ON CLUSTER company_cluster (
            id String,
            user_id String,
            track_id String,
            timestamp DateTime64(3, 'UTC')
        ) ENGINE = MergeTree
        ORDER BY (timestamp, id)
        PARTITION BY toYYYYMM(timestamp)
    ''')
    print('✅ ClickHouse schema ready')

if __name__ == '__main__':
    main()