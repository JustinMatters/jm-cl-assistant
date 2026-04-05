"""System information tool.

Returns a human-readable summary of the host machine: OS, CPU, RAM,
GPU/VRAM (via ``torch.cuda`` if available), Python version, and loaded
Ollama models.  Uses only stdlib plus optional torch — no extra deps.
"""

from __future__ import annotations

import platform
import sys

import ollama

from src.tools.registry import REGISTRY, ToolDefinition


def _ram_info() -> tuple[float, float]:
    """Return total and available RAM in GiB.

    Uses ``/proc/meminfo`` on Linux and ``psutil`` on other platforms
    when available; falls back to zeros if neither is accessible.

    Returns:
        ``(total_gib, available_gib)``
    """
    # Try psutil first (may already be installed as a transitive dep)
    try:
        import psutil  # type: ignore[import-not-found]

        vm = psutil.virtual_memory()
        return vm.total / 1024**3, vm.available / 1024**3
    except ImportError:
        pass

    # Stdlib fallback: /proc/meminfo (Linux)
    try:
        meminfo: dict[str, int] = {}
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                key, _, value = line.partition(":")
                meminfo[key.strip()] = int(value.split()[0])  # kB
        total = meminfo.get("MemTotal", 0) / 1024**2
        avail = meminfo.get("MemAvailable", 0) / 1024**2
        return total, avail
    except OSError:
        pass

    return 0.0, 0.0


def _gpu_info() -> list[str]:
    """Return GPU name and VRAM info for each CUDA device.

    Returns an empty list if torch is not installed or CUDA is
    unavailable.

    Returns:
        List of strings such as
        ``["GPU 0: NVIDIA RTX 3090 — 24.0 GiB total, 20.1 GiB free"]``.
    """
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return []

    if not torch.cuda.is_available():
        return []

    lines: list[str] = []
    for i in range(torch.cuda.device_count()):
        name = torch.cuda.get_device_name(i)
        total = torch.cuda.get_device_properties(i).total_memory / 1024**3
        free = (
            torch.cuda.get_device_properties(i).total_memory
            - torch.cuda.memory_allocated(i)
        ) / 1024**3
        lines.append(
            f"GPU {i}: {name} — {total:.1f} GiB total, {free:.1f} GiB free"
        )
    return lines


def _ollama_models() -> list[str]:
    """Return names of locally pulled Ollama models.

    Returns an empty list if Ollama is unreachable.

    Returns:
        List of model name strings.
    """
    try:
        return [m.model for m in ollama.list().models]
    except Exception:
        return []


def system_info() -> str:
    """Return a plain-text summary of the host system.

    Includes OS, CPU, RAM, GPU/VRAM, Python version, and loaded Ollama
    models.

    Returns:
        A formatted multi-line string.
    """
    uname = platform.uname()
    cpu = uname.processor or uname.machine or "unknown"
    cpu_count = ""
    try:
        import os

        logical = os.cpu_count() or 0
        cpu_count = f" ({logical} logical cores)"
    except Exception:
        pass

    total_ram, avail_ram = _ram_info()
    gpu_lines = _gpu_info()
    models = _ollama_models()

    lines: list[str] = [
        f"OS: {uname.system} {uname.release} ({uname.machine})",
        f"CPU: {cpu}{cpu_count}",
    ]
    if total_ram > 0:
        lines.append(
            f"RAM: {avail_ram:.1f} GiB free / {total_ram:.1f} GiB total"
        )
    else:
        lines.append("RAM: unavailable")

    if gpu_lines:
        lines.extend(gpu_lines)
    else:
        lines.append("GPU: not available or torch not installed")

    lines.append(
        f"Python: {sys.version_info.major}.{sys.version_info.minor}"
        f".{sys.version_info.micro}"
    )
    if models:
        lines.append(f"Ollama models: {', '.join(models)}")
    else:
        lines.append("Ollama models: none loaded or Ollama unreachable")

    return "\n".join(lines)


def _handle_sysinfo_query(query: str) -> str:
    """Handle a raw system info query.

    Args:
        query: The raw user query (ignored — always returns full info).

    Returns:
        A formatted system info string.
    """
    return system_info()


REGISTRY.register(
    ToolDefinition(
        name="sysinfo",
        router_tier="sysinfo",
        label="Tool: system info",
        description=(
            "queries about the host system: OS, CPU, RAM, GPU, VRAM, "
            "Python version, or loaded Ollama models"
        ),
        examples=[
            "what OS am I running",
            "how much RAM do I have",
            "how much VRAM is free",
            "what GPU do I have",
            "what Ollama models are loaded",
        ],
        default_enabled=True,
        min_tier="trivial_ollama",
        approach="A",
        callable=_handle_sysinfo_query,
        category="system",
    )
)
