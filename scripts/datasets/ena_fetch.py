import time
from typing import Dict, List

import requests

ENA_BASE = "https://www.ebi.ac.uk/ena/portal/api/search"

BATCH_SIZE = 100
MAX_RETRIES = 3
SLEEP_BETWEEN_BATCHES = 0.2


def batch_list(items: List[str], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def build_query(run_ids: List[str]) -> str:
    # Example:
    # run_accession="ERR1" OR run_accession="ERR2"
    return " OR ".join(f'run_accession="{run_id}"' for run_id in run_ids)


def parse_tsv(text: str) -> Dict[str, Dict[str, str]]:
    lines = text.strip().splitlines()
    if not lines:
        return {}

    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}

    required = {"run_accession", "fastq_md5", "fastq_ftp"}
    missing = required - set(idx)
    if missing:
        preview = "\n".join(lines[:10])
        raise ValueError(
            f"ENA response missing expected columns {sorted(missing)}.\n"
            f"Header was: {header}\n\n"
            f"Response preview:\n{preview}"
        )

    results: Dict[str, Dict[str, str]] = {}

    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) <= idx["run_accession"]:
            continue

        run_accession = cols[idx["run_accession"]].strip()
        if not run_accession:
            continue

        results[run_accession] = {
            "fastq_md5": cols[idx["fastq_md5"]].strip()
            if idx["fastq_md5"] < len(cols)
            else "",
            "fastq_ftp": cols[idx["fastq_ftp"]].strip()
            if idx["fastq_ftp"] < len(cols)
            else "",
        }

    return results


def fetch_batch(run_ids: List[str]) -> Dict[str, Dict[str, str]]:
    params = {
        "result": "read_run",
        "query": build_query(run_ids),
        "fields": "run_accession,fastq_md5,fastq_ftp",
        "format": "tsv",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(ENA_BASE, params=params, timeout=120)
            resp.raise_for_status()
            return parse_tsv(resp.text)
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Failed to fetch ENA batch after retries")


def fetch_all(run_ids: List[str]) -> Dict[str, Dict[str, str]]:
    all_results: Dict[str, Dict[str, str]] = {}

    for batch in batch_list(run_ids, BATCH_SIZE):
        print(f"Fetching batch of {len(batch)} runs...")
        batch_result = fetch_batch(batch)
        all_results.update(batch_result)
        time.sleep(SLEEP_BETWEEN_BATCHES)

    return all_results
