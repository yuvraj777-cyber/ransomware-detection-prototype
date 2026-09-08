import json
import os
import platform
import threading
import time
from pathlib import Path
from typing import Set

import psutil
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
TEST_FOLDER = BASE_DIR / "test_folder"
EVENT_DIR = BASE_DIR / "events"
EVENT_LOG = EVENT_DIR / "events.jsonl"

SYSTEM_POLL_INTERVAL = 2  # seconds


# ============================================================
# INITIAL SETUP
# ============================================================

TEST_FOLDER.mkdir(parents=True, exist_ok=True)
EVENT_DIR.mkdir(parents=True, exist_ok=True)


def write_event(record: dict) -> None:
    """
    Write one JSON event per line.
    This JSONL format becomes the stable interface
    for the next module.
    """
    record["timestamp"] = time.time()

    try:
        with EVENT_LOG.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[ERROR] Could not write event: {exc}")


# ============================================================
# FILE SYSTEM MONITOR
# ============================================================

class FileSystemMonitor(FileSystemEventHandler):
    """
    Monitors create/modify/delete/rename events
    inside the designated test folder.
    """

    def on_created(self, event):
        if event.is_directory:
            return

        write_event({
            "category": "filesystem",
            "event_type": "created",
            "path": os.path.abspath(event.src_path)
        })

    def on_modified(self, event):
        if event.is_directory:
            return

        write_event({
            "category": "filesystem",
            "event_type": "modified",
            "path": os.path.abspath(event.src_path)
        })

    def on_deleted(self, event):
        if event.is_directory:
            return

        write_event({
            "category": "filesystem",
            "event_type": "deleted",
            "path": os.path.abspath(event.src_path)
        })

    def on_moved(self, event):
        if event.is_directory:
            return

        write_event({
            "category": "filesystem",
            "event_type": "renamed",
            "src_path": os.path.abspath(event.src_path),
            "dest_path": os.path.abspath(event.dest_path)
        })


def run_filesystem_monitor() -> None:
    observer = Observer()
    handler = FileSystemMonitor()

    observer.schedule(
        handler,
        str(TEST_FOLDER),
        recursive=True
    )

    observer.start()

    print(f"[FILE] Monitoring: {TEST_FOLDER}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# ============================================================
# PROCESS MONITOR
# ============================================================

def get_process_snapshot() -> Set[int]:
    """
    Return currently running process IDs.
    """
    try:
        return set(psutil.pids())
    except psutil.Error:
        return set()


def monitor_processes() -> None:
    """
    Detect newly started processes.
    """
    previous_pids = get_process_snapshot()

    while True:
        time.sleep(SYSTEM_POLL_INTERVAL)

        current_pids = get_process_snapshot()
        new_pids = current_pids - previous_pids

        for pid in new_pids:
            try:
                process = psutil.Process(pid)

                write_event({
                    "category": "process",
                    "event_type": "created",
                    "pid": pid,
                    "name": process.name(),
                    "parent_pid": process.ppid()
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):
                pass

        previous_pids = current_pids


# ============================================================
# SYSTEM MONITOR
# ============================================================

def monitor_system() -> None:
    """
    Periodically records basic system telemetry.
    """
    previous_disk = None

    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory_percent = psutil.virtual_memory().percent

            disk = psutil.disk_io_counters()

            disk_read = disk.read_bytes if disk else 0
            disk_write = disk.write_bytes if disk else 0

            if previous_disk:
                read_delta = max(0, disk_read - previous_disk[0])
                write_delta = max(0, disk_write - previous_disk[1])
            else:
                read_delta = 0
                write_delta = 0

            previous_disk = (disk_read, disk_write)

            write_event({
                "category": "system",
                "event_type": "snapshot",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_read_bytes": read_delta,
                "disk_write_bytes": write_delta,
                "process_count": len(psutil.pids()),
                "platform": platform.system()
            })

        except psutil.Error as exc:
            print(f"[WARNING] System monitoring error: {exc}")

        time.sleep(SYSTEM_POLL_INTERVAL)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("==========================================")
    print(" AI RANSOMWARE MONITORING AGENT")
    print("==========================================")
    print(f"Platform : {platform.system()}")
    print(f"Python   : {platform.python_version()}")
    print(f"Watching : {TEST_FOLDER}")
    print(f"Logging  : {EVENT_LOG}")
    print("------------------------------------------")

    filesystem_thread = threading.Thread(
        target=run_filesystem_monitor,
        daemon=True
    )

    process_thread = threading.Thread(
        target=monitor_processes,
        daemon=True
    )

    system_thread = threading.Thread(
        target=monitor_system,
        daemon=True
    )

    filesystem_thread.start()
    process_thread.start()
    system_thread.start()

    print("[AGENT] Monitoring started.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[AGENT] Monitoring stopped.")


if __name__ == "__main__":
    main()