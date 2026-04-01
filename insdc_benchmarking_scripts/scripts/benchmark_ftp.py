# insdc_benchmarking_scripts/scripts/benchmark_ftp.py
"""FTP benchmarking using Python ftplib.

This CLI resolves FTP URLs for INSDC run accessions (SRR/ERR/DRR),
downloads files using ftplib, times the transfer, computes checksums,
samples system/network baselines, and prints/submits stats.

Highlights
----------
- Native Python FTP implementation (no external dependencies)
- ENA FTP support with automatic URL resolution
- Optional deterministic dataset support for pre-resolved URLs/checksums
- System metrics (CPU %, memory MB) and local write-speed baseline
- Network baseline (ping / traceroute) targeting the FTP host
- Produces JSON-compatible result matching v1.2 schema
- Optional --repeats for multiple trials with aggregate statistics
"""

from __future__ import annotations

import json
import os
import statistics
import time
from ftplib import FTP
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

import click

from insdc_benchmarking_scripts.utils import load_run_record
from insdc_benchmarking_scripts.utils.network_baseline import get_network_baseline
from insdc_benchmarking_scripts.utils.repositories import resolve_ena_fastq_urls
from insdc_benchmarking_scripts.utils.submit import submit_result
from insdc_benchmarking_scripts.utils.system_metrics import (
    SystemMonitor,
    get_baseline_metrics,
)


# --------------------------- Helpers ---------------------------


def _md5(path: Path) -> str:
    """Compute MD5 checksum using Python stdlib."""
    import hashlib

    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256(path: Path) -> str:
    """Compute SHA256 checksum using Python stdlib."""
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _pretty_mbps(bytes_count: int, seconds: float) -> float:
    """Compute average Mbps (decimal megabits)."""
    if seconds <= 0:
        return 0.0
    return (bytes_count * 8 / 1_000_000) / seconds


def _iso8601(ts_seconds: float) -> str:
    """Format a UNIX timestamp (seconds) as an ISO 8601 UTC string with Z suffix."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts_seconds))


def _convert_https_to_ftp(url: str) -> str:
    """Convert ENA URL or host/path string to a proper FTP URL."""
    url = url.strip()

    if url.startswith("ftp://"):
        return url
    if url.startswith("https://"):
        return url.replace("https://", "ftp://", 1)
    if url.startswith("http://"):
        return url.replace("http://", "ftp://", 1)

    # Handle scheme-less values like:
    # ftp.sra.ebi.ac.uk/vol1/fastq/...
    return f"ftp://{url}"


def _ftp_download(ftp_url: str, output_path: Path, timeout: int = 30) -> None:
    """Download a file via FTP using ftplib."""
    if not ftp_url.startswith("ftp://"):
        ftp_url = f"ftp://{ftp_url}"

    parsed = urlparse(ftp_url)
    host = parsed.hostname
    path = parsed.path
    port = parsed.port or 21

    if not host or not path:
        raise ValueError(f"Invalid FTP URL: {ftp_url}")

    ftp = FTP(timeout=timeout)
    ftp.connect(host, port)
    ftp.login()

    try:
        try:
            with open(output_path, "wb") as f:
                ftp.retrbinary(f"RETR {path}", f.write)
        except Exception:
            from posixpath import basename, dirname

            dirpart, filepart = dirname(path), basename(path)
            if dirpart:
                ftp.cwd(dirpart)
            with open(output_path, "wb") as f:
                ftp.retrbinary(f"RETR {filepart}", f.write)
    finally:
        try:
            ftp.quit()
        except Exception:
            pass


# ----------------------------- CLI -----------------------------


@click.command()
@click.option(
    "--dataset",
    required=True,
    help="INSDC run accession (SRR/ERR/DRR). Example: SRR000001",
)
@click.option(
    "--repository",
    type=click.Choice(["ENA", "SRA", "DDBJ"], case_sensitive=False),
    default="ENA",
    show_default=True,
    help="Source repository to benchmark.",
)
@click.option(
    "--site",
    default="nci",
    show_default=True,
    help="Short identifier for test location (e.g., nci, pawsey, qcif).",
)
@click.option(
    "--repeats",
    type=int,
    default=1,
    show_default=True,
    help="Repeat the download N times and print aggregate stats (submission uses last trial).",
)
@click.option(
    "--timeout",
    type=int,
    default=20,
    show_default=True,
    help="Resolver timeout (seconds) used when looking up URLs (e.g., ENA API).",
)
@click.option(
    "--ftp-timeout",
    type=int,
    default=30,
    show_default=True,
    help="Socket timeout (seconds) for the FTP connection.",
)
@click.option(
    "--no-submit",
    is_flag=True,
    help="Perform benchmark but skip submission step (printing only).",
)
@click.option(
    "--deterministic-dataset-file",
    default=None,
    help="Optional path to deterministic_datasets_v2.csv for pre-resolved URLs/checksums.",
)
def main(
    dataset: str,
    repository: str,
    site: str,
    repeats: int,
    timeout: int,
    ftp_timeout: int,
    no_submit: bool,
    deterministic_dataset_file: Optional[str],
) -> None:
    """Resolve FTP URL(s), download first, time transfer, sample metrics, and print/submit results."""
    print("\n" + "=" * 70)
    print("📁 INSDC Benchmarking - FTP Protocol")
    print("=" * 70)

    print("\n📋 Configuration:")
    print(f"   Dataset: {dataset}")
    print(f"   Repository: {repository}")
    print(f"   Site: {site}")

    repository = repository.upper()
    urls: List[str] = []
    note: Optional[str] = None
    deterministic_record: Optional[Dict[str, Any]] = None

    if deterministic_dataset_file:
        deterministic_record = load_run_record(deterministic_dataset_file, dataset)

        if deterministic_record:
            status = deterministic_record["status"]
            if status != "ACTIVE":
                raise SystemExit(
                    f"❌ Run {dataset} is marked as {status} in deterministic dataset."
                )

            https_urls = cast(List[str], deterministic_record["fastq_url_list"])
            if not https_urls:
                raise SystemExit(
                    f"❌ No FASTQ URLs stored for {dataset} in deterministic dataset."
                )

            urls = [_convert_https_to_ftp(u) for u in https_urls]
            note = (
                f"Resolved via deterministic dataset "
                f"({deterministic_record['category']})"
            )

            print("   Using deterministic dataset metadata.")
            print(f"   Resolved {len(urls)} file(s):")
            for u in urls[:3]:
                print(f"     - {u}")
            if len(urls) > 3:
                print(f"     - (+{len(urls) - 3} more)")
        else:
            print(
                "   Run not found in deterministic dataset, falling back to resolver."
            )

    # Only resolve from repository if deterministic dataset did not already provide URLs.
    if not urls:
        if repository == "ENA":
            https_urls = resolve_ena_fastq_urls(dataset, timeout=timeout)
            if not https_urls:
                raise SystemExit(f"❌ No FASTQ URLs on ENA for {dataset}.")

            urls = [_convert_https_to_ftp(u) for u in https_urls]

            print(f"   Resolved {len(urls)} file(s) via ENA (FTP).")
            for u in urls[:3]:
                print(f"     - {u}")
            if len(urls) > 3:
                print(f"     - (+{len(urls) - 3} more)")

        elif repository == "SRA":
            raise SystemExit(
                "❌ SRA FTP resolver not implemented yet. Use --repository ENA"
            )

        elif repository == "DDBJ":
            raise SystemExit("❌ DDBJ FTP resolver not implemented yet.")
        else:
            raise SystemExit(f"Unsupported repository: {repository}")

    print("\n📊 Baseline Measurements")
    print("-" * 70)

    target_url = urls[0]
    parsed = urlparse(target_url)
    target_host = parsed.hostname

    baseline_local = get_baseline_metrics()
    baseline_net = (
        get_network_baseline(host=target_host)
        if target_host
        else {
            "network_latency_ms": None,
            "network_path": None,
            "packet_loss_percent": None,
        }
    )

    sizes: List[int] = []
    durations: List[float] = []
    md5_last = ""
    sha256_last = ""
    expected_md5: Optional[str] = None
    checksum_match: Optional[bool] = None
    last_sys_avgs: Dict[str, Any] = {"cpu_usage_percent": 0.0, "memory_usage_mb": 0.0}

    start_ts: Optional[float] = None
    end_ts: Optional[float] = None

    if deterministic_record:
        md5s = cast(List[str], deterministic_record["fastq_md5_list"])
        if md5s:
            expected_md5 = md5s[0]

    out_path = Path(dataset)

    for i in range(1, repeats + 1):
        trial_label = f" (trial {i}/{repeats})" if repeats > 1 else ""
        print("\n🚀 Starting Download" + trial_label)
        print("-" * 70)
        print(f"   FTP Host: {target_host}")
        print(f"   Path: {parsed.path}")

        mon = SystemMonitor(interval=0.5)
        mon.start()

        t0 = time.time()
        if start_ts is None:
            start_ts = t0

        try:
            _ftp_download(target_url, out_path, timeout=ftp_timeout)
        except Exception as e:
            print(f"❌ FTP download failed: {e}")
            mon.stop()
            raise SystemExit(1)
        finally:
            t1 = time.time()
            mon.stop()
            end_ts = t1

        try:
            size_bytes = out_path.stat().st_size
        except FileNotFoundError:
            size_bytes = 0

        duration = t1 - t0
        avg_mbps = _pretty_mbps(size_bytes, duration)

        if size_bytes > 0:
            print("\n🔐 Calculating checksums...")
            md5_last = _md5(out_path)
            sha256_last = _sha256(out_path)
            if expected_md5:
                checksum_match = md5_last == expected_md5
        else:
            md5_last = ""
            sha256_last = ""
            checksum_match = None

        last_sys_avgs = mon.get_averages()

        print("\n✅ Download Complete!" if size_bytes > 0 else "\n❌ Download Failed!")
        print("   Files: 1")
        print(f"   Total size: {size_bytes / (1024 * 1024):.2f} MB")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Average speed: {avg_mbps:.2f} Mbps")
        if md5_last:
            print(f"   MD5 checksum: {md5_last}")
            print(f"   SHA256 checksum: {sha256_last}")
        if expected_md5:
            print(f"   Expected MD5: {expected_md5}")
            print(f"   MD5 match: {checksum_match}")
        print(f"   CPU usage: {last_sys_avgs.get('cpu_usage_percent', 0):.1f}%")
        print(f"   Memory usage: {last_sys_avgs.get('memory_usage_mb', 0):.1f} MB")

        sizes.append(size_bytes)
        durations.append(duration)

        try:
            out_path.unlink(missing_ok=True)
            print("\n🗑️  Cleaned up 1 downloaded file(s)")
        except Exception:
            pass

    if repeats > 1:
        speeds = [_pretty_mbps(s, d) for s, d in zip(sizes, durations)]
        print("\n📈 Aggregate over", repeats, "runs")
        print(
            f"   Speed   → mean: {statistics.mean(speeds):.2f} Mbps, "
            f"median: {statistics.median(speeds):.2f} Mbps, "
            f"p95: {statistics.quantiles(speeds, n=20)[18]:.2f} Mbps"
        )
        print(
            f"   Time    → mean: {statistics.mean(durations):.2f} s, "
            f"median: {statistics.median(durations):.2f} s, "
            f"p95: {statistics.quantiles(durations, n=20)[18]:.2f} s"
        )

    last_size = sizes[-1] if sizes else 0
    last_duration = durations[-1] if durations else 0.0
    last_speed = _pretty_mbps(last_size, last_duration)
    start_iso = _iso8601(start_ts or time.time())
    end_iso = _iso8601(end_ts or time.time())

    result: Dict[str, Any] = {
        "timestamp": start_iso,
        "end_timestamp": end_iso,
        "site": site,
        "protocol": "ftp",
        "repository": repository,
        "dataset_id": dataset,
        "duration_sec": round(last_duration, 2),
        "file_size_bytes": int(last_size),
        "average_speed_mbps": round(last_speed, 2),
        "cpu_usage_percent": last_sys_avgs.get("cpu_usage_percent", 0.0),
        "memory_usage_mb": last_sys_avgs.get("memory_usage_mb", 0.0),
        "status": "success" if last_size > 0 and md5_last else "fail",
        "checksum_md5": md5_last or "",
        "checksum_sha256": sha256_last or "",
        "expected_checksum_md5": expected_md5,
        "checksum_match": checksum_match,
        "write_speed_mbps": baseline_local.get("write_speed_mbps"),
        "network_latency_ms": baseline_net.get("network_latency_ms"),
        "packet_loss_percent": baseline_net.get("packet_loss_percent"),
        "network_path": (baseline_net.get("network_path") or "").splitlines()
        if baseline_net.get("network_path")
        else None,
        "tool_version": "Python ftplib",
        "notes": note or None,
        "error_message": None,
    }

    print("\n🧾 Result (schema v1.2 fields subset):")
    print(json.dumps(result, indent=2))

    if no_submit:
        print("\n⏭️  Skipping submission (--no-submit)")
    else:
        try:
            endpoint = os.getenv("BENCHMARK_SUBMIT_URL")
            if not endpoint:
                print("⚠️  BENCHMARK_SUBMIT_URL not set; skipping submission.")
            else:
                submit_result(endpoint, result)
                print("\n📤 Submitted result successfully.")
        except Exception as e:
            print(f"\n⚠️  Submission error: {e}")

    print("\n" + "=" * 70)
    print("✅ Benchmark Complete!")


if __name__ == "__main__":
    main()
