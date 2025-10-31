# insdc_benchmarking_scripts/utils/repositories/sra_repo.py
from __future__ import annotations
"""
Resolver for NCBI SRA endpoints.

Two modes:
1) sra_cloud: return HTTPS links to public .sra objects in the NCBI SRA Cloud buckets (AWS + GCP).
   NOTE: This downloads .sra files (container format), not FASTQ. Suitable for repository/protocol benchmarking.
2) fastq_via_ena: delegate to ENA resolver to obtain FASTQ HTTPS URLs (common practical choice for FASTQ over HTTP).

Why .sra for SRA? NCBI does not consistently expose FASTQ over HTTPS. Official tooling is SRA Toolkit (fasterq-dump).
"""

from urllib.parse import quote

from .ena_repo import resolve_ena_fastq_urls


def _sra_cloud_candidates(run_accession: str) -> list[str]:
    acc = run_accession.strip()
    # Known public buckets (object names frequently follow this layout).
    # These are *candidates* and may 404 for some runs; that's fine for benchmarking availability/latency.
    return [
        # AWS ODP
        f"https://sra-pub-run-odp.s3.amazonaws.com/sra/{quote(acc)}/{quote(acc)}.sra",
        # Older AWS path
        f"https://sra-pub-run-odp.s3.amazonaws.com/sra/{quote(acc)}/{quote(acc)}",
        # GCP ODP (via Google storage gateway)
        f"https://storage.googleapis.com/sra-pub-run-odp/sra/{quote(acc)}/{quote(acc)}.sra",
    ]


def resolve_sra_urls(
    run_accession: str,
    *,
    mode: str = "sra_cloud",  # or "fastq_via_ena"
    timeout: int = 20,
) -> list[str]:
    """
    Resolve URLs for SRA repository benchmarking.

    :param mode: "sra_cloud" (default) -> .sra objects via cloud buckets
                 "fastq_via_ena"      -> FASTQ via ENA resolver (if you want FASTQ specifically)
    """
    if mode == "fastq_via_ena":
        return resolve_ena_fastq_urls(run_accession, timeout=timeout)
    return _sra_cloud_candidates(run_accession)
