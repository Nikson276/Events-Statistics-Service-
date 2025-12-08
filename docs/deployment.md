
# Как запустить, настроить

Запуск

```bash
make setup
make start
```

Остановка и очистка

```bash
make clean
```

## Как использовать

```bash
# В корне ESS/
docker compose up -d          # запустить всё
docker compose logs -f        # смотреть логи
docker compose down -v        # остановить и удалить данные
```

FastAPI: http://localhost:8000
Kafka UI: http://localhost:8080
ClickHouse HTTP: http://localhost:8123