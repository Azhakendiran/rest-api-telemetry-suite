import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app

client = TestClient(app)

VALID = {"device_id": "router-01", "cpu_percent": 45.5, "memory_percent": 60}


@pytest.fixture(autouse=True)
def reset_state():
    """Each test starts with an empty in-memory DB."""
    main.db.clear()
    main.counter = 0
    yield


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_telemetry():
    r = client.post("/telemetry", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["device_id"] == "router-01"
    assert "timestamp" in body


def test_get_telemetry_by_id():
    client.post("/telemetry", json=VALID)
    r = client.get("/telemetry/1")
    assert r.status_code == 200
    assert r.json()["cpu_percent"] == 45.5


def test_get_missing_returns_404():
    r = client.get("/telemetry/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Record not found"


def test_list_and_filter_by_device():
    client.post("/telemetry", json=VALID)
    client.post("/telemetry", json={**VALID, "device_id": "switch-02"})
    assert len(client.get("/telemetry").json()) == 2
    r = client.get("/telemetry", params={"device_id": "switch-02"})
    assert len(r.json()) == 1
    assert r.json()[0]["device_id"] == "switch-02"


def test_delete_telemetry():
    client.post("/telemetry", json=VALID)
    assert client.delete("/telemetry/1").status_code == 204
    assert client.get("/telemetry/1").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "cpu_percent": 150},      # above range
        {**VALID, "memory_percent": -5},    # below range
        {**VALID, "device_id": ""},         # empty id
        {"device_id": "router-01"},         # missing fields
    ],
)
def test_invalid_payload_returns_422(payload):
    r = client.post("/telemetry", json=payload)
    assert r.status_code == 422