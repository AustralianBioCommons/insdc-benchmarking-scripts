#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from urllib.request import urlretrieve


DATASET = Path("data/deterministic_datasets_v2.csv")
DEFAULT_DOWNLOAD_DIR = Path("data/downloads")
DEFAULT_RESULTS_FILE = Path("data/benchmark_results.csv")


def compute_md5(filepath: Path) -> str:
    hash_md5 = hashlib.md5()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_file(url: str, dest: Path) -> None:
    ftp_url = (
        url if url.startswith(("ftp://", "http://", "https://")) else f"ftp://{url}"
    )
    urlretrieve(ftp_url, dest)


def load_rows(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def append_result(results_file: Path, row: dict[str, object]) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    file_exists = results_file.exists()

    with results_file.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "category",
                "run_accession",
                "file_index",
                "file_name",
                "status",
                "download_url",
                "expected_md5",
                "actual_md5",
                "download_seconds",
                "bytes_on_disk",
                "error",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run benchmark downloads from deterministic_datasets_v2.csv"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET,
        help="Path to deterministic dataset CSV",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=DEFAULT_DOWNLOAD_DIR,
        help="Directory for downloaded files",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="CSV file for benchmark results",
    )
    parser.add_argument(
        "--category",
        action="append",
        help="Category to include. Can be passed multiple times.",
    )
    parser.add_argument(
        "--run-accession",
        action="append",
        help="Specific run accession to include. Can be passed multiple times.",
    )
    parser.add_argument(
        "--status", default="ACTIVE", help="Status to include. Default: ACTIVE"
    )
    parser.add_argument(
        "--limit-runs",
        type=int,
        help="Maximum number of runs to process after filtering",
    )
    parser.add_argument(
        "--limit-files", type=int, help="Maximum number of files to process total"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep downloaded files after checksum validation",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would run without downloading"
    )
    return parser.parse_args()


def should_include_row(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.status and row["STATUS"] != args.status:
        return False
    if args.category and row["CATEGORY"] not in args.category:
        return False
    if args.run_accession and row["RUN_ACCESSION"] not in args.run_accession:
        return False
    return True


def main() -> int:
    args = parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Dataset file not found: {args.dataset}")

    rows = load_rows(args.dataset)
    rows = [row for row in rows if should_include_row(row, args)]

    if args.limit_runs is not None:
        rows = rows[: args.limit_runs]

    args.download_dir.mkdir(parents=True, exist_ok=True)

    total_files = 0
    success = 0
    failures = 0
    skipped_runs = 0

    for row in rows:
        category = row["CATEGORY"]
        run_id = row["RUN_ACCESSION"]
        status = row["STATUS"]

        if status != "ACTIVE":
            skipped_runs += 1
            continue

        md5_list = json.loads(row["FASTQ_MD5_LIST"])
        url_list = json.loads(row["FASTQ_URL_LIST"])

        if len(md5_list) != len(url_list):
            print(f"Skipping {run_id}: MD5/URL count mismatch")
            skipped_runs += 1
            continue

        for file_index, (expected_md5, url) in enumerate(
            zip(md5_list, url_list), start=1
        ):
            if args.limit_files is not None and total_files >= args.limit_files:
                print("\nReached file limit.")
                print_summary(total_files, success, failures, skipped_runs)
                return 0

            total_files += 1
            file_name = url.split("/")[-1]
            dest = args.download_dir / file_name

            if args.dry_run:
                print(f"[DRY RUN] {category} {run_id} file {file_index}: {url}")
                append_result(
                    args.results_file,
                    {
                        "category": category,
                        "run_accession": run_id,
                        "file_index": file_index,
                        "file_name": file_name,
                        "status": "DRY_RUN",
                        "download_url": url,
                        "expected_md5": expected_md5,
                        "actual_md5": "",
                        "download_seconds": "",
                        "bytes_on_disk": "",
                        "error": "",
                    },
                )
                continue

            print(
                f"Downloading {category} | {run_id} | file {file_index}/{len(md5_list)}"
            )

            actual_md5 = ""
            elapsed: float | None = None
            bytes_on_disk: int | None = None
            error = ""
            result_status = "FAILED"

            try:
                start = time.time()
                download_file(url, dest)
                elapsed = round(time.time() - start, 3)
                actual_md5 = compute_md5(dest)
                bytes_on_disk = dest.stat().st_size

                if actual_md5 == expected_md5:
                    result_status = "OK"
                    success += 1
                    print(f"  OK in {elapsed}s")
                else:
                    result_status = "MD5_MISMATCH"
                    failures += 1
                    print("  MD5 mismatch")
            except Exception as exc:
                failures += 1
                error = str(exc)
                print(f"  Error: {error}")
            finally:
                append_result(
                    args.results_file,
                    {
                        "category": category,
                        "run_accession": run_id,
                        "file_index": file_index,
                        "file_name": file_name,
                        "status": result_status,
                        "download_url": url,
                        "expected_md5": expected_md5,
                        "actual_md5": actual_md5,
                        "download_seconds": elapsed,
                        "bytes_on_disk": bytes_on_disk,
                        "error": error,
                    },
                )
                if dest.exists() and not args.keep_files:
                    dest.unlink()

    print_summary(total_files, success, failures, skipped_runs)
    return 0


def print_summary(
    total_files: int, success: int, failures: int, skipped_runs: int
) -> None:
    print("\nSummary")
    print(f"  Total files: {total_files}")
    print(f"  Success:     {success}")
    print(f"  Failures:    {failures}")
    print(f"  Skipped:     {skipped_runs}")


if __name__ == "__main__":
    raise SystemExit(main())
