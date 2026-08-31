from __future__ import annotations

from math import log2
from typing import Any

import pandas as pd

PROTOCOLS = ["TCP", "UDP", "DNS", "HTTP", "TLS"]


def _safe_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(value)
    return -sum((c / n) * log2(c / n) for c in counts.values())


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "src_bytes",
        "dst_bytes",
        "duration_ms",
        "packet_count",
        "protocol",
        "dst_port",
        "dns_query",
        "tls",
        "failed_connections",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()
    out["protocol"] = out["protocol"].fillna("TCP").astype(str).str.upper()
    out["duration_ms"] = pd.to_numeric(out["duration_ms"], errors="coerce").fillna(0)
    out["src_bytes"] = pd.to_numeric(out["src_bytes"], errors="coerce").fillna(0)
    out["dst_bytes"] = pd.to_numeric(out["dst_bytes"], errors="coerce").fillna(0)
    out["packet_count"] = pd.to_numeric(out["packet_count"], errors="coerce").fillna(0)
    out["dst_port"] = pd.to_numeric(out["dst_port"], errors="coerce").fillna(0)
    out["failed_connections"] = pd.to_numeric(out["failed_connections"], errors="coerce").fillna(0)
    out["tls"] = out["tls"].astype(int)

    out["byte_ratio"] = (out["src_bytes"] + 1) / (out["dst_bytes"] + 1)
    out["bytes_per_packet"] = (out["src_bytes"] + out["dst_bytes"]) / (out["packet_count"] + 1)
    out["packets_per_second"] = out["packet_count"] / (out["duration_ms"] / 1000 + 1)
    out["dns_entropy"] = out["dns_query"].fillna("").astype(str).map(_safe_entropy)
    out["high_port"] = (out["dst_port"] >= 49152).astype(int)
    out["failed_connection_rate"] = out["failed_connections"] / (out["packet_count"] + 1)

    protocol_dummies = pd.get_dummies(out["protocol"], prefix="proto", dtype=int)
    for protocol in PROTOCOLS:
        col = f"proto_{protocol}"
        if col not in protocol_dummies:
            protocol_dummies[col] = 0
    out = pd.concat([out, protocol_dummies], axis=1)
    return out


def model_columns() -> list[str]:
    return [
        "src_bytes",
        "dst_bytes",
        "duration_ms",
        "packet_count",
        "dst_port",
        "tls",
        "byte_ratio",
        "bytes_per_packet",
        "packets_per_second",
        "dns_entropy",
        "high_port",
        "failed_connection_rate",
        *[f"proto_{p}" for p in PROTOCOLS],
    ]
