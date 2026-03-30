#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

INPUT = Path("Datasets - Sheet1.csv")  # adjust to your repo location
OUT_DIR = Path("data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

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

RUN_RE = re.compile(r"^(ERR|SRR|DRR)\d+$", re.IGNORECASE)


def main():
    df = pd.read_csv(INPUT)
    df.columns = [c.strip() for c in df.columns]

    required = {"CATEGORY", "RUN ACCESSION"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    # Normalize fields
    df["CATEGORY"] = df["CATEGORY"].astype(str).str.strip()
    df["RUN ACCESSION"] = df["RUN ACCESSION"].astype(str).str.strip()

    # Drop empty rows
    df = df[
        (df["CATEGORY"] != "")
        & (df["RUN ACCESSION"] != "")
        & (df["RUN ACCESSION"].str.lower() != "nan")
    ]

    # Build issues list
    issues = []

    # Category validation
    bad_cat = df[~df["CATEGORY"].isin(ALLOWED_CATEGORIES)]
    for _, r in bad_cat.iterrows():
        issues.append(
            {
                "type": "BAD_CATEGORY",
                "CATEGORY": r["CATEGORY"],
                "RUN_ACCESSION": r["RUN ACCESSION"],
            }
        )

    # Accession validation
    bad_acc = df[~df["RUN ACCESSION"].str.match(RUN_RE)]
    for _, r in bad_acc.iterrows():
        issues.append(
            {
                "type": "BAD_ACCESSION",
                "CATEGORY": r["CATEGORY"],
                "RUN_ACCESSION": r["RUN ACCESSION"],
            }
        )

    # Duplicate rows within category
    dup_rows = df[df.duplicated(subset=["CATEGORY", "RUN ACCESSION"], keep=False)]
    for _, r in dup_rows.iterrows():
        issues.append(
            {
                "type": "DUPLICATE_WITHIN_CATEGORY",
                "CATEGORY": r["CATEGORY"],
                "RUN_ACCESSION": r["RUN ACCESSION"],
            }
        )

    # Run accession in multiple categories
    run_cat_counts = (
        df.groupby("RUN ACCESSION")["CATEGORY"]
        .nunique()
        .reset_index(name="category_count")
    )
    multi_cat_runs = run_cat_counts[run_cat_counts["category_count"] > 1][
        "RUN ACCESSION"
    ].tolist()
    if multi_cat_runs:
        # record only once per run
        for run_id in sorted(multi_cat_runs):
            cats = sorted(
                df[df["RUN ACCESSION"] == run_id]["CATEGORY"].unique().tolist()
            )
            issues.append(
                {
                    "type": "RUN_IN_MULTIPLE_CATEGORIES",
                    "CATEGORY": ";".join(cats),
                    "RUN_ACCESSION": run_id,
                }
            )

    # Clean minimal catalog (dedupe exact category/run pairs)
    clean = (
        df[["CATEGORY", "RUN ACCESSION"]]
        .drop_duplicates(subset=["CATEGORY", "RUN ACCESSION"])
        .sort_values(["CATEGORY", "RUN ACCESSION"])
        .reset_index(drop=True)
    )

    # Report
    report = {
        "input_file": str(INPUT),
        "rows_input": int(len(df)),
        "rows_clean": int(len(clean)),
        "unique_runs": int(clean["RUN ACCESSION"].nunique()),
        "categories_present": sorted(clean["CATEGORY"].unique().tolist()),
        "bad_categories": int(len(bad_cat)),
        "bad_accessions": int(len(bad_acc)),
        "duplicate_within_category_rows": int(len(dup_rows)),
        "runs_in_multiple_categories": int(len(multi_cat_runs)),
        "issues_total": int(len(issues)),
    }

    clean_path = OUT_DIR / "run_catalog_clean.csv"
    issues_path = OUT_DIR / "run_catalog_issues.csv"
    report_path = OUT_DIR / "run_catalog_report.json"

    clean.to_csv(clean_path, index=False)
    pd.DataFrame(issues).to_csv(issues_path, index=False)
    report_path.write_text(json.dumps(report, indent=2))

    print("Wrote:")
    print(f" - {clean_path}")
    print(f" - {issues_path}")
    print(f" - {report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
