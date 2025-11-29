from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone

class Event(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    user_id: str = Field(..., description="User who triggered the event")
    track_id: str = Field(..., description="Track being played")
    timestamp: datetime = Field(default_factory=datetime.now(timezone.utc))
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime) -> str:
        return dt.isoformat()

    class Config:
        json_schema_extra = {
            "example": {
                "id": "event123",
                "user_id": "user456",
                "track_id": "track789",
                "timestamp": "2023-01-01T12:00:00Z",
            }
        }
