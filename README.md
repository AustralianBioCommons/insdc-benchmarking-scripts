# INSDC Benchmarking Scripts

Automated benchmarking scripts for testing INSDC data download performance.

## Quick Start

```bash
# Install with Poetry
poetry install

# Or with pip
pip install -r requirements.txt

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Run HTTP benchmark
python scripts/benchmark_http.py \
  --dataset SRR12345678 \
  --repository ENA \
  --site nci

# Run FTP benchmark  
python scripts/benchmark_ftp.py \
  --dataset SRR12345678 \
  --repository ENA \
  --site nci
```

## Supported Protocols

- ✅ HTTP/HTTPS (wget-based)
- ✅ FTP (ftplib-based)
- 🔄 Globus (coming soon)
- 🔄 Aspera (coming soon)

## Configuration

See `config.yaml.example` for all options.

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [Protocol Guides](docs/protocols/)
