# INSDC Benchmarking Scripts

A lightweight benchmarking toolkit for evaluating data access performance across INSDC repositories (ENA, SRA, DDBJ) using HTTP/HTTPS and FTP protocols.

The tool measures:

- download performance (duration, throughput)
- system resource usage (CPU, memory)
- network characteristics (latency, packet loss, path)
- data integrity via checksum validation

---

## Features

- HTTP/HTTPS benchmarking using `wget`
- FTP benchmarking using Python `ftplib`
- ENA support, with SRA support for HTTP/HTTPS object resolution
- optional deterministic dataset support for pre-resolved URLs and expected MD5 checksums
- repeated runs with aggregate statistics
- JSON result output for submission and downstream analysis

---

## Installation

Clone the repository and install dependencies with Poetry:

```bash
git clone https://github.com/AustralianBioCommons/insdc-benchmarking-scripts.git
cd insdc-benchmarking-scripts
poetry install
poetry shell
```

---

## Basic Usage

### HTTP/HTTPS benchmark

```bash
poetry run benchmark-http \
  --dataset ERR3853594 \
  --repository ENA \
  --no-submit
```

### FTP benchmark

```bash
poetry run benchmark-ftp \
  --dataset ERR3853594 \
  --repository ENA \
  --no-submit
```

---

## Deterministic Dataset Support

Both CLI tools can optionally use a deterministic dataset CSV containing:

- pre-resolved FASTQ URLs
- expected MD5 checksums
- dataset categorisation and status

This is useful when:

- you want reproducible benchmarking
- you want to avoid runtime URL-resolution variability
- you want to compare the downloaded file checksum against an expected value

### Example

```bash
poetry run benchmark-http \
  --dataset ERR3853594 \
  --repository ENA \
  --deterministic-dataset-file scripts/data/deterministic_datasets_v2.csv \
  --no-submit
```

```bash
poetry run benchmark-ftp \
  --dataset ERR3853594 \
  --repository ENA \
  --deterministic-dataset-file scripts/data/deterministic_datasets_v2.csv \
  --no-submit
```

When a deterministic dataset file is provided, the benchmark will:

- use the stored URL for the requested run when available
- load the expected MD5 from the dataset
- compute the downloaded file MD5
- compare actual vs expected checksum for the run being benchmarked

---

## Checksum Validation

Checksum comparison is performed for each run that is benchmarked when an expected checksum is available.

Current behaviour:

- the benchmark uses the first resolved file for a run
- the downloaded file MD5 is computed
- the computed MD5 is compared to the expected MD5 from the deterministic dataset
- a checksum mismatch should be treated as a failed benchmark result

This keeps the current workflow simple while still validating integrity.

---

## Schema

Benchmark result payloads should conform to the INSDC benchmarking schema:

- Schema repository: `https://github.com/AustralianBioCommons/insdc-benchmarking-schema`
- Current schema version used by this project: `result-schema-v1.2.json`

### Important schema notes

The schema defines:

- `protocol` as one of:
  - `ftp`
  - `aspera`
  - `globus`
  - `wget`
  - `sra-toolkit`
  - `ena-downloader`
  - `http-browser`
  - `other`
- `repository` as one of:
  - `ENA`
  - `SRA`
  - `DDBJ`

For this project:

- FTP results should use protocol value `ftp`
- HTTP/HTTPS benchmarking performed via `wget` should use protocol value `wget`

If you extend the local result object with additional fields such as:

- `expected_checksum_md5`
- `checksum_match`

treat those as local or operational fields unless and until they are added to the shared schema.

### Required schema fields

The v1.2 schema requires at minimum:

- `timestamp`
- `site`
- `protocol`
- `repository`
- `dataset_id`
- `status`
- `duration_sec`
- `file_size_bytes`
- `average_speed_mbps`
- `checksum_md5`

---

## Example Result

Example of a core result payload aligned to the shared schema:

```json
{
  "timestamp": "2026-03-01T10:00:00Z",
  "site": "nci",
  "protocol": "ftp",
  "repository": "ENA",
  "dataset_id": "ERR3853594",
  "duration_sec": 12.34,
  "file_size_bytes": 104857600,
  "average_speed_mbps": 67.8,
  "cpu_usage_percent": 12.5,
  "memory_usage_mb": 150.2,
  "status": "success",
  "checksum_md5": "0123456789abcdef0123456789abcdef",
  "checksum_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "write_speed_mbps": 500.0,
  "network_latency_ms": 12.3,
  "packet_loss_percent": 0.0,
  "network_path": ["hop1", "hop2"],
  "tool_version": "Python ftplib",
  "notes": null,
  "error_message": null
}
```

---

## CLI Options

### Common options

- `--dataset`
  INSDC run accession (for example `ERR3853594`, `SRR000001`)

- `--repository`
  Source repository: `ENA`, `SRA`, or `DDBJ`

- `--site`
  Short identifier for the benchmarking location

- `--repeats`
  Repeat the benchmark multiple times and print aggregate statistics

- `--no-submit`
  Run the benchmark without submitting the result

- `--deterministic-dataset-file`
  Optional path to `deterministic_datasets_v2.csv`

### HTTP/HTTPS options

- `--sra-mode`
- `--mirror`
- `--require-mirror`
- `--timeout`
- `--explain`

### FTP options

- `--timeout`
- `--ftp-timeout`

---

## Current Scope

Current implementation scope:

- benchmarks the first resolved file for a run
- supports checksum comparison for the file being benchmarked
- supports deterministic dataset lookup when provided

Not yet implemented:

- benchmarking every file for multi-file runs in a single invocation
- full category-based batch benchmarking from the CLI
- DDBJ resolver support across all protocols
- SRA FTP support

---

## Submission

To enable submission, set the submission endpoint:

```bash
export BENCHMARK_SUBMIT_URL=<endpoint>
```

If this variable is not set, the benchmark will print the result and skip submission.

---

## Project Structure

```text
insdc_benchmarking_scripts/
  scripts/
    benchmark_http.py
    benchmark_ftp.py
  utils/
    repositories.py
    system_metrics.py
    network_baseline.py
    submit.py

scripts/
  data/
    deterministic_datasets_v2.csv
```

---

## Development Notes

A deterministic dataset workflow was added to support checksum-driven benchmarking because the original dataset source included incorrect checksums. The current catalogue was regenerated from ENA metadata and validated before being integrated into the benchmark flow.

---

## Roadmap

- benchmark all files for multi-file runs
- add batch execution by deterministic dataset category
- add schema validation before submission
- improve reporting and result summaries
- extend resolver coverage

---

## License

Apache 2.0
