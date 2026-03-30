#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

RUN_CATALOG = Path("data/run_catalog_clean.csv")
ENA_RAW = Path("data/ena_raw_metadata.json")

OUT_DATASET = Path("data/deterministic_datasets_v2.csv")
OUT_ISSUES = Path("data/deterministic_datasets_v2_issues.csv")


def split_ena_list(value) -> list[str]:
    if value is None:
        return []

    value = str(value).strip()
    if not value:
        return []

    return [item.strip() for item in value.split(";") if item.strip()]


def classify_status(
    run_accession: str, ena_data: dict
) -> tuple[str, list[str], list[str]]:
    if run_accession not in ena_data:
        return "NOT_FOUND", [], []

    record = ena_data[run_accession] or {}

    md5_list = split_ena_list(record.get("fastq_md5", ""))
    url_list = split_ena_list(record.get("fastq_ftp", ""))

    if not md5_list:
        return "SUPPRESSED", md5_list, url_list

    return "ACTIVE", md5_list, url_list


def main():
    if not RUN_CATALOG.exists():
        raise SystemExit(f"Missing input file: {RUN_CATALOG}")

    if not ENA_RAW.exists():
        raise SystemExit(f"Missing input file: {ENA_RAW}")

    runs_df = pd.read_csv(RUN_CATALOG)
    runs_df.columns = [c.strip() for c in runs_df.columns]

    required = {"CATEGORY", "RUN ACCESSION"}
    missing = required - set(runs_df.columns)
    if missing:
        raise SystemExit(
            f"Missing required columns in {RUN_CATALOG}: {sorted(missing)}"
        )

    with ENA_RAW.open() as f:
        ena_data = json.load(f)

    output_rows = []
    issue_rows = []

    for _, row in runs_df.iterrows():
        category = str(row["CATEGORY"]).strip()
        run_accession = str(row["RUN ACCESSION"]).strip()

        status, md5_list, url_list = classify_status(run_accession, ena_data)

        if status == "ACTIVE" and len(md5_list) != len(url_list):
            issue_rows.append(
                {
                    "TYPE": "MD5_URL_COUNT_MISMATCH",
                    "CATEGORY": category,
                    "RUN_ACCESSION": run_accession,
                    "STATUS": status,
                    "MD5_COUNT": len(md5_list),
                    "URL_COUNT": len(url_list),
                    "FASTQ_MD5_LIST": json.dumps(md5_list, separators=(",", ":")),
                    "FASTQ_URL_LIST": json.dumps(url_list, separators=(",", ":")),
                }
            )

        output_rows.append(
            {
                "CATEGORY": category,
                "RUN_ACCESSION": run_accession,
                "STATUS": status,
                "FASTQ_MD5_LIST": json.dumps(md5_list, separators=(",", ":")),
                "FASTQ_URL_LIST": json.dumps(url_list, separators=(",", ":")),
            }
        )

    out_df = (
        pd.DataFrame(output_rows)
        .sort_values(["CATEGORY", "RUN_ACCESSION"])
        .reset_index(drop=True)
    )

    issues_columns = [
        "TYPE",
        "CATEGORY",
        "RUN_ACCESSION",
        "STATUS",
        "MD5_COUNT",
        "URL_COUNT",
        "FASTQ_MD5_LIST",
        "FASTQ_URL_LIST",
    ]
    issues_df = pd.DataFrame(issue_rows, columns=issues_columns)

    OUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_DATASET, index=False)
    issues_df.to_csv(OUT_ISSUES, index=False)

    print(f"Wrote: {OUT_DATASET}")
    print(f"Wrote: {OUT_ISSUES}")
    print()
    print("Summary")
    print(f"  Total rows:    {len(out_df)}")
    print(f"  ACTIVE:        {(out_df['STATUS'] == 'ACTIVE').sum()}")
    print(f"  SUPPRESSED:    {(out_df['STATUS'] == 'SUPPRESSED').sum()}")
    print(f"  NOT_FOUND:     {(out_df['STATUS'] == 'NOT_FOUND').sum()}")
    print(f"  Issues logged: {len(issues_df)}")


if __name__ == "__main__":
    main()
