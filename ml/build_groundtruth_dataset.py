from pathlib import Path
import json

import pandas as pd

from features import build_from_file, read_jsonl


LABELS = {
    "benign": 0,
    "ransomware": 1,
}

WINDOW_SECONDS = 10


def normalized_timestamp(event):
    ts = float(event.get("timestamp", 0))

    if ts > 1e12:
        ts /= 1000.0

    return ts


def load_groundtruth(path: Path):
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def apply_groundtruth(
    features: pd.DataFrame,
    events: list[dict],
    groundtruth: dict,
    window_seconds: int,
) -> pd.DataFrame:

    timestamps = [
        normalized_timestamp(e)
        for e in events
        if e.get("timestamp") is not None
    ]

    if not timestamps:
        return pd.DataFrame()

    session_start = min(timestamps)

    attack_start = float(groundtruth["attack_start"])
    attack_end = float(groundtruth["attack_end"])

    labels = []
    overlaps = []

    for window_id in features["window_id"]:
        window_start = session_start + int(window_id) * window_seconds
        window_end = window_start + window_seconds

        overlap_start = max(window_start, attack_start)
        overlap_end = min(window_end, attack_end)
        overlap = max(0.0, overlap_end - overlap_start)

        labels.append(int(overlap > 0))
        overlaps.append(round(overlap, 3))

    out = features.copy()
    out["label"] = labels
    out["attack_overlap_s"] = overlaps
    out["groundtruth"] = True

    return out


def main():
    input_root = Path("data/raw")
    output_path = Path(
        "data/processed/dataset_groundtruth.csv"
    )

    frames = []

    # ----------------------------
    # Benign data
    # ----------------------------
    benign_dir = input_root / "benign"

    for path in sorted(benign_dir.glob("*.jsonl")):
        events = read_jsonl(path)

        feats = build_from_file(
            path,
            0,
            path.stem,
            WINDOW_SECONDS,
        )

        if feats.empty:
            continue

        feats["groundtruth"] = True
        feats["attack_overlap_s"] = 0.0

        frames.append(feats)

    # ----------------------------
    # Ransomware data
    # Only use runs with explicit
    # simulator ground truth.
    # ----------------------------
    ransomware_dir = input_root / "ransomware"

    skipped = []

    for path in sorted(ransomware_dir.glob("*.jsonl")):

        session_id = path.stem

        groundtruth_path = (
            ransomware_dir
            / f"{session_id}_groundtruth.json"
        )

        groundtruth = load_groundtruth(groundtruth_path)

        if groundtruth is None:
            skipped.append(session_id)
            continue

        events = read_jsonl(path)

        feats = build_from_file(
            path,
            1,
            session_id,
            WINDOW_SECONDS,
        )

        if feats.empty:
            continue

        feats = apply_groundtruth(
            feats,
            events,
            groundtruth,
            WINDOW_SECONDS,
        )

        if not feats.empty:
            frames.append(feats)

    if not frames:
        raise SystemExit(
            "No ground-truth-compatible data found."
        )

    dataset = pd.concat(
        frames,
        ignore_index=True,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset.to_csv(
        output_path,
        index=False,
    )

    print(f"Created {output_path}")
    print(f"Rows: {len(dataset)}")
    print(
        "Class counts:",
        dataset["label"]
        .value_counts()
        .sort_index()
        .to_dict(),
    )
    print(
        "Sessions:",
        dataset["session_id"].nunique(),
    )

    print("\nSession counts:")
    print(
        dataset.groupby(
            ["session_id", "label"]
        ).size()
    )

    if skipped:
        print(
            "\nSkipped ransomware runs without "
            "explicit ground truth:"
        )
        for session in skipped:
            print(f"  - {session}")


if __name__ == "__main__":
    main()
