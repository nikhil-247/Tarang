from types import SimpleNamespace

from fastapi.testclient import TestClient

import tarang.api as api


client = TestClient(api.app)


def valid_event() -> dict[str, object]:
    return {
        "src_bytes": 1000,
        "dst_bytes": 2000,
        "duration_ms": 500,
        "packet_count": 20,
        "protocol": "TCP",
        "dst_port": 443,
        "dns_query": "example.com",
        "tls": 1,
        "failed_connections": 0,
    }


def test_health_endpoint_reports_service_state() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_status"] in {"ready", "not_ready"}


def test_predict_returns_normalized_result_when_detector_is_ready(monkeypatch) -> None:
    result = SimpleNamespace(
        label="normal",
        confidence=0.91,
        anomaly_score=0.12,
        anomaly=False,
        risk="low",
    )
    detector = SimpleNamespace(predict_one=lambda _event: result)
    monkeypatch.setattr(api, "get_detector", lambda: detector)

    response = client.post("/v1/predict", json=valid_event())

    assert response.status_code == 200
    assert response.json() == {
        "label": "normal",
        "confidence": 0.91,
        "anomaly_score": 0.12,
        "anomaly": False,
        "risk": "low",
    }


def test_predict_returns_503_when_model_artifacts_are_missing(monkeypatch) -> None:
    def missing_model():
        raise RuntimeError("Model artifacts are unavailable. Run scripts/train.py first.")

    monkeypatch.setattr(api, "get_detector", missing_model)

    response = client.post("/v1/predict", json=valid_event())

    assert response.status_code == 503
    assert "Model artifacts are unavailable" in response.json()["detail"]


def test_predict_rejects_invalid_network_event(monkeypatch) -> None:
    response = client.post("/v1/predict", json={**valid_event(), "dst_port": 70000})

    assert response.status_code == 422
