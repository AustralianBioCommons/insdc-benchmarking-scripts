#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

DEFAULT_DATASET = Path("scripts/data/deterministic_datasets_v2.csv")
DEFAULT_RESULTS_FILE = Path("data/benchmark_results.csv")


def load_rows(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open(newline="") as f:
        return list(csv.DictReader(f))


def should_include_row(row: dict[str, str], args: argparse.Namespace) -> bool:
    if args.status and row["STATUS"] != args.status:
        return False
    if args.category and row["CATEGORY"] not in args.category:
        return False
    if args.run_accession and row["RUN_ACCESSION"] not in args.run_accession:
        return False
    return True


def build_http_command(
    dataset_id: str, dataset_file: Path, args: argparse.Namespace
) -> list[str]:
    cmd = [
        "poetry",
        "run",
        "benchmark-http",
        "--dataset",
        dataset_id,
        "--repository",
        args.repository,
        "--site",
        args.site,
        "--repeats",
        str(args.repeats),
        "--timeout",
        str(args.timeout),
        "--deterministic-dataset-file",
        str(dataset_file),
        "--no-submit",
    ]

    if args.repository.upper() == "SRA":
        cmd.extend(["--sra-mode", args.sra_mode, "--mirror", args.mirror])
        if args.require_mirror:
            cmd.append("--require-mirror")
        if args.explain:
            cmd.append("--explain")

    return cmd


def build_ftp_command(
    dataset_id: str, dataset_file: Path, args: argparse.Namespace
) -> list[str]:
    return [
        "poetry",
        "run",
        "benchmark-ftp",
        "--dataset",
        dataset_id,
        "--repository",
        args.repository,
        "--site",
        args.site,
        "--repeats",
        str(args.repeats),
        "--timeout",
        str(args.timeout),
        "--ftp-timeout",
        str(args.ftp_timeout),
        "--deterministic-dataset-file",
        str(dataset_file),
        "--no-submit",
    ]


ProtocolBuilder = Callable[[str, Path, argparse.Namespace], list[str]]

PROTOCOLS: dict[str, ProtocolBuilder] = {
    "wget": build_http_command,
    "ftp": build_ftp_command,
    # future:
    # "globus": build_globus_command,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run protocol benchmarks across deterministic dataset runs"
    )
    parser.add_argument(
        "--dataset-file",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to deterministic_datasets_v2.csv",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="CSV file for aggregated benchmark results",
    )
    parser.add_argument(
        "--protocol",
        action="append",
        choices=sorted(PROTOCOLS.keys()),
        help="Protocol(s) to benchmark. Can be passed multiple times. Default: all registered protocols",
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
        "--status",
        default="ACTIVE",
        help="Status to include. Default: ACTIVE",
    )
    parser.add_argument(
        "--limit-runs",
        type=int,
        help="Maximum number of runs to process after filtering",
    )
    parser.add_argument(
        "--site",
        default="nci",
        help="Site identifier passed through to benchmark scripts",
    )
    parser.add_argument(
        "--repository",
        default="ENA",
        help="Repository passed through to benchmark scripts",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Resolver timeout passed through to benchmark scripts",
    )
    parser.add_argument(
        "--ftp-timeout",
        type=int,
        default=30,
        help="FTP timeout passed to benchmark-ftp",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Repeat count passed through to benchmark scripts",
    )
    parser.add_argument(
        "--sra-mode",
        default="sra_cloud",
        help="SRA mode passed to benchmark-http when repository=SRA",
    )
    parser.add_argument(
        "--mirror",
        default="auto",
        help="Mirror passed to benchmark-http when repository=SRA",
    )
    parser.add_argument(
        "--require-mirror",
        action="store_true",
        help="Pass --require-mirror to benchmark-http",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Pass --explain to benchmark-http",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing them",
    )
    return parser.parse_args()


def extract_result_json(stdout: str) -> dict[str, Any] | None:
    marker = "🧾 Result (schema v1.2 fields subset):"
    marker_index = stdout.find(marker)
    if marker_index == -1:
        return None

    after_marker = stdout[marker_index + len(marker) :].strip()
    start = after_marker.find("{")
    if start == -1:
        return None

    json_candidate = after_marker[start:]
    decoder = json.JSONDecoder()

    try:
        obj, _ = decoder.raw_decode(json_candidate)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        return None

    return None


def append_result(results_file: Path, row: dict[str, object]) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    file_exists = results_file.exists()

    with results_file.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_accession",
                "category",
                "protocol",
                "repository",
                "site",
                "status",
                "duration_sec",
                "file_size_bytes",
                "average_speed_mbps",
                "checksum_md5",
                "timestamp",
                "notes",
                "error_message",
                "command",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_command(
    protocol: str,
    dataset_id: str,
    dataset_file: Path,
    args: argparse.Namespace,
) -> list[str]:
    builder = PROTOCOLS.get(protocol)
    if builder is None:
        raise ValueError(f"Unsupported protocol: {protocol}")
    return builder(dataset_id, dataset_file, args)


def main() -> int:
    args = parse_args()

    if not args.dataset_file.exists():
        raise SystemExit(f"Dataset file not found: {args.dataset_file}")

    protocols = args.protocol or list(PROTOCOLS.keys())

    rows = load_rows(args.dataset_file)
    rows = [row for row in rows if should_include_row(row, args)]

    if args.limit_runs is not None:
        rows = rows[: args.limit_runs]

    total_jobs = 0
    success = 0
    failures = 0
    skipped_runs = 0

    for row in rows:
        run_id = row["RUN_ACCESSION"]
        category = row["CATEGORY"]
        status = row["STATUS"]

        if status != "ACTIVE":
            skipped_runs += 1
            print(f"Skipping {run_id}: status={status}")
            continue

        for protocol in protocols:
            total_jobs += 1
            cmd = build_command(protocol, run_id, args.dataset_file, args)

            if args.dry_run:
                print("[DRY RUN]", " ".join(cmd))
                append_result(
                    args.results_file,
                    {
                        "run_accession": run_id,
                        "category": category,
                        "protocol": protocol,
                        "repository": args.repository,
                        "site": args.site,
                        "status": "DRY_RUN",
                        "duration_sec": "",
                        "file_size_bytes": "",
                        "average_speed_mbps": "",
                        "checksum_md5": "",
                        "timestamp": "",
                        "notes": "",
                        "error_message": "",
                        "command": " ".join(cmd),
                    },
                )
                continue

            print(f"\nRunning {protocol.upper()} benchmark for {run_id} ({category})")
            print("Command:", " ".join(cmd))

            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            result_json = extract_result_json(completed.stdout)
            combined_error = completed.stderr.strip() or ""

            if completed.returncode == 0 and result_json:
                row_out = {
                    "run_accession": run_id,
                    "category": category,
                    "protocol": protocol,
                    "repository": result_json.get("repository", args.repository),
                    "site": result_json.get("site", args.site),
                    "status": result_json.get("status", "unknown"),
                    "duration_sec": result_json.get("duration_sec", ""),
                    "file_size_bytes": result_json.get("file_size_bytes", ""),
                    "average_speed_mbps": result_json.get("average_speed_mbps", ""),
                    "checksum_md5": result_json.get("checksum_md5", ""),
                    "timestamp": result_json.get("timestamp", ""),
                    "notes": result_json.get("notes", ""),
                    "error_message": result_json.get("error_message", combined_error),
                    "command": " ".join(cmd),
                }
                append_result(args.results_file, row_out)

                if result_json.get("status") == "success":
                    success += 1
                    print("  OK")
                else:
                    failures += 1
                    print("  FAIL")
            else:
                failures += 1
                error_text = combined_error or completed.stdout[-1000:]

                append_result(
                    args.results_file,
                    {
                        "run_accession": run_id,
                        "category": category,
                        "protocol": protocol,
                        "repository": args.repository,
                        "site": args.site,
                        "status": "runner_fail",
                        "duration_sec": "",
                        "file_size_bytes": "",
                        "average_speed_mbps": "",
                        "checksum_md5": "",
                        "timestamp": "",
                        "notes": "",
                        "error_message": error_text,
                        "command": " ".join(cmd),
                    },
                )
                print("  FAIL")
                if error_text:
                    print(error_text)

    print("\nSummary")
    print(f"  Total jobs:   {total_jobs}")
    print(f"  Success:      {success}")
    print(f"  Failures:     {failures}")
    print(f"  Skipped runs: {skipped_runs}")
    print(f"  Results file: {args.results_file}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
