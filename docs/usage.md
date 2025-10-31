# Usage Guide

## Basic Usage

### Run HTTP Benchmark

```bash
python scripts/benchmark_http.py \\
  --dataset SRR12345678 \\
  --repository ENA \\
  --site nci
```

### Run FTP Benchmark

```bash
python scripts/benchmark_ftp.py \\
  --dataset SRR12345678 \\
  --repository ENA \\
  --site nci
```

## Command-Line Options

### Common Options (all protocols)

- `--dataset` (required): INSDC dataset ID (e.g., SRR12345678)
- `--repository`: Repository to download from (ENA, SRA, DDBJ). Default: ENA
- `--site`: Site identifier. Overrides config.yaml
- `--config-file`: Path to config file. Default: config.yaml
- `--no-submit`: Skip submitting results to API

## Examples

### Test without submitting results

```bash
python scripts/benchmark_http.py \\
  --dataset SRR000001 \\
  --no-submit
```

### Use custom config file

```bash
python scripts/benchmark_http.py \\
  --dataset SRR000001 \\
  --config-file /path/to/custom-config.yaml
```

### Run for different repositories

```bash
# ENA
python scripts/benchmark_http.py --dataset SRR000001 --repository ENA

# SRA
python scripts/benchmark_http.py --dataset SRR000001 --repository SRA

# DDBJ
python scripts/benchmark_http.py --dataset SRR000001 --repository DDBJ
```

## Automated Benchmarking

### Using cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add daily benchmark at 2 AM
0 2 * * * cd /path/to/insdc-benchmarking-scripts && python scripts/benchmark_http.py --dataset SRR000001
```

### Using systemd timer (Linux)

See `examples/systemd/` for service and timer files.

### Batch script

```bash
#!/bin/bash
# Run benchmarks for multiple datasets

DATASETS=("SRR000001" "SRR000002" "SRR000003")

for dataset in "${DATASETS[@]}"; do
    echo "Benchmarking $dataset..."
    python scripts/benchmark_http.py --dataset $dataset
    sleep 60  # Wait between tests
done
```

## Output

### Console Output

The scripts provide detailed output including:
- Configuration summary
- Baseline measurements (I/O speed, network latency)
- Download progress
- Final results (speed, checksum, resource usage)
- Submission status

### Result Submission

Results are automatically submitted to the configured API endpoint in JSON format matching the INSDC benchmarking schema.

## Troubleshooting

### Download fails

- Check internet connectivity
- Verify dataset ID exists
- Try different repository (--repository option)
- Check timeout setting in config.yaml

### Submission fails

- Verify API endpoint in config.yaml
- Check API token if required
- Use --no-submit to test benchmark without submission