# insdc_benchmarking_scripts/scripts/benchmark_http.py
"""HTTP/HTTPS benchmarking using wget"""

from __future__ import annotations

import click
import subprocess
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Sequence
from urllib.parse import urlparse
from os.path import basename

from insdc_benchmarking_scripts.utils.config import load_config
from insdc_benchmarking_scripts.utils.system_metrics import (
    SystemMonitor,
    get_baseline_metrics,
)
from insdc_benchmarking_scripts.utils.network_baseline import get_network_baseline
from insdc_benchmarking_scripts.utils.submit import submit_result
from insdc_benchmarking_scripts.utils.repositories import (
    resolve_ena_fastq_urls,
    resolve_ddbj_fastq_urls,
    resolve_sra_urls,
)


def calculate_md5(filepath: Path) -> str:
    """Calculate MD5 checksum of file"""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def resolve_urls_for_repo(
    repository: str,
    dataset: str,
    *,
    ddbj_mode: str = "native",      # "native" or "mirror"
    sra_mode: str = "sra_cloud",    # "sra_cloud" or "fastq_via_ena"
    timeout: int = 20,
) -> list[str]:
    repo = repository.upper()
    if repo == "ENA":
        return resolve_ena_fastq_urls(dataset, timeout=timeout)
    if repo == "DDBJ":
        return resolve_ddbj_fastq_urls(
            dataset,
            native=(ddbj_mode == "native"),
            mirror_from_ena=(ddbj_mode == "mirror"),
            timeout=timeout,
        )
    if repo == "SRA":
        return resolve_sra_urls(dataset, mode=sra_mode, timeout=timeout)
    raise ValueError(f"Unknown repository: {repository}")


@click.command()
@click.option("--dataset", required=True, help="Dataset ID (e.g., SRR12345678)")
@click.option(
    "--repository",
    type=click.Choice(["ENA", "DDBJ", "SRA"]),
    default="ENA",
    help="Repository to benchmark",
)
@click.option("--site", help="Site identifier (overrides config)")
@click.option(
    "--config-file",
    type=click.Path(),
    default="config.yaml",
    help="Config file path",
)
@click.option("--no-submit", is_flag=True, help="Skip submitting result to API")
@click.option(
    "--ddbj-mode",
    type=click.Choice(["native", "mirror"]),
    default="native",
    help="DDBJ resolver mode: 'native' (parse DDBJ dir) or 'mirror' (use ENA filenames mapped to DDBJ).",
)
@click.option(
    "--sra-mode",
    type=click.Choice(["sra_cloud", "fastq_via_ena"]),
    default="sra_cloud",
    help="SRA resolver mode: 'sra_cloud' (.sra objects via cloud) or 'fastq_via_ena' (FASTQ via ENA).",
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Per-file download timeout (seconds).",
)
def main(
    dataset: str,
    repository: str,
    site: Optional[str],
    config_file: str,
    no_submit: bool,
    ddbj_mode: str,
    sra_mode: str,
    timeout: int,
):
    """
    Benchmark HTTP/HTTPS download performance for a chosen repository.

    Examples:
      ENA FASTQ over HTTPS:
        python -m insdc_benchmarking_scripts.scripts.benchmark_http --dataset SRR000003 --repository ENA

      DDBJ (native listing):
        python -m insdc_benchmarking_scripts.scripts.benchmark_http --dataset DRR001001 --repository DDBJ --ddbj-mode native

      SRA (.sra over cloud HTTPS):
        python -m insdc_benchmarking_scripts.scripts.benchmark_http --dataset SRR000003 --repository SRA --sra-mode sra_cloud
    """
    print("=" * 70)
    print("🌐 INSDC Benchmarking - HTTP/HTTPS Protocol")
    print("=" * 70)

    # Load config
    config = load_config(Path(config_file))
    # Allow CLI timeout override to influence config timeout
    config_timeout = int(config.get("timeout", timeout))
    timeout = timeout or config_timeout
    site = site or config.get("site", "unknown")

    print(f"\n📋 Configuration:")
    print(f"   Dataset: {dataset}")
    print(f"   Repository: {repository}")
    print(f"   Site: {site}")

    # Resolve URLs according to repository
    urls = resolve_urls_for_repo(
        repository,
        dataset,
        ddbj_mode=ddbj_mode,
        sra_mode=sra_mode,
        timeout=20,
    )
    if not urls:
        print(f"❌ No URLs found for {dataset} (repository={repository}).")
        return 1
    print(f"   Resolved {len(urls)} file(s):")
    for u in urls:
        print(f"     - {u}")

    # Extract host for baseline from the first URL
    host = urlparse(urls[0]).hostname

    # Setup download directory
    download_dir = Path(config.get("download_dir", "./downloads"))
    download_dir.mkdir(exist_ok=True, parents=True)

    # Baseline measurements
    print("\n📊 Baseline Measurements")
    print("-" * 70)
    baseline = get_baseline_metrics()
    network_baseline = get_network_baseline(host)
    baseline.update(network_baseline)

    # Start monitoring
    monitor = SystemMonitor()
    monitor.start()

    # Run download(s)
    print("\n🚀 Starting Download")
    print("-" * 70)

    started_at = datetime.now(timezone.utc)
    wall_start = time.time()

    try:
        total_bytes = 0
        md5s: list[str] = []

        for idx, url in enumerate(urls, start=1):
            # Prefer original filename if present; otherwise fall back to dataset-based name
            name = basename(urlparse(url).path) or f"{dataset}_{idx}"
            output_file = download_dir / name

            display_url = (url[:70] + "…") if len(url) > 73 else url
            print(f"   Running: wget -O {output_file.name} {display_url}")
            result = subprocess.run(
                ["wget", "-O", str(output_file), url],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            monitor.sample()

            if result.returncode != 0:
                raise Exception(f"wget failed with code {result.returncode}: {result.stderr}")

            sz = output_file.stat().st_size
            total_bytes += sz

            # MD5 per file (works for .fastq.gz and .sra alike)
            print("\n🔐 Calculating MD5 checksum...")
            md5s.append(calculate_md5(output_file))

        wall_end = time.time()
        duration = wall_end - wall_start
        speed_mbps = (total_bytes * 8) / (duration * 1_000_000)

        # Get system metrics (averages)
        system_metrics = monitor.get_averages()

        # Print results
        print("\n✅ Download Complete!")
        print(f"   Files: {len(urls)}")
        print(f"   Total size: {total_bytes / (1024 ** 2):.2f} MB")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Average speed: {speed_mbps:.2f} Mbps")
        if len(md5s) == 1:
            print(f"   MD5 checksum: {md5s[0]}")
        else:
            for i, m in enumerate(md5s, 1):
                print(f"   MD5_{i}: {m}")
        print(f"   CPU usage: {system_metrics['cpu_usage_percent']:.1f}%")
        print(f"   Memory usage: {system_metrics['memory_usage_mb']:.1f} MB")

        # Build result payload
        result_data = {
            "timestamp": started_at.isoformat(),
            "site": site.lower(),
            "protocol": "http",  # still HTTP/HTTPS via wget in this script
            "repository": repository,
            "dataset_id": dataset,
            "files_downloaded": len(urls),
            "duration_sec": round(duration, 2),
            "file_size_bytes": total_bytes,
            "average_speed_mbps": round(speed_mbps, 2),
            "status": "success",
            "checksums_md5": md5s,
            "tool_version": "wget",
            **system_metrics,
        }
        # Add optional metrics if available
        for k, v in baseline.items():
            if v is not None:
                result_data[k] = v

        # Cleanup if configured
        if config.get("cleanup", True):
            removed = 0
            for idx, url in enumerate(urls, start=1):
                name = basename(urlparse(url).path) or f"{dataset}_{idx}"
                f = download_dir / name
                if f.exists():
                    f.unlink()
                    removed += 1
            print(f"\n🗑️  Cleaned up {removed} downloaded file(s)")

        # Submit result
        if not no_submit:
            print("\n" + "=" * 70)
            resp = submit_result(
                config.get("api_endpoint", ""),
                result_data,
                config.get("api_token", ""),
            )
            if isinstance(resp, dict) and resp.get("status") not in ("ok", "skipped"):
                print("⚠️  Submission failed:", resp)
        else:
            print("\n⏭️  Skipping submission (--no-submit)")
            import json
            print(json.dumps(result_data, indent=2))

        print("\n" + "=" * 70)
        print("✅ Benchmark Complete!")
        print("=" * 70)
        return 0

    except subprocess.TimeoutExpired:
        print(f"\n❌ Download timeout after {timeout} seconds")
        return 1
    except FileNotFoundError:
        print("\n❌ Error: 'wget' command not found. Please install wget.")
        return 1
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
