import os
from datetime import datetime
from typing import Union, List
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
            f"SELECT id, user_id, track_id, ingest_time, store_time "
            f"FROM {self.database}.{self.table} "
            f"ORDER BY ingest_time DESC "
            f"LIMIT %(limit)s OFFSET %(offset)s"
        )
        params = {"limit": limit, "offset": offset}
        rows = self.client.execute(query, params)
        events: list[Event] = []
        for id_, user_id, track_id, ingtime, strtime in rows:
            # ts is datetime or string
            ingest_time = ingtime if isinstance(ingtime, datetime) else datetime.fromisoformat(ingtime)
            store_time = strtime if isinstance(strtime, datetime) else datetime.fromisoformat(strtime)
            events.append(
                Event(id=id_, user_id=user_id, track_id=track_id, ingest_time=ingest_time, store_time=store_time)
            )
        return events
        
    def insert_events(self, events: Union[Event, List[Event]]) -> None:
        """Insert one or more events into ClickHouse table."""
        event_list = [events] if isinstance(events, Event) else events
        if not event_list:
            return

        # Подготавливаем данные как список кортежей
        data = [
            (e.id, e.user_id, e.track_id, e.ingest_time, e.store_time)
            for e in event_list
        ]

        # Используем executemany-стиль: один запрос с VALUES и списком данных
        query = f"""
            INSERT INTO {self.database}.{self.table}  
            (id, user_id, track_id, ingest_time, store_time) 
            VALUES
        """
        self.client.execute(query, data)