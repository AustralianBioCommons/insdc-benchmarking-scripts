"""FTP benchmarking using Python ftplib"""

import click
import time
import hashlib
from ftplib import FTP
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from insdc_benchmarking_scripts.utils.config import load_config
from insdc_benchmarking_scripts.utils.system_metrics import SystemMonitor, get_baseline_metrics
from insdc_benchmarking_scripts.utils.network_baseline import get_network_baseline
from insdc_benchmarking_scripts.utils.submit import submit_result


def get_ftp_url(repository: str, dataset_id: str) -> str:
    """Get FTP URL for dataset"""
    # Example URLs - adjust for your actual repositories
    urls = {
        "ENA": f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{dataset_id[:6]}/00{dataset_id[-1]}/{dataset_id}/{dataset_id}_1.fastq.gz",
        "SRA": f"ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByRun/sra/SRR/{dataset_id[:6]}/{dataset_id}/{dataset_id}.sra",
        "DDBJ": f"ftp://ftp.ddbj.nig.ac.jp/ddbj_database/dra/fastq/{dataset_id[:6]}/{dataset_id}/{dataset_id}_1.fastq.gz",
    }
    return urls.get(repository, urls["ENA"])


def calculate_md5(filepath: Path) -> str:
    """Calculate MD5 checksum"""
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


@click.command()
@click.option('--dataset', required=True, help='Dataset ID (e.g., SRR12345678)')
@click.option('--repository', type=click.Choice(['ENA', 'SRA', 'DDBJ']), default='ENA', help='INSDC repository')
@click.option('--site', help='Site identifier (overrides config)')
@click.option('--config-file', type=click.Path(), default='config.yaml', help='Config file path')
@click.option('--no-submit', is_flag=True, help='Skip submitting result to API')
def main(dataset: str, repository: str, site: Optional[str], config_file: str, no_submit: bool):
    """
    Benchmark FTP download performance

    Example:
        python scripts/benchmark_ftp.py --dataset SRR12345678 --repository ENA --site nci
    """
    print("=" * 70)
    print("📁 INSDC Benchmarking - FTP Protocol")
    print("=" * 70)

    # Load config
    config = load_config(Path(config_file))
    site = site or config['site']

    print(f"\n📋 Configuration:")
    print(f"   Dataset: {dataset}")
    print(f"   Repository: {repository}")
    print(f"   Site: {site}")

    # Get FTP URL
    ftp_url = get_ftp_url(repository, dataset)
    parsed = urlparse(ftp_url)
    host = parsed.hostname
    path = parsed.path

    print(f"   FTP Host: {host}")
    print(f"   Path: {path}")

    # Setup
    download_dir = Path(config['download_dir'])
    download_dir.mkdir(exist_ok=True, parents=True)
    output_file = download_dir / f"{dataset}_ftp.fastq.gz"

    # Baseline
    print("\n📊 Baseline Measurements")
    print("-" * 70)
    baseline = get_baseline_metrics()
    network_baseline = get_network_baseline(host)
    baseline.update(network_baseline)

    # Monitor
    monitor = SystemMonitor()
    monitor.start()

    # Download
    print("\n🚀 Starting FTP Download")
    print("-" * 70)

    start_time = datetime.utcnow()
    start_timestamp = time.time()

    try:
        # Connect to FTP
        print(f"   Connecting to {host}...")
        ftp = FTP(host, timeout=config['timeout'])
        ftp.login()  # Anonymous login
        print(f"   Connected successfully")

        # Download file
        print(f"   Downloading {path}...")
        with open(output_file, 'wb') as f:
            ftp.retrbinary(f'RETR {path}', f.write)

        ftp.quit()

        monitor.sample()

        end_timestamp = time.time()
        duration = end_timestamp - start_timestamp

        # File size
        file_size = output_file.stat().st_size

        # Speed
        speed_mbps = (file_size * 8) / (duration * 1_000_000)

        # Checksum
        print("\n🔐 Calculating MD5 checksum...")
        checksum = calculate_md5(output_file)

        # Metrics
        system_metrics = monitor.get_averages()

        # Print results
        print("\n✅ Download Complete!")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   File size: {file_size / (1024 ** 2):.2f} MB")
        print(f"   Average speed: {speed_mbps:.2f} Mbps")
        print(f"   MD5 checksum: {checksum}")
        print(f"   CPU usage: {system_metrics['cpu_usage_percent']:.1f}%")
        print(f"   Memory usage: {system_metrics['memory_usage_mb']:.1f} MB")

        # Result
        result_data = {
            "timestamp": start_time.isoformat() + "Z",
            "site": site.lower(),
            "protocol": "ftp",
            "repository": repository,
            "dataset_id": dataset,
            "duration_sec": round(duration, 2),
            "file_size_bytes": file_size,
            "average_speed_mbps": round(speed_mbps, 2),
            "status": "success",
            "checksum_md5": checksum,
            "tool_version": "ftplib",
        }

        # Add optional metrics
        result_data.update(system_metrics)
        for key, value in baseline.items():
            if value is not None:
                result_data[key] = value

        # Cleanup
        if config['cleanup']:
            output_file.unlink()
            print(f"\n🗑️  Cleaned up: {output_file}")

        # Submit
        if not no_submit:
            print("\n" + "=" * 70)
            success = submit_result(
                result_data,
                config['api_endpoint'],
                config.get('api_token', '')
            )
            if not success:
                print("⚠️  Submission failed, but benchmark completed successfully")
        else:
            print("\n⏭️  Skipping submission (--no-submit flag)")
            import json
            print(f"\nResult data:\n{json.dumps(result_data, indent=2)}")

        print("\n" + "=" * 70)
        print("✅ Benchmark Complete!")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())