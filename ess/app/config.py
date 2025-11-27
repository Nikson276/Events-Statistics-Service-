from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "nikson-test"
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_database: str = "default"
    clickhouse_table: str = "events"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton settings instance
settings = Settings()
    