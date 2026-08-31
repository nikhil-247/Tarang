from __future__ import annotations

from math import log2

import pandas as pd

# Canonical protocol vocabulary used by both training and inference.
PROTOCOLS = ["TCP", "UDP", "DNS", "HTTP", "HTTPS", "TLS"]

REQUIRED_COLUMNS = [
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


def _safe_entropy(value: str) -> float:
    """Calculate Shannon entropy for a short string without raising on empty input."""
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    return -sum((count / length) * log2(count / length) for count in counts.values())


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Validate raw event columns and produce model-ready numeric features."""
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = df.copy()
    out["protocol"] = out["protocol"].fillna("TCP").astype(str).str.upper().replace({"HTTPS": "HTTPS"})

    numeric_columns = [
        "duration_ms",
        "src_bytes",
        "dst_bytes",
        "packet_count",
        "dst_port",
        "failed_connections",
    ]
    for column in numeric_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0).clip(lower=0)

    out["tls"] = pd.to_numeric(out["tls"], errors="coerce").fillna(0).clip(0, 1).astype(int)
    out["dns_query"] = out["dns_query"].fillna("").astype(str)

    # Ratios use +1 guards so malformed/empty events do not generate infinities.
    out["byte_ratio"] = (out["src_bytes"] + 1.0) / (out["dst_bytes"] + 1.0)
    out["bytes_per_packet"] = (out["src_bytes"] + out["dst_bytes"]) / (out["packet_count"] + 1.0)
    out["packets_per_second"] = out["packet_count"] / (out["duration_ms"] / 1000.0 + 1.0)
    out["dns_entropy"] = out["dns_query"].map(_safe_entropy)
    out["dns_length"] = out["dns_query"].str.len().astype(float)
    out["high_port"] = (out["dst_port"] >= 49152).astype(int)
    out["well_known_port"] = out["dst_port"].isin([22, 53, 80, 123, 443, 8080, 8443]).astype(int)
    out["failed_connection_rate"] = out["failed_connections"] / (out["packet_count"] + 1.0)

    protocol_dummies = pd.get_dummies(out["protocol"], prefix="proto", dtype=int)
    for protocol in PROTOCOLS:
        column = f"proto_{protocol}"
        if column not in protocol_dummies:
            protocol_dummies[column] = 0

    out = pd.concat([out, protocol_dummies[[f"proto_{p}" for p in PROTOCOLS]]], axis=1)
    return out


def model_columns() -> list[str]:
    """Return the stable feature order expected by trained models."""
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
        "dns_length",
        "high_port",
        "well_known_port",
        "failed_connection_rate",
        *[f"proto_{protocol}" for protocol in PROTOCOLS],
    ]
