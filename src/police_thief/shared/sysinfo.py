"""Machine specification for the Step-0 computational-fairness declaration.

Before the first move each agent declares its hardware - operating system, CPU
cores and frequency, memory, graphics accelerator - alongside its language
model, code version, team name and mini-game number. The league's normalization
rewards algorithmic efficiency over raw compute, so the declaration must be
honest and is cryptographically sealed (rulebook ch. 5.5).
"""

from __future__ import annotations

import os
import platform
from typing import Any


def _cpu_frequency_mhz() -> float:
    """Best-effort CPU frequency; zero when the platform hides it."""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as handle:
            for line in handle:
                if line.lower().startswith("cpu mhz"):
                    return round(float(line.split(":")[1]), 1)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def _total_ram_gb() -> float:
    """Total physical memory in gigabytes, zero when undetectable."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return round(pages * page_size / (1024**3), 2)
    except (ValueError, OSError, AttributeError):
        return 0.0


def _gpu_description() -> str:
    """A best-effort GPU description; honest 'none detected' otherwise.

    League play runs on plain laptops; a missing accelerator is the common
    case and reporting it plainly is exactly what fairness wants.
    """
    for path in ("/proc/driver/nvidia/version",):
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.readline().strip()[:80]
        except OSError:
            continue
    return "none detected"


def hardware_spec() -> dict[str, Any]:
    """The machine specification the Step-0 declaration seals."""
    return {
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_cores": os.cpu_count() or 0,
        "cpu_mhz": _cpu_frequency_mhz(),
        "ram_gb": _total_ram_gb(),
        "gpu": _gpu_description(),
    }
