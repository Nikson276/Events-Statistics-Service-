import os
from datetime import datetime
from clickhouse_driver import Client
from ess.app.schemas.event import Event
from ess.app.config import settings


class ClickHouseService:
    """Service for querying events from ClickHouse."""
    def __init__(self):
        self.host = settings.clickhouse_host
        self.port = settings.clickhouse_port
        self.database = settings.clickhouse_database
        self.table = settings.clickhouse_table
        # Initialize ClickHouse client
        self.client = Client(
            host=self.host,
            port=self.port,
            database=self.database,
        )

    def get_events(self, limit: int = 10, offset: int = 0) -> list[Event]:
        """Fetch events from ClickHouse table."""
        query = (
            f"SELECT id, user_id, track_id, timestamp "
            f"FROM {self.database}.{self.table} "
            f"ORDER BY timestamp DESC "
            f"LIMIT %(limit)s OFFSET %(offset)s"
        )
        params = {"limit": limit, "offset": offset}
        rows = self.client.execute(query, params)
        events: list[Event] = []
        for id_, user_id, track_id, ts in rows:
            # ts is datetime or string
            timestamp = ts if isinstance(ts, datetime) else datetime.fromisoformat(ts)
            events.append(
                Event(id=id_, user_id=user_id, track_id=track_id, timestamp=timestamp)
            )
        return events
