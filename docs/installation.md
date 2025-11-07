🧰 Installation Guide -- INSDC Benchmarking Scripts
==================================================

This guide describes how to install and verify the **INSDC Benchmarking Scripts** for measuring HTTP/HTTPS download performance across INSDC repositories (ENA, NCBI SRA, and DDBJ).

* * * * *

🧩 Prerequisites
----------------

Before installing, ensure your environment includes:

-   **Python ≥ 3.9**
-   **wget** -- required for HTTP/HTTPS transfers *(install via Homebrew, apt, or yum if missing)*
-   **ping** and **traceroute** -- used for network latency and route metrics *(usually pre-installed on Linux/macOS)*
-   **git** -- for cloning the repository

Optional (but recommended):

-   **psutil** -- used for CPU and memory sampling (installed automatically)

* * * * *

💻 Installation Methods
-----------------------

### Option 1 --- Poetry (Recommended for Development)

```
# Clone repository
git clone https://github.com/AustralianBioCommons/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Install dependencies (creates .venv automatically)
poetry install

# (optional) enter Poetry shell
poetry shell

# Verify CLI is available
poetry run benchmark-http --help

```

✅ This installs the package in editable mode inside a managed virtualenv. `benchmark-http` is automatically registered as a console command.

### Option 2 --- pip + Virtual Environment

```
# Clone repository
git clone https://github.com/AustralianBioCommons/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify CLI
benchmark-http --help

```

### Option 3 --- Direct pip Install (when published)

```
pip install insdc-benchmarking-scripts

```

Then run the CLI globally:

```
benchmark-http --help

```

* * * * *

⚙️ Configuration
----------------

The tool can run with defaults, but result submission and site info are typically configured in `config.yaml`.

Copy the example:

```
cp config.yaml.example config.yaml

```

Edit `config.yaml`:

```
site: nci                      # e.g., nci, pawsey, aarnet
api_endpoint: https://your.api/submit
api_token: YOUR_TOKEN          # optional authentication token

```

The file is automatically read by the submission helper.

* * * * *

🧪 Verify Installation
----------------------

### Quick dry-run (no submission)

```
benchmark-http --dataset SRR000001 --repository ENA --site test --no-submit

```

### SRA Cloud (ODP .sra, mirror auto)

```
benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --no-submit

```

### Force GCS mirror and fail if not found

```
benchmark-http --dataset DRR000001\
  --repository SRA --sra-mode sra_cloud\
  --mirror gcs --require-mirror --no-submit

```

**Expected output:**

-   Configuration summary (dataset, repo, site)
-   Baseline metrics (write speed, latency)
-   Download duration, throughput, checksums
-   CPU/memory usage
-   JSON summary (schema v1.2)
-   ✅ Benchmark Complete!

* * * * *

⚡ Optional: Bash Completion
---------------------------

If you installed via Poetry or pip editable mode:

```
eval "$(_BENCHMARK_HTTP_COMPLETE=bash_source benchmark-http)"

```

Add this to your `.bashrc` or `.zshrc` for autocompletion.

* * * * *

🧰 Troubleshooting
------------------

### "wget: command not found"

Install wget:

```
# macOS
brew install wget

# Ubuntu/Debian
sudo apt-get install -y wget

# CentOS/RHEL
sudo yum install -y wget

```

### "Module not found" errors

```
# Ensure you're in the virtual environment
source .venv/bin/activate        # or: poetry shell

# Reinstall dependencies
pip install -r requirements.txt  # or: poetry install

```

### "ping" or "traceroute" not found

The script will still run, but network baselines will be skipped.

```
sudo apt-get install -y iputils-ping traceroute
# or on macOS
brew install inetutils

```

### Submission Fails

-   Verify the `api_endpoint` and `api_token` in `config.yaml`
-   Ensure network and HTTPS trust are configured
-   Use `--no-submit` to validate benchmark logic without uploading

* * * * *

🧭 Tips
-------

-   Use `--repeats N` to smooth out transient network variability
-   Add `--require-mirror` to enforce AWS/GCS-only tests
-   Combine with cron or systemd for automated benchmarking
-   JSON results align with the INSDC Benchmarking Schema v1.2

* * * * *

✅ Example
---------

```
benchmark-http\
  --dataset DRR000001\
  --repository SRA\
  --sra-mode sra_cloud\
  --mirror aws\
  --no-submit

```

Produces a validated JSON result like:

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
  "checksum_sha256": "...",
  "write_speed_mbps": 3350.3,
  "network_latency_ms": 8.9,
  "tool_version": "GNU Wget 1.21.4",
  "notes": "Resolved from AWS ODP mirror"
}

```

* * * * *

📄 Next Steps
-------------

See `USAGE.md` for full CLI command reference and advanced examples.
