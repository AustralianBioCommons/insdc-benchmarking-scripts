# insdc_benchmarking_scripts/utils/repositories/ena_repo.py
from __future__ import annotations
"""
Resolver for ENA FASTQ HTTPS URLs using the ENA Filereport API.
"""

import csv
import io
import urllib.request
import urllib.parse


def resolve_ena_fastq_urls(run_accession: str, timeout: int = 20) -> list[str]:
    """
    Return HTTPS FASTQ URLs for a run by querying ENA Filereport.
    Handles single/paired (semicolon-separated field).

    :param run_accession: SRR/ERR/DRR accession
    :param timeout: request timeout in seconds
    """
    acc = run_accession.strip()
    api = (
        "https://www.ebi.ac.uk/ena/portal/api/filereport"
        f"?accession={urllib.parse.quote(acc)}"
        "&result=read_run&fields=fastq_ftp&format=tsv&limit=0"
    )
    with urllib.request.urlopen(api, timeout=timeout) as r:
        tsv = r.read().decode("utf-8", "replace")
    rows = list(csv.reader(io.StringIO(tsv), delimiter="\t"))
    if len(rows) < 2:
        return []
    fastq = (rows[1][0] or "").strip()
    if not fastq:
        return []
    parts = [p.strip() for p in fastq.split(";") if p.strip()]
    # Ensure https:// (ENA returns ftp.sra.ebi.ac.uk paths)
    return [("https://" + p) if p.startswith("ftp.") else p for p in parts]
