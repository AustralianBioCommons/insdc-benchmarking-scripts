from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Optional


class DeterministicDatasetError(ValueError):
    pass


def load_run_record(
    dataset_file: str | Path, run_accession: str
) -> Optional[dict[str, Any]]:
    path = Path(dataset_file)

    if not path.exists():
        raise FileNotFoundError(f"Deterministic dataset file not found: {path}")

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("RUN_ACCESSION") or "").strip() != run_accession.strip():
                continue

            md5_list = json.loads(row.get("FASTQ_MD5_LIST", "[]"))
            url_list = json.loads(row.get("FASTQ_URL_LIST", "[]"))

            if not isinstance(md5_list, list) or not isinstance(url_list, list):
                raise DeterministicDatasetError(
                    f"Invalid JSON list fields for run {run_accession}"
                )

            return {
                "category": (row.get("CATEGORY") or "").strip(),
                "run_accession": (row.get("RUN_ACCESSION") or "").strip(),
                "status": (row.get("STATUS") or "").strip(),
                "fastq_md5_list": md5_list,
                "fastq_url_list": url_list,
            }

    return None
