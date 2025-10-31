"""HTTP/HTTPS benchmarking using wget"""

import click
import subprocess
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.config import load_config
from utils.system_metrics import SystemMonitor, get_baseline_metrics
from utils.network_baseline import get_network_baseline
from utils.submit import submit_result


def get_http_url(repository: str, dataset_id: str) -> str:
    """Get HTTP download URL for dataset"""
    # Example URLs - adjust for your actual repositories
    urls = {
        "ENA": f"https://ftp.sra.ebi.ac.uk/vol1/fastq/{dataset_id[:6]}/00{dataset_id[-1]}/{dataset_id}/{dataset_id}_1.fastq.gz",
        "SRA": f"https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos3/sra-pub-run-11/{dataset_id}/{dataset_id}.1",
        "DDBJ": f"https://ddbj.nig.ac.jp/public/ddbj_database/dra/fastq/{dataset_id[:6]}/{dataset_id}/{dataset_id}_1.fastq.gz",
    }
    return urls.get(repository, urls["ENA"])


def calculate_md5(filepath: Path) -> str:
    """Calculate MD5 checksum of file"""
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
    Benchmark HTTP/HTTPS download performance

    Example:
        python scripts/benchmark_http.py --dataset SRR12345678 --repository ENA --site nci
    """
    print("=" * 70)
    print("🌐 INSDC Benchmarking - HTTP/HTTPS Protocol")
    print("=" * 70)

    # Load config
    config = load_config(Path(config_file))
    site = site or config['site']

    print(f"\n📋 Configuration:")
    print(f"   Dataset: {dataset}")
    print(f"   Repository: {repository}")
    print(f"   Site: {site}")

    # Get download URL
    url = get_http_url(repository, dataset)
    print(f"   URL: {url}")

    # Extract host for baseline
    from urllib.parse import urlparse
    host = urlparse(url).hostname

    # Setup download directory
    download_dir = Path(config['download_dir'])
    download_dir.mkdir(exist_ok=True, parents=True)
    output_file = download_dir / f"{dataset}_http.fastq.gz"

    # Baseline measurements
    print("\n📊 Baseline Measurements")
    print("-" * 70)
    baseline = get_baseline_metrics()
    network_baseline = get_network_baseline(host)
    baseline.update(network_baseline)

    # Start monitoring
    monitor = SystemMonitor()
    monitor.start()

    # Run download
    print("\n🚀 Starting Download")
    print("-" * 70)

    start_time = datetime.utcnow()
    start_timestamp = time.time()

    try:
        # Use wget for download
        print(f"   Running: wget -O {output_file.name} {url[:50]}...")
        result = subprocess.run(
            ['wget', '-O', str(output_file), url],
            capture_output=True,
            text=True,
            timeout=config['timeout']
        )

        monitor.sample()

        end_timestamp = time.time()
        duration = end_timestamp - start_timestamp

        if result.returncode != 0:
            raise Exception(f"wget failed with code {result.returncode}: {result.stderr}")

        # Get file size
        file_size = output_file.stat().st_size

        # Calculate speed
        speed_mbps = (file_size * 8) / (duration * 1_000_000)

        # Calculate checksum
        print("\n🔐 Calculating MD5 checksum...")
        checksum = calculate_md5(output_file)

        # Get system metrics
        system_metrics = monitor.get_averages()

        # Print results
        print("\n✅ Download Complete!")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   File size: {file_size / (1024 ** 2):.2f} MB")
        print(f"   Average speed: {speed_mbps:.2f} Mbps")
        print(f"   MD5 checksum: {checksum}")
        print(f"   CPU usage: {system_metrics['cpu_usage_percent']:.1f}%")
        print(f"   Memory usage: {system_metrics['memory_usage_mb']:.1f} MB")

        # Build result
        result_data = {
            "timestamp": start_time.isoformat() + "Z",
            "site": site.lower(),
            "protocol": "http-browser",
            "repository": repository,
            "dataset_id": dataset,
            "duration_sec": round(duration, 2),
            "file_size_bytes": file_size,
            "average_speed_mbps": round(speed_mbps, 2),
            "status": "success",
            "checksum_md5": checksum,
            "tool_version": "wget",
        }

        # Add optional metrics if available
        result_data.update(system_metrics)
        for key, value in baseline.items():
            if value is not None:
                result_data[key] = value

        # Cleanup if configured
        if config['cleanup']:
            output_file.unlink()
            print(f"\n🗑️  Cleaned up: {output_file}")

        # Submit result
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

    except subprocess.TimeoutExpired:
        print(f"\n❌ Download timeout after {config['timeout']} seconds")
        return 1
    except FileNotFoundError:
        print("\n❌ Error: 'wget' command not found. Please install wget.")
        return 1
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())