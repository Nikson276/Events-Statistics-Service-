
# Как использовать

Через .sh скрипт

```bash
./start.sh
```

или вручную 

```bash
# В корне ESS/
docker compose up -d          # запустить всё
docker compose --profile consumers up -d  # Запустить консьюмеры отдельно
docker compose logs -f        # смотреть логи
docker compose stats          # смотреть метрики контейнеров
docker compose down -v        # остановить и удалить данные
```

FastAPI: http://localhost:8000
Kafka UI: http://localhost:8080
ClickHouse HTTP: http://localhost:8123

## Запуск тестов

Запускаем внутри сети докер, в временном контейнере

```bash
docker compose run --rm k6
```

## Работа с clickhouse

Следить за БД

```bash
watch -n 30 "docker compose exec clickhouse-node1 clickhouse-client --query 'SELECT count() FROM example.events'"
```

Внутри контейнера

```bash
docker compose exec -it clickhouse-node1 bash

clickhouse-client

SHOW TABLES IN example;

SELECT * FROM example.events;


SELECT 
  count() AS total,
  avg(dateDiff('second', ingest_time, store_time)) AS avg_e2e_sec,
  quantiles(0.5, 0.9, 0.95, 0.99)(
    dateDiff('second', ingest_time, store_time)
  ) AS p_latencies_sec
FROM example.events
WHERE store_time IS NOT NULL;
```

## Работа с Kafka

Зайти в контейнер

```bash
docker compose exec kafka-0
```

Проверить, состояние и показатели на консьюмер группе

```bash
docker compose exec kafka-0 /opt/kafka/bin/kafka-consumer-groups.sh   --bootstrap-server localhost:9092   --group event-statistics-service   --describe
```

Следить за лагом 

```bash
watch -n 30 "docker compose exec kafka-0 /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group event-statistics-service --describe | tail -n +2 | awk '{sum += \$5} END {print \"Processed:\", sum}'"
```

Проверь, есть ли активный контроллер для группы консьюмеров

```bash
docker compose exec kafka-0 /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server localhost:9092 describe --status

>> 
ClusterId:              Some(abcdefghijklmnopqrstuv)
LeaderId:               1
LeaderEpoch:            1
HighWatermark:          910
MaxFollowerLag:         0
MaxFollowerLagTimeMs:   461
CurrentVoters:          [0,1,2]
CurrentObservers:       []
```

**Что это значит:**

- LeaderId: 1 → нода kafka-1 — активный контроллер (это и есть "ActiveController").
- CurrentVoters: [0,1,2] → все 3 ноды участвуют в кворуме.
- MaxFollowerLag: 0 → все ноды синхронизированы.