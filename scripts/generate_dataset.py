from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

random.seed(42)

PROFILES = {
    "benign": ["TCP", "UDP", "HTTP", "TLS", "DNS"],
    "suspicious": ["TCP", "UDP", "DNS"],
    "exfiltration": ["TCP", "TLS"],
    "scan": ["TCP", "UDP"],
}


def make_row(i: int) -> dict:
    label = random.choices(
        ["benign", "suspicious", "exfiltration", "scan"],
        weights=[0.72, 0.12, 0.08, 0.08],
        k=1,
    )[0]
    protocol = random.choice(PROFILES[label])

    if label == "benign":
        src = random.randint(80, 8000)
        dst = random.randint(100, 12000)
        duration = random.randint(20, 3000)
        packets = random.randint(4, 120)
        port = random.choice([53, 80, 443, 123, 8080])
        failed = random.randint(0, 2)
        dns = random.choice(["example.com", "cdn.example.net", "api.service.local", ""])
        tls = int(protocol == "TLS")
    elif label == "suspicious":
        src = random.randint(5000, 50000)
        dst = random.randint(200, 4000)
        duration = random.randint(10, 1200)
        packets = random.randint(2, 60)
        port = random.randint(1, 65535)
        failed = random.randint(2, 15)
        dns = random.choice(["xj3k9q2m.example", "a8f1e7bad.test", ""])
        tls = int(protocol == "TLS")
    elif label == "exfiltration":
        src = random.randint(200000, 1200000)
        dst = random.randint(100, 2500)
        duration = random.randint(50, 2400)
        packets = random.randint(40, 500)
        port = random.choice([443, 8443, 9001, 10443])
        failed = random.randint(0, 3)
        dns = random.choice(["upload-cache.example", "edge-storage.example", ""])
        tls = 1
    else:
        src = random.randint(20, 1000)
        dst = random.randint(20, 1000)
        duration = random.randint(1, 400)
        packets = random.randint(10, 80)
        port = random.randint(1, 65535)
        failed = random.randint(5, 30)
        dns = ""
        tls = 0

    timestamp = datetime.now(timezone.utc) - timedelta(minutes=(1200 - i) * 2)
    return {
        "timestamp": timestamp.isoformat(),
        "src_bytes": src,
        "dst_bytes": dst,
        "duration_ms": duration,
        "packet_count": packets,
        "protocol": protocol,
        "dst_port": port,
        "dns_query": dns,
        "tls": tls,
        "failed_connections": failed,
        "label": label,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--output", type=Path, default=Path("data/network_events.csv"))
    args = parser.parse_args()

    if args.rows < 100:
        raise ValueError("Use at least 100 rows to create a useful demo dataset")

    rows = [make_row(i) for i in range(args.rows)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {len(rows):,} records to {args.output}")


if __name__ == "__main__":
    main()
