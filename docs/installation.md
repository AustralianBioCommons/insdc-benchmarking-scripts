# Installation Guide

## Prerequisites

- Python 3.9 or higher
- wget (for HTTP benchmarks)
- ping and traceroute utilities (usually pre-installed)

## Installation Methods

### Option 1: Poetry (Recommended)

```bash
# Clone repository
git clone https://github.com/yourorg/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Install dependencies
poetry install

# Verify installation
poetry run python scripts/benchmark_http.py --help
```

### Option 2: pip

```bash
# Clone repository
git clone https://github.com/yourorg/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python scripts/benchmark_http.py --help
```

### Option 3: Direct pip install (when published)

```bash
pip install insdc-benchmarking-scripts
```

## Configuration

1. Copy the example config:
```bash
cp config.yaml.example config.yaml
```

2. Edit `config.yaml`:
```yaml
site: your-site-name       # e.g., nci, pawsey, aarnet
api_endpoint: YOUR_API_URL # Your benchmarking API endpoint
api_token: YOUR_TOKEN      # Optional authentication token
```

## Verify Installation

```bash
# Test HTTP benchmark (no submission)
python scripts/benchmark_http.py \\
  --dataset SRR000001 \\
  --repository ENA \\
  --site test \\
  --no-submit
```

## Troubleshooting

### "wget not found"
```bash
# macOS
brew install wget

# Ubuntu/Debian
sudo apt-get install wget

# CentOS/RHEL
sudo yum install wget
```

### "Module not found" errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # or: poetry shell

# Reinstall dependencies
pip install -r requirements.txt  # or: poetry install
```