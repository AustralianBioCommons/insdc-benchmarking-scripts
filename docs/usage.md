# Usage Guide
TL;DR
-----

### SRA .sra over HTTPS (ODP), auto-select mirror
```benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --no-submit```

### Force GCS mirror (fail if unavailable)
```benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --mirror gcs --require-mirror --no-submit```

### ENA FASTQ over HTTPS
```benchmark-http --dataset SRR000001 --repository ENA --no-submit```

### Explain URL resolution and run 3 trials
```benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --explain --repeats 3 --no-submit```

* * * * *

Command
-------

The tool is installed as a console script:

`benchmark-http [OPTIONS]`

### Required

-   `--dataset TEXT`\
    INSDC run accession, e.g. `SRR12345678`, `ERR1234567`, `DRR000001`.

### Common Options

-   `--repository [SRA|ENA|DDBJ]` *(default: SRA)*\
    Source repository to benchmark.

-   `--site TEXT` *(default: nci)*\
    Short label for where the test is run (printed/submitted with results).

-   `--timeout INTEGER` *(default: 20)*\
    Resolver HTTP timeout (seconds).

-   `--repeats INTEGER` *(default: 1)*\
    Download the selected URL N times and print aggregates. Submission uses the **last** run.

-   `--no-submit`\
    Run benchmark but **do not** POST results.

### SRA-specific Options

-   `--sra-mode [sra_cloud|fastq_via_ena]` *(default: sra_cloud)*

    -   `sra_cloud`: download `.sra` objects from NCBI ODP buckets (AWS/GCS), handling both with/without ".sra" suffix.

    -   `fastq_via_ena`: resolve FASTQ HTTPS via ENA (delegates to ENA resolver).

-   `--mirror [auto|aws|gcs]` *(default: auto)*\
    Preferred mirror for `sra_cloud`. The resolver probes candidates and may fall back.

-   `--require-mirror/--no-require-mirror` *(default: no-require-mirror)*\
    If set, **error out** when preferred mirror has no live objects.

-   `--explain`\
    Print all candidate URLs and mark which ones are LIVE. Helpful for mirror/debug.

> You can also set `SRA_MIRROR=aws|gcs|auto` in the environment. Env var overrides the CLI.

* * * * *

Examples
--------

### SRA: ODP `.sra` (auto mirror)

`benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --no-submit`

### SRA: Force GCS and fail if not present

`benchmark-http --dataset DRR000001\
  --repository SRA --sra-mode sra_cloud\
  --mirror gcs --require-mirror --no-submit`

### SRA: Show resolution details and run 5 trials

`benchmark-http --dataset SRR000001\
  --repository SRA --sra-mode sra_cloud\
  --explain --repeats 5 --no-submit`

### ENA: FASTQ over HTTPS

`benchmark-http --dataset SRR000001 --repository ENA --no-submit`

* * * * *

Output
------

-   Configuration summary (dataset, repo, site, mirror notes)

-   Baselines (local write speed; ping/traceroute best-effort to chosen host)

-   Per-trial:

    -   Download size, duration, average Mbps

    -   MD5 + SHA256 checksums

    -   Avg CPU% and memory MB (lightweight sampler)

-   If `--repeats > 1`: aggregate mean/median/p95

-   Result JSON (schema v1.2 subset) with:

    -   `timestamp` (start of first trial, ISO 8601 UTC)

    -   `end_timestamp` (end of last trial)

    -   `protocol`=`http`, `repository`, `dataset_id`, `duration_sec`, `file_size_bytes`,\
        `average_speed_mbps`, `cpu_usage_percent`, `memory_usage_mb`,\
        `checksum_md5`, `checksum_sha256`, baselines, `tool_version`, `notes`, `status`

-   Submission status (unless `--no-submit`)

* * * * *

Automation
----------

### Cron (Linux/macOS)

`# Edit crontab
crontab -e

# Daily at 02:00, no submission
0 2 * * * benchmark-http --dataset DRR000001 --repository SRA --sra-mode sra_cloud --no-submit >> /var/log/insdc-http.log 2>&1`

### Batch multiple datasets

`#!/usr/bin/env bash
set -euo pipefail

DATASETS=(DRR000001 SRR000001 ERR000001)
for ds in "${DATASETS[@]}"; do
  echo "Benchmarking $ds..."
  benchmark-http --dataset "$ds" --repository SRA --sra-mode sra_cloud --repeats 3 --no-submit
  sleep 60
done`

* * * * *

Troubleshooting
---------------

-   **"No downloadable URLs resolved..."**

    -   For very old runs, ENA FASTQ may not exist; try `--repository SRA --sra-mode sra_cloud`.

    -   Use `--explain` to see candidates; try the other mirror (`--mirror aws|gcs`).

    -   If you truly require a mirror, add `--require-mirror` to force a clear failure.

-   **Mirror not honored**

    -   If `--mirror gcs` prints an AWS URL, the resolver likely didn't find a live GCS object and fell back.

    -   Use `--require-mirror` to fail instead, or inspect with `--explain`.

-   **Slow speeds / high variance**

    -   Use `--repeats N` and compare mean/median/p95.

    -   Check the printed baselines; high latency or a long route can explain slow runs.

    -   Local disk write can dominate on very fast links---baseline shows write MB/s.

-   **Submission fails**

    -   Use `--no-submit` to test.

    -   Verify API endpoint/token in your config (if you wired `submit_result` to use it).