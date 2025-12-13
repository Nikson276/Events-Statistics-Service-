# ess/app/schemas/event.py
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone


class Event(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="User who triggered the event")
    track_id: str = Field(..., description="Track being played")
    
    # 1. Время создания события (из k6 / клиента)
    ingest_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 2. Время записи в ClickHouse (устанавливается consumer'ом)
    store_time: datetime | None = Field(None, description="When event was written to ClickHouse")

    @field_serializer('ingest_time', 'store_time')
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return dt.isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "event123",
                "user_id": "user456",
                "track_id": "track789",
                "ingest_time": "2025-06-01T12:00:00Z",
                "store_time": "2025-06-01T12:00:02Z",
            }
        }
