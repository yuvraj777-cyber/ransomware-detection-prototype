import argparse
import json
import random
import string
import time
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parents[2] / "agent" / "test_folder"
GROUNDTRUTH_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ransomware"

EXTENSIONS = [
    ".locked",
    ".encrypted",
    ".enc",
    ".crypt",
]


def random_name(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


def simulate(run_id: str):
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    GROUNDTRUTH_DIR.mkdir(parents=True, exist_ok=True)

    file_count = random.choice([30, 40, 50])
    extension = random.choice(EXTENSIONS)
    create_delay = random.choice([1.0, 1.5, 2.0])
    group_size = random.choice([4, 5])
    group_pause = random.choice([8, 10, 12])

    print(
        f"Controlled test: {file_count} files, "
        f"extension={extension}, run_id={run_id}",
        flush=True,
    )

    files = []

    # -------------------------------------------------
    # Phase 1: Controlled preparation
    # -------------------------------------------------
    for i in range(file_count):
        path = TEST_DIR / f"{run_id}_{i}.txt"

        path.write_text(
            "SAFE CONTROLLED TEST DATA\n"
            + "".join(random.choices(string.ascii_letters, k=200))
        )

        files.append(path)
        time.sleep(create_delay)

    # Short pause before the simulated attack.
    time.sleep(random.choice([2, 4, 6]))

    # -------------------------------------------------
    # Phase 2: Controlled ransomware-like activity
    # Ground truth begins here.
    # -------------------------------------------------
    attack_start = time.time()

    for start in range(0, len(files), group_size):
        group = files[start:start + group_size]

        for path in group:
            if not path.exists():
                continue

            path.write_text(
                path.read_text()
                + "\nCONTROLLED_TEST_MODIFICATION\n"
            )

            new_path = TEST_DIR / f"{random_name()}{extension}"
            path.rename(new_path)

        time.sleep(group_pause)

    attack_end = time.time()

    # -------------------------------------------------
    # Ground-truth metadata
    # -------------------------------------------------
    groundtruth = {
        "session_id": run_id,
        "label": 1,
        "attack_start": attack_start,
        "attack_end": attack_end,
        "file_count": file_count,
        "extension": extension,
        "test_directory": str(TEST_DIR.resolve()),
    }

    output = GROUNDTRUTH_DIR / f"{run_id}_groundtruth.json"
    output.write_text(json.dumps(groundtruth, indent=2))

    print(f"ATTACK_START: {attack_start}", flush=True)
    print(f"ATTACK_END: {attack_end}", flush=True)
    print(f"Ground truth saved: {output}", flush=True)
    print(
        "Controlled ransomware-like simulation complete. "
        "Only dummy files in agent/test_folder were modified/renamed.",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique session ID, e.g. ransomware_run_06",
    )
    args = parser.parse_args()

    simulate(args.run_id)


if __name__ == "__main__":
    main()
