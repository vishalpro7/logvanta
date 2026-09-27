from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_json_pipeline():
    response = client.post("/api/v1/process", json={
        "source": "firewall-json",
        "raw_log": '{"timestamp":"2026-09-27T10:30:00Z","src_ip":"192.168.1.10","dst_ip":"10.0.0.5","action":"deny","severity":"high"}'
    })
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["detected_format"] == "json"
    assert body["normalized"]["source_endpoint"] == "192.168.1.10"
    assert body["traceability"]["raw_preserved"] is True


def test_key_value_pipeline():
    response = client.post("/api/v1/process", json={
        "source": "firewall-kv",
        "raw_log": 'src_ip=192.168.1.20 dst_ip=10.0.0.8 action=allow'
    })
    assert response.status_code == 200
    assert response.json()["profile"]["detected_format"] == "key_value"
