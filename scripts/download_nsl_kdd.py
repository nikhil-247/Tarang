from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request

FILES = {
    "KDDTrain+.txt": {
        "url": "https://zenodo.org/records/17424143/files/KDDTrain%2B.txt?download=1",
        "md5": "120b13c9092ab72d4902f2079143cc2c",
    },
    "KDDTest+.txt": {
        "url": "https://zenodo.org/records/17424143/files/KDDTest%2B.txt?download=1",
        "md5": "1e53a506c102628114ca1b1fa509b6a8",
    },
}

def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Tarang-Network-Benchmark/1.0"})
    with urlopen(request, timeout=60) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)

def main() -> None:
    parser = argparse.ArgumentParser(description="Download a pinned NSL-KDD benchmark copy.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/nsl-kdd"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifest = {}
    for name, meta in FILES.items():
        target = args.output_dir / name
        if target.exists() and not args.force:
            print(f"exists: {target}")
        else:
            print(f"download: {name}")
            download(meta["url"], target)

        observed = md5(target)
        if observed != meta["md5"]:
            raise RuntimeError(f"MD5 mismatch for {name}: expected {meta['md5']}, got {observed}")
        manifest[name] = {"url": meta["url"], "md5": observed, "bytes": target.stat().st_size}
        print(f"verified: {name} ({target.stat().st_size:,} bytes)")

    import json
    (args.output_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {args.output_dir / 'MANIFEST.json'}")

if __name__ == "__main__":
    main()
