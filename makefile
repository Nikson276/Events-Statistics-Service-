.PHONY: help setup-kafka setup-clickhouse start-api start-consumer start stop clean

# === Целевые команды ===

help:
	@echo "Usage:"
	@echo "  make setup       # Запустить Kafka + ClickHouse и подготовить схемы"
	@echo "  make start       # Запустить FastAPI и Kafka consumer"
	@echo "  make stop        # Остановить все процессы"
	@echo "  make clean       # Очистить данные и остановить всё"
	@echo "  make only-clean  # Только очистить"

# === Подготовка инфраструктуры ===

setup: setup-kafka setup-clickhouse

setup-kafka:
	@echo "🚀 Starting Kafka cluster..."
	@cd kafka-cluster && docker compose up -d
	@sleep 5
	@echo "📦 Creating Kafka topic 'nikson-test'..."
	@cd kafka-cluster && docker compose exec -T kafka-0 \
		/opt/kafka/bin/kafka-topics.sh --create \
			--topic nikson-test \
			--bootstrap-server localhost:9094 \
			--partitions 3 \
			--replication-factor 3

setup-clickhouse:
	@echo "🚀 Starting ClickHouse cluster..."
	@cd clickhouse-cluster && docker compose up -d
	@sleep 10
	@echo "🗃️  Creating database and table..."
	@python3 ess/scripts/init_clickhouse.py

# === Запуск приложений ===

start: start-api start-consumer

start-api:
	@echo "🔌 Starting FastAPI server..."
	@nohup python3 -m ess.app.main > fastapi.log 2>&1 & echo $$! > fastapi.pid

start-consumer:
	@echo "📬 Starting Kafka consumer..."
	@nohup python3 -m ess.kafka_consumer.main > consumer.log 2>&1 & echo $$! > consumer.pid

# === Остановка ===

stop:
	@if [ -f fastapi.pid ]; then kill $$(cat fastapi.pid) && rm fastapi.pid && echo "⏹️  FastAPI stopped"; fi
	@if [ -f consumer.pid ]; then kill $$(cat consumer.pid) && rm consumer.pid && echo "⏹️  Consumer stopped"; fi

# === Полная очистка ===

clean: stop
	@echo "🧹 Stopping and removing Kafka & ClickHouse..."
	@cd kafka-cluster && docker compose down -v
	@cd clickhouse-cluster && docker compose down -v
	@rm -f *.log *.pid
	@echo "✨ All cleaned up!"

# === Только очистка ===

only-clean:
	@echo "🧹 Stopping and removing Kafka & ClickHouse..."
	@cd kafka-cluster && docker compose down -v
	@cd clickhouse-cluster && docker compose down -v
	@rm -f *.log *.pid
	@echo "✨ All cleaned up!"
