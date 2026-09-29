from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


SYSTEM_COLS = [
    "cpu_percent",
    "memory_percent",
    "disk_read_bytes",
    "disk_write_bytes",
    "process_count",
]

SUSPICIOUS_EXTENSIONS = {
    ".locked",
    ".lock",
    ".encrypted",
    ".enc",
    ".crypt",
    ".crypto",
    ".ransom",
    ".wncry",
    ".zepto",
}


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
                raise ValueError(
                    f"Invalid JSON in {path} line {line_no}: {exc}"
                ) from exc

    return out


def _safe_rate(value: float, seconds: float) -> float:
    return float(value) / max(seconds, 1e-6)


def _extension(path_value: str) -> str:
    if not path_value:
        return ""

    return Path(str(path_value)).suffix.lower()


def _directory(path_value: str) -> str:
    if not path_value:
        return ""

    return str(Path(str(path_value)).parent)


def _burst_count(timestamps: np.ndarray, interval: float) -> int:
    if len(timestamps) == 0:
        return 0

    ts = np.sort(timestamps)
    right = np.searchsorted(ts, ts + interval, side="right")
    counts = right - np.arange(len(ts))

    return int(counts.max())


def window_features(
    events: list[dict],
    window_seconds: int = 10,
) -> pd.DataFrame:

    if not events:
        return pd.DataFrame()

    rows = []

    for e in events:
        ts = float(e.get("timestamp", 0))

        if ts > 1e12:
            ts /= 1000.0

        rows.append({**e, "_ts": ts})

    df = pd.DataFrame(rows).sort_values("_ts")

    start = float(df["_ts"].min())
    df["window"] = (
        (df["_ts"] - start) // window_seconds
    ).astype(int)

    records = []

    for win, g in df.groupby("window", sort=True):

        span = max(
            float(g["_ts"].max() - g["_ts"].min()),
            float(window_seconds),
        )

        system = g[g["category"].eq("system")]
        process = g[g["category"].eq("process")]
        fs = g[g["category"].eq("filesystem")]

        # ----------------------------
        # Process behavior
        # ----------------------------
        names = (
            process.get("name", pd.Series(dtype=str))
            .fillna("")
            .astype(str)
        )

        suspicious_names = names.str.lower().str.contains(
            r"(encrypt|crypt|ransom|locker|vssadmin|wbadmin|cipher|powershell)",
            regex=True,
            na=False,
        )

        # ----------------------------
        # Filesystem behavior
        # ----------------------------
        event_types = (
            fs.get("event_type", pd.Series(dtype=str))
            .fillna("")
            .astype(str)
            .str.lower()
        )

        fs_created = int((event_types == "created").sum())
        fs_modified = int((event_types == "modified").sum())
        fs_deleted = int((event_types == "deleted").sum())
        fs_renamed = int((event_types == "renamed").sum())

        fs_timestamps = pd.to_numeric(
            fs.get("_ts", pd.Series(dtype=float)),
            errors="coerce",
        ).dropna().to_numpy()

        rename_timestamps = pd.to_numeric(
            fs.loc[event_types == "renamed", "_ts"]
            if "_ts" in fs.columns
            else pd.Series(dtype=float),
            errors="coerce",
        ).dropna().to_numpy()

        # Collect paths from filesystem events.
        path_values = []

        for _, row in fs.iterrows():
            for key in ("path", "src_path", "dest_path"):
                value = row.get(key)

                if pd.notna(value) and str(value):
                    path_values.append(str(value))

        extensions = {
            ext
            for value in path_values
            for ext in [_extension(value)]
            if ext
        }

        directories = {
            directory
            for value in path_values
            for directory in [_directory(value)]
            if directory
        }

        suspicious_extension_events = 0
        extension_change_events = 0

        for _, row in fs.iterrows():

            path_ext = _extension(str(row.get("path", "")))
            dest_ext = _extension(str(row.get("dest_path", "")))
            src_ext = _extension(str(row.get("src_path", "")))

            for ext in (path_ext, dest_ext, src_ext):
                if ext in SUSPICIOUS_EXTENSIONS:
                    suspicious_extension_events += 1

            if (
                row.get("event_type") == "renamed"
                and src_ext
                and dest_ext
                and src_ext != dest_ext
            ):
                extension_change_events += 1

        # ----------------------------
        # Feature record
        # ----------------------------
        rec = {
            "window_id": int(win),
            "duration_s": span,

            # General counts
            "total_events": len(g),
            "system_events": len(system),
            "process_events": len(process),
            "filesystem_events": len(fs),

            # Rates
            "process_create_rate": _safe_rate(len(process), span),
            "filesystem_event_rate": _safe_rate(len(fs), span),
            "create_rate": _safe_rate(fs_created, span),
            "modify_rate": _safe_rate(fs_modified, span),
            "delete_rate": _safe_rate(fs_deleted, span),
            "rename_rate": _safe_rate(fs_renamed, span),

            # Process indicators
            "suspicious_process_events": int(suspicious_names.sum()),
            "unique_process_names": int(
                names[names.ne("")].nunique()
            ),
            "process_burst": int(len(process) >= 5),

            # Filesystem counts
            "fs_created": fs_created,
            "fs_modified": fs_modified,
            "fs_deleted": fs_deleted,
            "fs_renamed": fs_renamed,

            # Behavioral ratios
            "rename_ratio": (
                fs_renamed / max(len(fs), 1)
            ),
            "modify_ratio": (
                fs_modified / max(len(fs), 1)
            ),
            "create_ratio": (
                fs_created / max(len(fs), 1)
            ),
            "delete_ratio": (
                fs_deleted / max(len(fs), 1)
            ),
            "rename_to_modify_ratio": (
                fs_renamed / max(fs_modified, 1)
            ),

            # Path / extension behavior
            "unique_extensions": len(extensions),
            "unique_directories": len(directories),
            "extension_change_events": extension_change_events,
            "suspicious_extension_events": suspicious_extension_events,

            # Burst behavior
            "max_fs_events_1s": _burst_count(
                fs_timestamps,
                1.0,
            ),
            "max_rename_events_1s": _burst_count(
                rename_timestamps,
                1.0,
            ),
            "filesystem_burst": int(len(fs) >= 10),
        }

        # ----------------------------
        # System statistics
        # ----------------------------
        for c in SYSTEM_COLS:

            vals = pd.to_numeric(
                system.get(c, pd.Series(dtype=float)),
                errors="coerce",
            ).dropna()

            rec[f"{c}_mean"] = (
                float(vals.mean()) if len(vals) else 0.0
            )

            rec[f"{c}_max"] = (
                float(vals.max()) if len(vals) else 0.0
            )

            rec[f"{c}_std"] = (
                float(vals.std(ddof=0)) if len(vals) else 0.0
            )

        # Disk activity
        disk_write = float(
            system.get(
                "disk_write_bytes",
                pd.Series(dtype=float),
            )
            .fillna(0)
            .sum()
        )

        disk_read = float(
            system.get(
                "disk_read_bytes",
                pd.Series(dtype=float),
            )
            .fillna(0)
            .sum()
        )

        rec["disk_write_rate"] = _safe_rate(
            disk_write,
            span,
        )

        rec["disk_read_rate"] = _safe_rate(
            disk_read,
            span,
        )

        rec["write_read_ratio"] = (
            rec["disk_write_rate"]
            / max(rec["disk_read_rate"], 1.0)
        )

        records.append(rec)

    return pd.DataFrame(records)


def build_from_file(
    path: Path,
    label: int,
    session_id: str,
    window_seconds: int,
) -> pd.DataFrame:

    feats = window_features(
        read_jsonl(path),
        window_seconds,
    )

    if feats.empty:
        return feats

    feats["label"] = int(label)
    feats["session_id"] = session_id
    feats["source_file"] = path.name

    return feats
