"""
System metrics sampler for benchmarking.
Attempts to use `psutil` if available; otherwise provides safe fallbacks.
"""

from __future__ import annotations
import os
import time
import tempfile
from typing import List, Dict, Any, Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore


class SystemMonitor:
    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self):
        self.start_time = time.time()

    def sample(self):
        # CPU
        if psutil:
            try:
                self.cpu_samples.append(psutil.cpu_percent(interval=None))
            except Exception:
                self.cpu_samples.append(0.0)
            try:
                mem = psutil.virtual_memory()
                self.memory_samples.append(mem.used / (1024 * 1024))  # MB
            except Exception:
                self.memory_samples.append(0.0)
        else:
            # Fallbacks
            self.cpu_samples.append(0.0)
            self.memory_samples.append(0.0)

    def stop(self):
        self.end_time = time.time()

    def get_averages(self) -> Dict[str, float]:
        cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        mem = (
            sum(self.memory_samples) / len(self.memory_samples)
            if self.memory_samples
            else 0.0
        )
        return {
            "cpu_usage_percent": round(cpu, 2),
            "memory_usage_mb": round(mem, 2),
        }


def _test_write_speed(
    tmp_dir: Optional[str] = None, size_mb: int = 100
) -> Optional[float]:
    """Rough write speed test; returns MB/s or None on failure."""
    try:
        tmp_dir = tmp_dir or tempfile.gettempdir()
        path = os.path.join(tmp_dir, "bench_write_test.bin")
        chunk = b"0" * (1024 * 1024)  # 1 MB
        start = time.time()
        with open(path, "wb") as f:
            for _ in range(size_mb):
                f.write(chunk)
        end = time.time()
        try:
            os.remove(path)
        except Exception:
            pass
        elapsed = end - start
        if elapsed <= 0:
            return None
        mb_per_s = size_mb / elapsed
        # Convert MB/s -> Mbps (decimal-ish; close enough for baseline)
        return round(mb_per_s * 8, 2)
    except Exception:
        return None


def get_baseline_metrics() -> Dict[str, Any]:
    return {
        "write_speed_mbps": _test_write_speed(),
    }
