# INSDC Benchmarking Scripts

A benchmarking toolkit for INSDC data access (ENA, SRA, DDBJ).

This project focuses on:

- reproducible benchmarking using deterministic datasets
- performance measurement across protocols (FTP, HTTP via wget)
- checksum validation for data integrity

---

## 🚀 Primary Usage (Recommended)

The main supported entry points are:

- `benchmark-http` (uses wget over HTTP/HTTPS)
- `benchmark-ftp` (uses Python ftplib)

These commands provide the core benchmarking functionality.

---

## 🧪 Example Usage

### HTTP (via wget)

```bash
poetry run benchmark-http \
  --dataset ERR3853594 \
  --repository ENA \
  --deterministic-dataset-file scripts/data/deterministic_datasets_v2.csv \
  --no-submit
```

### FTP

```bash
poetry run benchmark-ftp \
  --dataset ERR3853594 \
  --repository ENA \
  --deterministic-dataset-file scripts/data/deterministic_datasets_v2.csv \
  --no-submit
```

---

## 📊 Deterministic Dataset

A curated dataset (`deterministic_datasets_v2.csv`) is used to ensure:

- stable file URLs
- correct MD5 checksums
- reproducible benchmarking

This dataset was rebuilt after the initial dataset was found to contain incorrect checksums.

---

## ✅ Checksum Validation

For each run:

1. File is downloaded
2. MD5 checksum is computed
3. Compared against expected checksum

### Result logic

- success → download OK + checksum match
- fail → download failed OR checksum mismatch

---

## 📐 Schema Alignment

Results are designed to align with the INSDC benchmarking schema:

https://github.com/AustralianBioCommons/insdc-benchmarking-schema

Important:

- HTTP benchmarking uses `"protocol": "wget"`
- FTP benchmarking uses `"protocol": "ftp"`

---

## 📌 Scope

- currently benchmarks the first file per run
- checksum validation applies per run
- multi-file benchmarking is not yet implemented

---

## ⚙️ Optional: Benchmark Runner

A batch runner (`benchmark-runner`) exists for:

- running multiple datasets
- filtering by category/status
- aggregating results into CSV

However:

- it is not the primary interface
- its CLI differs from the main commands
- it is best suited for internal or large-scale runs

---

## 🛣️ Roadmap

- multi-file benchmarking
- category-based batch execution
- schema validation (pending Python upgrade)
- reporting and summaries

---

## 📄 License

Apache 2.0
