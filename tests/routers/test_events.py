import pytest
from datetime import datetime

from fastapi.testclient import TestClient
from ess.app.main import app
from ess.app.schemas.event import Event
from ess.app.services.kafka import KafkaProducerService
from ess.app.services.clickhouse import ClickHouseService


class FakeKafkaProducerService:
    def __init__(self):
        self.sent = []

    async def send_event(self, event: Event):
        self.sent.append(event)


class FakeClickHouseService:
    def __init__(self):
        # pre-populate with one event
        self.events = [
            Event(
                id="e1",
                user_id="u1",
                track_id="t1",
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
            )
        ]

    def get_events(self, limit: int = 10, offset: int = 0):
        return self.events[offset : offset + limit]


@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    fake_kafka = FakeKafkaProducerService()
    fake_clickhouse = FakeClickHouseService()
    # Override DI dependencies
    app.dependency_overrides[KafkaProducerService] = lambda: fake_kafka
    app.dependency_overrides[ClickHouseService] = lambda: fake_clickhouse
    return fake_kafka, fake_clickhouse


@pytest.fixture()
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "ESS Service is running"}


def test_create_event_success(client, override_dependencies):
    fake_kafka, _ = override_dependencies
    payload = {
        "id": "ev1",
        "user_id": "u1",
        "track_id": "t1",
        "timestamp": "2023-01-01T12:00:00Z",
    }
    response = client.post("/events/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "queued"}
    # verify event sent to Kafka stub
    assert len(fake_kafka.sent) == 1
    sent_event = fake_kafka.sent[0]
    assert sent_event.dict() == Event(**payload).dict()


def test_create_event_validation_error(client):
    # missing required fields
    response = client.post("/events/", json={"user_id": "u1"})
    assert response.status_code == 422


def test_list_events_success(client, override_dependencies):
    _, fake_clickhouse = override_dependencies
    response = client.get("/events/?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    expected = [e.dict() for e in fake_clickhouse.events]
    assert data == expected
