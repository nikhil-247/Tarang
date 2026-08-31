import pandas as pd
import pytest

from src.tarang.features import extract_features, model_columns


def _event(protocol: str = "TCP") -> dict:
    return {
        "src_bytes": 1000,
        "dst_bytes": 2000,
        "duration_ms": 500,
        "packet_count": 20,
        "protocol": protocol,
        "dst_port": 443,
        "dns_query": "example.com",
        "tls": 1,
        "failed_connections": 0,
    }


def test_protocol_features_are_created() -> None:
    features = extract_features(pd.DataFrame([_event("TCP")]))
    assert set(model_columns()).issubset(features.columns)
    assert features.loc[0, "proto_TCP"] == 1
    assert features.loc[0, "proto_HTTPS"] == 0


def test_https_is_a_supported_protocol() -> None:
    features = extract_features(pd.DataFrame([_event("HTTPS")]))
    assert features.loc[0, "proto_HTTPS"] == 1


def test_derived_features_are_non_negative() -> None:
    features = extract_features(pd.DataFrame([_event("HTTP")]))
    assert features.loc[0, "bytes_per_packet"] >= 0
    assert features.loc[0, "packets_per_second"] >= 0
    assert features.loc[0, "dns_entropy"] >= 0


def test_missing_required_columns_raise_clear_error() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        extract_features(pd.DataFrame([{ "src_bytes": 1 }]))
