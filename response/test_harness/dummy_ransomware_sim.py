import os
import time
import random
import string

TEST_DIR = "../../agent/test_folder"


def random_name(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n))


def simulate():
    os.makedirs(TEST_DIR, exist_ok=True)

    # create some dummy files
    for i in range(30):
        with open(os.path.join(TEST_DIR, f"file_{i}.txt"), "w") as f:
            f.write("sample content")
        time.sleep(1)

    # rapidly modify and rename dummy files
    for i in range(30):
        old_path = os.path.join(TEST_DIR, f"file_{i}.txt")
        new_path = os.path.join(TEST_DIR, f"{random_name()}.locked")

        with open(old_path, "a") as f:
            f.write("MODIFIED_CONTENT")

        os.rename(old_path, new_path)


if __name__ == "__main__":
    simulate()