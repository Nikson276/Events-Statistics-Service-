
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

## Nginx balancer 

```bash
# Пересобери (если менял код или requirements.txt)
docker compose build

# Запусти всё, включая nginx
docker compose up -d

# Масштабируй fastapi до 3 реплик
docker compose scale fastapi=3
```

## Запуск тестов

Запускаем внутри сети докер, в временном контейнере

```bash
docker compose run --rm k6
```

