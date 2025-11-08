🌐 INSDC Benchmarking Scripts
=============================

Automated benchmarking tools for testing **INSDC data download performance** across repositories (**ENA**, **SRA**, and **DDBJ**) and multiple transfer protocols.

* * * * *

🚀 Quick Start
--------------

### 1\. Install

```bash
pip install insdc-benchmarking-scripts
```

### 2\. Configure

```
cp config.yaml.example config.yaml
# Edit config.yaml:
# site: nci
# api_endpoint: https://your.api/submit
# api_token: YOUR_TOKEN   # optional

```

### 3\. Run a Benchmark

#### HTTP/HTTPS (wget-based)

```
benchmark-http --dataset DRR12345678 --repository ENA --site nci

```

#### SRA Cloud .sra Objects (AWS/GCS)

```
benchmark-http\
  --dataset DRR000001\
  --repository SRA\
  --sra-mode sra_cloud\
  --mirror auto\
  --no-submit

```

#### ENA FASTQ via HTTPS

```
benchmark-http\
  --dataset SRR000001\
  --repository ENA\
  --no-submit

```

* * * * *

🧠 Key Features
---------------

-   ✅ HTTP/HTTPS benchmarking using wget
-   ✅ SRA Cloud (AWS/GCS) .sra object downloads
-   ✅ ENA FASTQ over HTTPS
-   🧩 Automatic system metrics --- CPU%, memory MB, disk write speed
-   🌍 Network baselines --- ping/traceroute latency and route
-   🧾 JSON output aligned with INSDC Benchmarking Schema v1.2
-   📤 Optional API submission (secure HTTP POST)
-   🧪 Repeatable tests with `--repeats` and aggregate stats
-   🧰 Mirror control for SRA: `--mirror [aws|gcs|auto]`, `--require-mirror`, `--explain`

* * * * *

📦 Supported Protocols
----------------------

| Protocol | Implementation | Status |
| --- | --- | --- |
| HTTP/HTTPS | wget | ✅ Stable |
| FTP | ftplib | ✅ Stable |
| Globus | Python SDK | 🔄 Planned |
| Aspera | CLI SDK | 🔄 Planned |
| SRA Toolkit | fasterq-dump (wrapper) | 🔄 Planned |

* * * * *

⚙️ Configuration
----------------

See `config.yaml.example`:

```
site: nci
api_endpoint: https://your.api/submit
api_token: your-secret-token

```

* * * * *

📊 Example Output
-----------------

```
{
  "timestamp": "2025-11-06T06:21:33Z",
  "end_timestamp": "2025-11-06T06:23:05Z",
  "site": "nci",
  "protocol": "http",
  "repository": "SRA",
  "dataset_id": "DRR000001",
  "duration_sec": 92.3,
  "file_size_bytes": 596137898,
  "average_speed_mbps": 51.6,
  "cpu_usage_percent": 7.2,
  "memory_usage_mb": 10300.5,
  "status": "success",
  "checksum_md5": "bf11d3ea9d7e0b6e984998ea2dfd53ca",
  "write_speed_mbps": 3350.3,
  "network_latency_ms": 8.9,
  "tool_version": "GNU Wget 1.21.4",
  "notes": "Resolved from AWS ODP mirror"
}

```

* * * * *

🧱 Repository Structure
-----------------------

```
insdc-benchmarking-scripts/
├── scripts/
│   ├── benchmark_http.py        # HTTP/HTTPS benchmarking CLI (Click)
│   ├── benchmark_ftp.py         # FTP benchmarking (ftplib)
│   └── benchmark_aspera.py      # Future Aspera integration
│
├── insdc_benchmarking_scripts/
│   ├── utils/
│   │   ├── repositories/        # ENA/SRA/DDBJ resolvers
│   │   ├── system_metrics.py    # CPU/memory sampler
│   │   ├── network_baseline.py  # ping/traceroute helpers
│   │   ├── submit.py            # HTTP POST to results API
│   │   └── config.py            # Config loader
│   └── __init__.py
│
├── docs/
│   ├── INSTALLATION.md          # Setup and verification instructions
│   ├── USAGE.md                 # CLI usage and examples
│   ├── protocols/               # Protocol-specific notes
│   └── schema/                  # INSDC Benchmarking Schema v1.2
│
├── config.yaml.example          # Example configuration file
├── requirements.txt             # Dependencies for pip installs
├── pyproject.toml               # Poetry build config
├── README.md                    # This file
└── LICENSE

```

* * * * *

📚 Documentation
----------------

-   📘 [Installation Guide](docs/INSTALLATION.md)
-   🧭 [Usage Guide](docs/USAGE.md)
-   🧩 [Protocol Guides](docs/protocols/)
-   📄 [INSDC Benchmarking Schema v1.2](docs/schema/)

* * * * *

🧭 Roadmap
----------

-   [ ] Add Globus and Aspera benchmarking
-   [ ] Unified results ingestion API (FastAPI backend)
-   [ ] Web dashboard for live performance visualization
-   [ ] Scheduled batch benchmarking for curated datasets
-   [ ] Add object checksum validation and retry support

* * * * *

🤝 Contributing
---------------

Contributions are welcome! Please open an issue or submit a pull request to add protocols, metrics, or infrastructure integrations.

### Development Workflow

```
# Fork and clone
git clone https://github.com/AustralianBioCommons/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Install dependencies
poetry install

# Run a test benchmark
poetry run benchmark-http --dataset DRR000001 --repository ENA --no-submit

```

* * * * *

**Maintained by:** Australian BioCommons\
📍 University of Melbourne\
🔗 Licensed under the Apache 2.0 License
