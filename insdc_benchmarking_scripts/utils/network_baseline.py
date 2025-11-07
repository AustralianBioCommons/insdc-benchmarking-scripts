from __future__ import annotations
import shlex
import subprocess
from typing import Dict, Any, Optional

"""
Network baseline measurements.
Uses system tools if present; safe fallbacks otherwise.
"""


def _run(cmd: str, timeout: int = 5) -> str:
    try:
        out = subprocess.check_output(
            shlex.split(cmd), stderr=subprocess.STDOUT, timeout=timeout
        )
        return out.decode("utf-8", "ignore")
    except Exception:
        return ""


def measure_latency(
    host: str = "8.8.8.8", count: int = 3, timeout: int = 5
) -> Optional[float]:
    """
    Returns average latency in ms using `ping`. Returns None if not available.
    """
    # Unix-style ping
    out = _run(f"ping -c {count} -W {timeout} {host}", timeout=timeout + count + 1)
    if not out:
        return None
    # parse rtt line: rtt min/avg/max/mdev = 8.884/8.884/8.884/0.000 ms
    for line in out.splitlines():
        if "min/avg/max" in line or "round-trip" in line:
            parts = line.split("=")[-1].strip().split("/")
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except Exception:
                    return None
    return None


def get_network_baseline(host: str = "8.8.8.8") -> Dict[str, Any]:
    lat = measure_latency(host)
    # Basic traceroute if available
    trace = _run(f"traceroute -m 5 {host}", timeout=10)
    result = {
        "network_latency_ms": lat,
        "network_path": trace.strip() or None,
        "packet_loss_percent": None,  # not measured here
    }
    return result
