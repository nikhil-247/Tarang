from fastapi.testclient import TestClient

from src.tarang.api import app


client = TestClient(app)


def test_health_endpoint_reports_not_ready_before_training() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_validates_network_event_payload() -> None:
    response = client.post(
        "/v1/predict",
        json={
            "src_bytes": 1000,
            "dst_bytes": 2000,
            "duration_ms": 500,
            "packet_count": 20,
            "protocol": "TCP",
            "dst_port": 443,
            "dns_query": "example.com",
            "tls": 1,
            "failed_connections": 0,
        },
    )
    # A clean 503 is expected until local model artifacts have been trained.
    assert response.status_code in (200, 503)
