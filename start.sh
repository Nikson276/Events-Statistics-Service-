#!/bin/bash
docker compose up -d
echo "Waiting for Kafka to stabilize..."
sleep 120
docker compose --profile consumers up -d
echo "Consumers started!"