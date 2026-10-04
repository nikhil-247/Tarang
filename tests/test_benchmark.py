import numpy as np
import pandas as pd

from tarang.benchmark import NSLKDD_COLUMNS, binary_labels, build_preprocessor

def make_frame(n: int = 20) -> pd.DataFrame:
    rows = []
    for i in range(n):
        row = [0] * len(NSLKDD_COLUMNS)
        row[1] = "tcp"
        row[2] = "http" if i % 2 else "private"
        row[3] = "SF"
        row[4] = 100 + i
        row[5] = 200 + i
        row[-2] = "normal" if i < n // 2 else "neptune"
        row[-1] = 21
        rows.append(row)
    return pd.DataFrame(rows, columns=NSLKDD_COLUMNS)

def test_binary_labels_and_preprocessor():
    frame = make_frame()
    y = binary_labels(frame)
    assert int(y.sum()) == 10
    preprocessor = build_preprocessor()
    transformed = preprocessor.fit_transform(frame[NSLKDD_COLUMNS[:-2]])
    assert transformed.shape[0] == 20
    assert transformed.shape[1] > len(NSLKDD_COLUMNS) - 2


def test_nsl_kdd_loader_tab_delimited(tmp_path):
    path = tmp_path / "KDDTest+.txt"
    row = "\t".join([
        "0", "tcp", "http", "SF", "10", "20", "0", "0", "0", "0",
        "0", "1", "0", "0", "0", "0", "0", "0", "0", "0", "0",
        "0", "1", "1", "0", "0", "0", "0", "1", "0", "0", "10",
        "10", "1.0", "0.0", "1.0", "0.0", "0.0", "0.0", "1.0",
        "0.0", "normal", "21"
    ])
    path.write_text(row + "\n", encoding="utf-8")
    from tarang.benchmark import load_nsl_kdd
    loaded = load_nsl_kdd(path)
    assert list(loaded.columns) == NSLKDD_COLUMNS
    assert loaded.iloc[0]["label"] == "normal"
