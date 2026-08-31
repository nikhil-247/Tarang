import pandas as pd

from src.tarang.features import extract_features, model_columns


def test_protocol_features_are_created():
    df = pd.DataFrame(
        [
            {
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
        ]
    )
    features = extract_features(df)
    assert set(model_columns()).issubset(features.columns)
    assert features.loc[0, "proto_TCP"] == 1


def test_derived_features_are_non_negative():
    df = pd.DataFrame(
        [
            {
                "src_bytes": 100,
                "dst_bytes": 200,
                "duration_ms": 1000,
                "packet_count": 10,
                "protocol": "HTTP",
                "dst_port": 80,
                "dns_query": "api.example.com",
                "tls": 0,
                "failed_connections": 1,
            }
        ]
    )
    features = extract_features(df)
    assert features.loc[0, "bytes_per_packet"] >= 0
    assert features.loc[0, "packets_per_second"] >= 0
