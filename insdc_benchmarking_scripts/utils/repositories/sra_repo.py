# insdc_benchmarking_scripts/utils/repositories/sra_repo.py
from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import Literal, List, Tuple
from urllib.parse import quote
import urllib.request
import urllib.error

from .ena_repo import resolve_ena_fastq_urls

"""
Resolver for NCBI SRA endpoints.

INSDC prefixes:
- SRR = NCBI, ERR = ENA, DRR = DDBJ.
NCBI ODP mirrors partner data, so SRR/ERR/DRR all appear in ODP buckets.

Modes:
- sra_cloud (default): return HTTPS links to public .sra objects in ODP buckets (AWS+GCS).
  Some runs exist WITHOUT the ".sra" extension (e.g. .../SRR000001/SRR000001).
- fastq_via_ena: delegate to ENA for FASTQ HTTPS URLs.

You can prefer a mirror with preferred_mirror: "auto" | "aws" | "gcs".
"""

DEFAULT_UA = "insdc-benchmarking/0.1 (+https://biocommons.org.au)"
Mirror = Literal["auto", "aws", "gcs"]


@dataclass
class Resolution:
    run_accession: str
    mode: str
    preferred_mirror: Mirror
    candidates: List[str]
    live: List[str]
    note: str = ""


def _to_mirror(value: str, *, default: Mirror = "auto") -> Mirror:
    """Map arbitrary string to a strict Mirror literal, falling back to default."""
    v = value.lower()
    if v == "aws":
        return "aws"
    if v == "gcs":
        return "gcs"
    if v == "auto":
        return "auto"
    return default


def _candidates_for(acc: str, mirror: Mirror) -> list[str]:
    """Build candidate URLs in a preferred order for given mirror."""
    q = quote
    aws = [
        f"https://sra-pub-run-odp.s3.amazonaws.com/sra/{q(acc)}/{q(acc)}",
        f"https://sra-pub-run-odp.s3.amazonaws.com/sra/{q(acc)}/{q(acc)}.sra",
    ]
    gcs = [
        f"https://storage.googleapis.com/sra-pub-run-odp/sra/{q(acc)}/{q(acc)}",
        f"https://storage.googleapis.com/sra-pub-run-odp/sra/{q(acc)}/{q(acc)}.sra",
    ]
    if mirror == "aws":
        return aws + gcs
    if mirror == "gcs":
        return gcs + aws
    return aws + gcs  # auto


def _url_exists(url: str, timeout: int = 10) -> bool:
    """HEAD probe; on failure, try a 1-byte Range GET."""
    head = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": DEFAULT_UA}
    )
    try:
        with contextlib.closing(urllib.request.urlopen(head, timeout=timeout)) as r:
            return 200 <= getattr(r, "status", 200) < 400
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return False
    except Exception:
        pass

    get1 = urllib.request.Request(
        url, method="GET", headers={"Range": "bytes=0-0", "User-Agent": DEFAULT_UA}
    )
    try:
        with contextlib.closing(urllib.request.urlopen(get1, timeout=timeout)) as r:
            return 200 <= getattr(r, "status", 200) < 400
    except Exception:
        return False


def resolve_sra_urls(
    run_accession: str,
    *,
    mode: str = "sra_cloud",  # or "fastq_via_ena"
    preferred_mirror: Mirror = "auto",  # "auto" | "aws" | "gcs"
    timeout: int = 20,
) -> list[str]:
    """
    Back-compat: return only the URL list (no explanation).
    """
    urls, _res = resolve_sra_urls_ex(
        run_accession,
        mode=mode,
        preferred_mirror=preferred_mirror,
        timeout=timeout,
    )
    return urls


def resolve_sra_urls_ex(
    run_accession: str,
    *,
    mode: str = "sra_cloud",
    preferred_mirror: Mirror = "auto",
    timeout: int = 20,
) -> Tuple[List[str], Resolution]:
    """
    Resolve URLs for SRA repository benchmarking and return an explanation.

    :return: (urls, Resolution)
    """
    if mode == "fastq_via_ena":
        urls = resolve_ena_fastq_urls(run_accession, timeout=timeout)
        res = Resolution(
            run_accession=run_accession,
            mode=mode,
            preferred_mirror="auto",
            candidates=[],
            live=urls[:],
            note="Delegated to ENA for FASTQ.",
        )
        return urls, res

    acc = run_accession.strip()

    # Env may override; normalize to a strict Mirror literal without reassigning the param.
    env_pref = os.getenv("SRA_MIRROR", "").strip().lower()
    mirror: Mirror = _to_mirror(env_pref, default=preferred_mirror)

    candidates = _candidates_for(acc, mirror)
    live = [u for u in candidates if _url_exists(u, timeout=timeout)]

    note = ""
    if mirror in ("aws", "gcs"):
        # Determine if *preferred* group had any live URLs; if not, explain fallback.
        group_prefix = (
            "https://sra-pub-run-odp.s3.amazonaws.com"
            if mirror == "aws"
            else "https://storage.googleapis.com"
        )
        had_preferred = any(u.startswith(group_prefix) for u in live)
        if not had_preferred:
            note = f"No live objects on preferred mirror '{mirror}', falling back."

    res = Resolution(
        run_accession=acc,
        mode="sra_cloud",
        preferred_mirror=mirror,
        candidates=candidates,
        live=live[:],
        note=note,
    )
    # Return live URLs if any, otherwise fall back to the candidate list so callers can still try.
    return (live or candidates), res


__all__ = ["resolve_sra_urls", "resolve_sra_urls_ex"]
