from pathlib import Path
import argparse
import pandas as pd
from features import build_from_file

LABELS = {"benign": 0, "ransomware": 1}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw")
    ap.add_argument("--output", default="data/processed/dataset.csv")
    ap.add_argument("--window", type=int, default=10)
    args = ap.parse_args()

    root = Path(args.input)
    frames = []
    for cls, label in LABELS.items():
        folder = root / cls
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.jsonl")):
            df = build_from_file(path, label, path.stem, args.window)
            if not df.empty:
                frames.append(df)

    if not frames:
        raise SystemExit(
            "No JSONL runs found. Put benign logs in data/raw/benign/ and "
            "ransomware logs in data/raw/ransomware/."
        )

    dataset = pd.concat(frames, ignore_index=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(args.output, index=False)

    print(f"Created {args.output}")
    print(f"Rows: {len(dataset)}")
    print("Class counts:", dataset["label"].value_counts().sort_index().to_dict())
    print("Sessions:", dataset["session_id"].nunique())

if __name__ == "__main__":
    main()
