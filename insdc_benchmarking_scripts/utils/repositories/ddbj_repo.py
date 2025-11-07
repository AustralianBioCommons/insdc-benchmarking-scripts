# insdc_benchmarking_scripts/utils/repositories/ddbj_repo.py
from __future__ import annotations
import re
import urllib.request
from html import unescape
from .ena_repo import resolve_ena_fastq_urls  # used only when mirror_from_ena=True

"""
Resolver for DDBJ FASTQ HTTPS URLs.

Two modes:
1) native: try to list the DDBJ directory natively and pick *.fastq.gz links.
2) mirror_from_ena: resolve filenames from ENA and map to DDBJ path root.

If you are benchmarking repositories independently, prefer `native=True`.
"""


def _ddbj_dir_url(accession: str) -> str:
    # DDBJ mirrors ENA's /vol1/fastq layout under a different root.
    parent = accession[:6]
    return (
        f"https://ddbj.nig.ac.jp/public/ddbj_database/dra/fastq/{parent}/{accession}/"
    )


def _fetch(url: str, timeout: int = 20) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _extract_fastq_links(html: str) -> list[str]:
    # Very lightweight parser for directory index pages
    # Match href="FILENAME.fastq.gz" or >FILENAME.fastq.gz<
    html = unescape(html)
    pattern = r">([^<]+\.fastq\.gz)<"
    return sorted(set(re.findall(pattern, html)))


def resolve_ddbj_fastq_urls(
    run_accession: str,
    *,
    native: bool = True,
    timeout: int = 20,
    mirror_from_ena: bool = False,
) -> list[str]:
    """
    Resolve DDBJ FASTQ URLs for an accession.

    :param native: if True, parse DDBJ directory listing directly (preferred for repo benchmarking)
    :param mirror_from_ena: if True, use ENA filenames and project them onto DDBJ path (fallback)
    """
    dir_url = _ddbj_dir_url(run_accession)

    if native:
        try:
            html = _fetch(dir_url, timeout=timeout)
            files = _extract_fastq_links(html)
            return [dir_url + f for f in files]
        except Exception:
            # fall through to mirror_from_ena if allowed
            if not mirror_from_ena:
                return []

    if mirror_from_ena:
        try:
            ena_urls = resolve_ena_fastq_urls(run_accession, timeout=timeout)
            # Replace ENA root with DDBJ root
            mapped = []
            for u in ena_urls:
                needle = "/vol1/fastq/"
                i = u.find(needle)
                if i == -1:
                    continue
                tail = u[i + len(needle) :]
                mapped.append(
                    "https://ddbj.nig.ac.jp/public/ddbj_database/dra/fastq/" + tail
                )
            return mapped
        except Exception:
            return []

    return []
