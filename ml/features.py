from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd

SYSTEM_COLS = [
    "cpu_percent", "memory_percent", "disk_read_bytes",
    "disk_write_bytes", "process_count"
]

def read_jsonl(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} line {line_no}: {exc}") from exc
    return out

def _safe_rate(value: float, seconds: float) -> float:
    return float(value) / max(seconds, 1e-6)

def window_features(events: list[dict], window_seconds: int = 10) -> pd.DataFrame:
    if not events:
        return pd.DataFrame()

    rows = []
    for e in events:
        ts = float(e.get("timestamp", 0))
        if ts > 1e12:  # tolerate milliseconds
            ts /= 1000.0
        rows.append({**e, "_ts": ts})

    df = pd.DataFrame(rows).sort_values("_ts")
    start = float(df["_ts"].min())
    df["window"] = ((df["_ts"] - start) // window_seconds).astype(int)

    records = []
    for win, g in df.groupby("window", sort=True):
        span = max(float(g["_ts"].max() - g["_ts"].min()), float(window_seconds))
        system = g[g["category"].eq("system")]
        process = g[g["category"].eq("process")]
        fs = g[g["category"].eq("filesystem")]

        names = process.get("name", pd.Series(dtype=str)).fillna("").astype(str)
        suspicious_names = names.str.lower().str.contains(
            r"(encrypt|crypt|ransom|locker|vssadmin|wbadmin|cipher|powershell)",
            regex=True, na=False
        )

        rec = {
            "window_id": int(win),
            "duration_s": span,
            "total_events": len(g),
            "system_events": len(system),
            "process_events": len(process),
            "filesystem_events": len(fs),
            "process_create_rate": _safe_rate(len(process), span),
            "filesystem_event_rate": _safe_rate(len(fs), span),
            "suspicious_process_events": int(suspicious_names.sum()),
            "unique_process_names": int(names[names.ne("")].nunique()),
            "process_burst": int(len(process) >= 5),
        }

        for c in SYSTEM_COLS:
            vals = pd.to_numeric(system.get(c, pd.Series(dtype=float)), errors="coerce").dropna()
            rec[f"{c}_mean"] = float(vals.mean()) if len(vals) else 0.0
            rec[f"{c}_max"] = float(vals.max()) if len(vals) else 0.0
            rec[f"{c}_std"] = float(vals.std(ddof=0)) if len(vals) else 0.0

        rec["disk_write_rate"] = _safe_rate(
            float(system.get("disk_write_bytes", pd.Series(dtype=float)).fillna(0).sum()), span
        )
        rec["disk_read_rate"] = _safe_rate(
            float(system.get("disk_read_bytes", pd.Series(dtype=float)).fillna(0).sum()), span
        )
        rec["write_read_ratio"] = (
            rec["disk_write_rate"] / max(rec["disk_read_rate"], 1.0)
        )

        # Filesystem event-type counts.
        for event_name in ["created", "modified", "deleted", "renamed"]:
            rec[f"fs_{event_name}"] = int(
                fs.get("event_type", pd.Series(dtype=str)).astype(str).eq(event_name).sum()
            )

        # Label is assigned by the parent directory in build_dataset.py.
        records.append(rec)

    return pd.DataFrame(records)

def build_from_file(path: Path, label: int, session_id: str, window_seconds: int) -> pd.DataFrame:
    feats = window_features(read_jsonl(path), window_seconds)
    if feats.empty:
        return feats
    feats["label"] = int(label)
    feats["session_id"] = session_id
    feats["source_file"] = path.name
    return feats
