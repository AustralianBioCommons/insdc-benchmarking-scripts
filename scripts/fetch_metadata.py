#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd

from datasets.ena_fetch import fetch_all

RUN_CATALOG = Path("data/run_catalog_clean.csv")
ENA_RAW = Path("data/ena_raw_metadata.json")


def main():
    df = pd.read_csv(RUN_CATALOG)
    df.columns = [c.strip() for c in df.columns]

    run_ids = df["RUN ACCESSION"].dropna().astype(str).str.strip().unique().tolist()

    ena_data = fetch_all(run_ids)

    ENA_RAW.parent.mkdir(parents=True, exist_ok=True)
    with ENA_RAW.open("w") as f:
        json.dump(ena_data, f, indent=2, sort_keys=True)

    print(f"Fetched metadata for {len(ena_data)} runs out of {len(run_ids)}")
    print(f"Wrote: {ENA_RAW}")


if __name__ == "__main__":
    main()
