#!/bin/bash
# Example: Run benchmarks for multiple protocols

DATASET="SRR000001"
REPOSITORY="ENA"
SITE="nci"

echo "Running HTTP benchmark..."
python scripts/benchmark_http.py \
  --dataset $DATASET \
  --repository $REPOSITORY \
  --site $SITE

echo ""
echo "Running FTP benchmark..."
python scripts/benchmark_ftp.py \
  --dataset $DATASET \
  --repository $REPOSITORY \
  --site $SITE

echo ""
echo "All benchmarks complete!"
