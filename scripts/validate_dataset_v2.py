#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

DATASET = Path("data/deterministic_datasets_v2.csv")
REPORT = Path("data/deterministic_datasets_v2_validation_report.json")
ISSUES = Path("data/deterministic_datasets_v2_validation_issues.csv")

ALLOWED_STATUSES = {"ACTIVE", "SUPPRESSED", "NOT_FOUND"}
ALLOWED_CATEGORIES = {
    "1_MB_FILE",
    "1_GB_FILE",
    "1_TB_FILE",
    "10_RANDOM_1MB",
    "1000_RANDOM_1MB",
    "10000_RANDOM_1MB",
    "10_RANDOM_1GB",
    "1000_RANDOM_1GB",
    "5_RANDOM_500GB",
}


def parse_json_list(value):
    if pd.isna(value):
        return [], "EMPTY_VALUE"

    try:
        parsed = json.loads(value)
    except Exception:
        return None, "INVALID_JSON"

    if not isinstance(parsed, list):
        return None, "NOT_A_LIST"

    return parsed, None


def main():
    if not DATASET.exists():
        raise SystemExit(f"Missing input file: {DATASET}")

    df = pd.read_csv(DATASET)
    df.columns = [c.strip() for c in df.columns]

    required = {
        "CATEGORY",
        "RUN_ACCESSION",
        "STATUS",
        "FASTQ_MD5_LIST",
        "FASTQ_URL_LIST",
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    issues = []

    # duplicate rows
    dupes = df[df.duplicated(subset=["CATEGORY", "RUN_ACCESSION"], keep=False)]
    for _, row in dupes.iterrows():
        issues.append(
            {
                "TYPE": "DUPLICATE_CATEGORY_RUN",
                "CATEGORY": row["CATEGORY"],
                "RUN_ACCESSION": row["RUN_ACCESSION"],
                "STATUS": row["STATUS"],
                "DETAIL": "Duplicate CATEGORY + RUN_ACCESSION row",
            }
        )

    for _, row in df.iterrows():
        category = str(row["CATEGORY"]).strip()
        run_accession = str(row["RUN_ACCESSION"]).strip()
        status = str(row["STATUS"]).strip()

        if category not in ALLOWED_CATEGORIES:
            issues.append(
                {
                    "TYPE": "INVALID_CATEGORY",
                    "CATEGORY": category,
                    "RUN_ACCESSION": run_accession,
                    "STATUS": status,
                    "DETAIL": f"Unexpected category: {category}",
                }
            )

        if status not in ALLOWED_STATUSES:
            issues.append(
                {
                    "TYPE": "INVALID_STATUS",
                    "CATEGORY": category,
                    "RUN_ACCESSION": run_accession,
                    "STATUS": status,
                    "DETAIL": f"Unexpected status: {status}",
                }
            )

        md5_list, md5_err = parse_json_list(row["FASTQ_MD5_LIST"])
        url_list, url_err = parse_json_list(row["FASTQ_URL_LIST"])

        if md5_err:
            issues.append(
                {
                    "TYPE": "INVALID_FASTQ_MD5_LIST",
                    "CATEGORY": category,
                    "RUN_ACCESSION": run_accession,
                    "STATUS": status,
                    "DETAIL": md5_err,
                }
            )
            md5_list = []

        if url_err:
            issues.append(
                {
                    "TYPE": "INVALID_FASTQ_URL_LIST",
                    "CATEGORY": category,
                    "RUN_ACCESSION": run_accession,
                    "STATUS": status,
                    "DETAIL": url_err,
                }
            )
            url_list = []

        if status == "ACTIVE":
            if len(md5_list) == 0:
                issues.append(
                    {
                        "TYPE": "ACTIVE_WITH_EMPTY_MD5_LIST",
                        "CATEGORY": category,
                        "RUN_ACCESSION": run_accession,
                        "STATUS": status,
                        "DETAIL": "ACTIVE row has no MD5 entries",
                    }
                )

            if len(md5_list) != len(url_list):
                issues.append(
                    {
                        "TYPE": "ACTIVE_MD5_URL_COUNT_MISMATCH",
                        "CATEGORY": category,
                        "RUN_ACCESSION": run_accession,
                        "STATUS": status,
                        "DETAIL": f"MD5 count={len(md5_list)}, URL count={len(url_list)}",
                    }
                )

        if status in {"SUPPRESSED", "NOT_FOUND"}:
            if len(md5_list) > 0 or len(url_list) > 0:
                issues.append(
                    {
                        "TYPE": "NON_ACTIVE_WITH_NON_EMPTY_LISTS",
                        "CATEGORY": category,
                        "RUN_ACCESSION": run_accession,
                        "STATUS": status,
                        "DETAIL": f"MD5 count={len(md5_list)}, URL count={len(url_list)}",
                    }
                )

    issues_df = pd.DataFrame(
        issues, columns=["TYPE", "CATEGORY", "RUN_ACCESSION", "STATUS", "DETAIL"]
    )
    issues_df.to_csv(ISSUES, index=False)

    report = {
        "dataset_file": str(DATASET),
        "total_rows": int(len(df)),
        "active_rows": int((df["STATUS"] == "ACTIVE").sum()),
        "suppressed_rows": int((df["STATUS"] == "SUPPRESSED").sum()),
        "not_found_rows": int((df["STATUS"] == "NOT_FOUND").sum()),
        "issues_total": int(len(issues_df)),
        "valid": len(issues_df) == 0,
    }

    REPORT.write_text(json.dumps(report, indent=2))

    print(f"Wrote: {ISSUES}")
    print(f"Wrote: {REPORT}")
    print(json.dumps(report, indent=2))

    if len(issues_df) > 0:
        raise SystemExit("Validation failed: issues were found.")


if __name__ == "__main__":
    main()
