#!/usr/bin/env python3
import subprocess
import sys

steps = [
    ["python3", "fetch_metadata.py"],
    ["python3", "build_dataset_v2.py"],
]

for step in steps:
    print(f"Running: {' '.join(step)}")
    result = subprocess.run(step)
    if result.returncode != 0:
        sys.exit(result.returncode)

print("Dataset refresh complete.")
