"""Hardware description and peak-memory sampling using only the standard library.

Everything returns None / "not measured" when it cannot be measured; nothing is estimated.
Peak figures are SYSTEM-WIDE (all processes), sampled every `interval` seconds, so short spikes
between samples can be missed. They are indicative, not a per-process profile.
"""

import contextlib
import ctypes
import os
import platform
import shutil
import subprocess
import threading
import time


def system_memory_total_used_mb() -> tuple[float, float] | None:
    """(total_mb, used_mb) where used = total - available."""
    try:
        if platform.system() == "Linux":
            info = {}
            with open("/proc/meminfo") as handle:
                for line in handle:
                    key, value = line.split(":", 1)
                    info[key] = float(value.split()[0]) / 1024
            return info["MemTotal"], info["MemTotal"] - info["MemAvailable"]
        if platform.system() == "Windows":

            class Status(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = Status()
            status.dwLength = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))  # type: ignore[attr-defined]
            total = status.ullTotalPhys / 1048576
            return total, total - status.ullAvailPhys / 1048576
    except Exception:
        return None
    return None


def gpu_info() -> list[dict] | None:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    rows = []
    for line in out.strip().splitlines():
        name, total, used, driver = [part.strip() for part in line.split(",")]
        rows.append({"name": name, "memory_total_mb": float(total), "memory_used_mb": float(used), "driver": driver})
    return rows


def system_info() -> dict:
    memory = system_memory_total_used_mb()
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "cpu_logical_cores": os.cpu_count(),
        "ram_total_mb": round(memory[0]) if memory else "not measured",
        "gpus": gpu_info() or "none detected (nvidia-smi not available); AMD/Intel/Apple GPUs not probed",
    }


class PeakSampler(contextlib.AbstractContextManager):
    def __init__(self, interval: float = 0.25):
        self.interval = interval
        self.peak_system_used_mb: float | None = None
        self.baseline_system_used_mb: float | None = None
        self.peak_gpu_used_mb: float | None = None
        self.samples = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self) -> None:
        memory = system_memory_total_used_mb()
        if memory:
            used = memory[1]
            self.peak_system_used_mb = max(self.peak_system_used_mb or 0.0, used)
            if self.baseline_system_used_mb is None:
                self.baseline_system_used_mb = used
        gpus = gpu_info()
        if gpus:
            used = sum(g["memory_used_mb"] for g in gpus)
            self.peak_gpu_used_mb = max(self.peak_gpu_used_mb or 0.0, used)
        self.samples += 1

    def _run(self) -> None:
        while not self._stop.is_set():
            self._sample()
            time.sleep(self.interval)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=5)
        self._sample()
        return False

    def summary(self) -> dict:
        def r(value):
            return round(value) if value is not None else "not measured"

        return {
            "baseline_system_used_mb": r(self.baseline_system_used_mb),
            "peak_system_used_mb": r(self.peak_system_used_mb),
            "peak_gpu_used_mb": r(self.peak_gpu_used_mb),
            "samples": self.samples,
            "note": "System-wide, sampled; not a per-process profile.",
        }
