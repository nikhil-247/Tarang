from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .detector import TarangDetector

MODEL_DIR = Path(os.getenv("TARANG_MODEL_DIR", "artifacts"))

app = FastAPI(
    title="Tarang Threat Detection API",
    version="0.2.0",
    description="Defensive network-event scoring API backed by a hybrid anomaly/classification pipeline.",
)


class NetworkEvent(BaseModel):
    timestamp: str | None = None
    src_bytes: float = Field(ge=0)
    dst_bytes: float = Field(ge=0)
    duration_ms: float = Field(ge=0)
    packet_count: float = Field(ge=0)
    protocol: str = "TCP"
    dst_port: int = Field(ge=0, le=65535)
    dns_query: str = ""
    tls: int = Field(default=0, ge=0, le=1)
    failed_connections: float = Field(default=0, ge=0)


@lru_cache(maxsize=1)
def get_detector() -> TarangDetector:
    try:
        return TarangDetector.load(MODEL_DIR)
    except FileNotFoundError as exc:
        raise RuntimeError("Model artifacts are unavailable. Run scripts/train.py first.") from exc


@app.get("/health")
def health() -> dict[str, str]:
    ready = (MODEL_DIR / "random_forest.joblib").exists() and (MODEL_DIR / "isolation_forest.joblib").exists()
    return {"status": "ok", "model_status": "ready" if ready else "not_ready"}


@app.post("/v1/predict")
def predict(event: NetworkEvent) -> dict[str, object]:
    try:
        result = get_detector().predict_one(event.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "label": result.label,
        "confidence": result.confidence,
        "anomaly_score": result.anomaly_score,
        "anomaly": result.anomaly,
        "risk": result.risk,
    }
