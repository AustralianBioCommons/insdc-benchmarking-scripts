# insdc_benchmarking_scripts/utils/repositories/ena_repo.py
from __future__ import annotations
import csv
import io
import urllib.parse
import requests

"""
Resolver for ENA FASTQ HTTPS URLs using the ENA Filereport API.
"""


def resolve_ena_fastq_urls(run_accession: str, timeout: int = 20) -> list[str]:
    """
    Return HTTPS FASTQ URLs for a run by querying ENA Filereport.
    Handles single/paired (semicolon-separated field).

    :param run_accession: SRR/ERR/DRR accession
    :param timeout: request timeout in seconds
    :raises requests.RequestException: if the API request fails
    :raises ValueError: if no FASTQ URLs found for the accession
    """
    acc = run_accession.strip()
    api = (
        "https://www.ebi.ac.uk/ena/portal/api/filereport"
        f"?accession={urllib.parse.quote(acc)}"
        "&result=read_run&fields=fastq_ftp&format=tsv&limit=0"
    )

    response = requests.get(api, timeout=timeout)
    response.raise_for_status()  # Raises HTTPError for bad status codes

    tsv = response.text

    # Debug: print the raw response to understand what we're getting
    if not tsv.strip():
        raise ValueError(f"Empty response from ENA API for accession {acc}")

    # Debug output
    import sys

    print(f"\n🔍 DEBUG: ENA API Response for {acc}:", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)
    print(tsv, file=sys.stderr)
    print(f"{'=' * 60}\n", file=sys.stderr)

    rows = list(csv.reader(io.StringIO(tsv), delimiter="\t"))

    # Check if we have a header row and at least one data row
    if len(rows) < 1:
        raise ValueError(f"No data returned from ENA API for accession {acc}")

    if len(rows) < 2:
        raise ValueError(
            f"No FASTQ files found for {acc}. "
            f"This accession may not have FASTQ files available, or the data may only be in SRA format. "
            f"Header received: {rows[0] if rows else 'none'}"
        )

    # The fastq_ftp field is the SECOND column (index 1)
    # Row structure: [run_accession, fastq_ftp]
    if len(rows[1]) < 2:
        raise ValueError(f"Unexpected TSV format for {acc}: {rows[1]}")

    fastq = (rows[1][1] or "").strip()  # Changed from [0] to [1]

    if not fastq:
        raise ValueError(
            f"Empty fastq_ftp field for {acc}. "
            f"This accession may not have FASTQ files available via ENA. "
            f"Try using SRA repository instead."
        )

    # Split by semicolon for paired-end data
    parts = [p.strip() for p in fastq.split(";") if p.strip()]

    # Debug: show what we parsed
    print(f"🔍 DEBUG: Found {len(parts)} part(s) after splitting:", file=sys.stderr)
    for i, p in enumerate(parts, 1):
        print(f"  {i}. {p!r}", file=sys.stderr)

    # Ensure https:// (ENA returns paths like "ftp.sra.ebi.ac.uk/vol1/fastq/...")
    urls = []
    for p in parts:
        if p.startswith("https://"):
            urls.append(p)
        elif p.startswith("http://"):
            urls.append(p)
        elif p.startswith("ftp://"):
            # Convert ftp:// to https://
            urls.append(p.replace("ftp://", "https://"))
        elif p.startswith("ftp.sra.ebi.ac.uk/") or p.startswith("ftp."):
            # ENA returns paths like "ftp.sra.ebi.ac.uk/vol1/fastq/..."
            urls.append("https://" + p)
        else:
            # If it doesn't have a protocol or hostname, assume it's a path on ftp.sra.ebi.ac.uk
            urls.append(f"https://ftp.sra.ebi.ac.uk/{p.lstrip('/')}")

    print(f"🔍 DEBUG: Returning {len(urls)} URL(s):", file=sys.stderr)
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}", file=sys.stderr)

    return urls
