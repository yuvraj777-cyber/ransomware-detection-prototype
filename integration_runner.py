from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from ml.features import window_features


BASE_DIR = Path(__file__).resolve().parent
EVENT_LOG = BASE_DIR / "agent" / "events" / "events.jsonl"

BACKEND_URL = "http://127.0.0.1:8000/analyze"

# ML inference remains based on the 10-second feature window.
WINDOW_SECONDS = 10

# Metadata uses a slightly wider window so short filesystem bursts
# are less likely to be missed between polling cycles.
METADATA_LOOKBACK_SECONDS = 30

POLL_INTERVAL = 10


def read_recent_events(seconds: int) -> list[dict]:
    """Read valid events from the last `seconds` seconds."""
    if not EVENT_LOG.exists():
        return []

    cutoff = time.time() - seconds
    events = []

    try:
        with EVENT_LOG.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                try:
                    timestamp = float(event.get("timestamp", 0))
                except (TypeError, ValueError):
                    continue

                if timestamp >= cutoff:
                    events.append(event)

    except OSError as exc:
        print(f"[RUNNER] Could not read event log: {exc}")
        return []

    return events


def send_to_backend(feature_row: dict):
    payload = json.dumps(feature_row).encode("utf-8")

    request = urllib.request.Request(
        BACKEND_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body)

        print(
            f"[RUNNER] Risk={result.get('risk_level')} | "
            f"Probability={result.get('probability')} | "
            f"Indicators={len(result.get('main_contributing_indicators', []))} | "
            f"Files={result.get('files_observed', 0)} | "
            f"FS events={result.get('filesystem_events', 0)}"
        )

    except urllib.error.URLError as exc:
        print(f"[RUNNER] Backend unavailable: {exc}")

    except (json.JSONDecodeError, OSError) as exc:
        print(f"[RUNNER] Backend response error: {exc}")


def extract_file_metadata(events: list[dict]) -> dict:
    """Calculate security/file statistics independently of ML inference."""

    filesystem_events = [
        event
        for event in events
        if event.get("category") == "filesystem"
    ]

    paths = set()

    suspicious_paths = set()

    suspicious_extensions = (
        ".locked",
        ".lock",
        ".encrypted",
        ".enc",
        ".crypt",
        ".crypto",
        ".ransom",
        ".wncry",
        ".zepto",
    )

    for event in filesystem_events:

        for key in ("path", "src_path", "dest_path"):
            value = event.get(key)

            if value:
                path = str(value)
                paths.add(path)

                lower_path = path.lower()

                if any(
                    lower_path.endswith(ext)
                    for ext in suspicious_extensions
                ):
                    suspicious_paths.add(path)

    modified = sum(
        1
        for event in filesystem_events
        if event.get("event_type") == "modified"
    )

    created = sum(
        1
        for event in filesystem_events
        if event.get("event_type") == "created"
    )

    deleted = sum(
        1
        for event in filesystem_events
        if event.get("event_type") == "deleted"
    )

    renamed = sum(
        1
        for event in filesystem_events
        if event.get("event_type") == "renamed"
    )

    return {
        "files_observed": len(paths),
        "suspicious_files": len(suspicious_paths),
        "filesystem_events": len(filesystem_events),
        "files_modified": modified,
        "files_created": created,
        "files_deleted": deleted,
        "files_renamed": renamed,
    }


def run_once():
    # 10-second window for the trained ML model.
    ml_events = read_recent_events(WINDOW_SECONDS)

    if not ml_events:
        print("[RUNNER] No recent agent events.")
        return

    features = window_features(
        ml_events,
        window_seconds=WINDOW_SECONDS,
    )

    if features.empty:
        print("[RUNNER] Feature extraction returned no data.")
        return

    row = features.iloc[-1].to_dict()

    # Wider lookback for dashboard/security statistics.
    metadata_events = read_recent_events(
        METADATA_LOOKBACK_SECONDS
    )

    metadata = extract_file_metadata(metadata_events)

    row.update(metadata)

    row["events_observed"] = len(metadata_events)

    print(
        f"[RUNNER] Events={len(metadata_events)} | "
        f"Files observed={metadata['files_observed']} | "
        f"FS events={metadata['filesystem_events']} | "
        f"Suspicious files={metadata['suspicious_files']}"
    )

    send_to_backend(row)


def main():
    print("=" * 60)
    print(" LIVE RANSOMWARE INFERENCE RUNNER")
    print("=" * 60)
    print(f"Event log        : {EVENT_LOG}")
    print(f"Backend          : {BACKEND_URL}")
    print(f"ML window        : {WINDOW_SECONDS}s")
    print(f"Metadata lookback: {METADATA_LOOKBACK_SECONDS}s")
    print(f"Interval         : {POLL_INTERVAL}s")
    print("-" * 60)

    while True:
        run_once()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()