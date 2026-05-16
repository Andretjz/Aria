"""GPU memory helpers — dev only.

These are no-ops when CUDA is unavailable (CPU dev machines, production).
Import freely; they will not raise on non-GPU hosts.
"""
from __future__ import annotations

import gc


def flush_gpu() -> None:
    """Release all cached CUDA tensors and run the Python garbage collector.

    Call this between pipeline passes to reclaim VRAM before loading the
    next model. Safe to call when CUDA is unavailable — becomes a no-op.
    """
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            torch.cuda.synchronize()
    except ImportError:
        gc.collect()


def vram_free_gb() -> float:
    """Return free VRAM in gigabytes, or 0.0 if CUDA is unavailable.

    Returns:
        Free VRAM in GB rounded to two decimal places.
    """
    try:
        import torch
        if torch.cuda.is_available():
            free_bytes, _ = torch.cuda.mem_get_info()
            return round(free_bytes / 1e9, 2)
    except ImportError:
        pass
    return 0.0


def vram_total_gb() -> float:
    """Return total VRAM in gigabytes, or 0.0 if CUDA is unavailable.

    Returns:
        Total VRAM in GB rounded to two decimal places.
    """
    try:
        import torch
        if torch.cuda.is_available():
            _, total_bytes = torch.cuda.mem_get_info()
            return round(total_bytes / 1e9, 2)
    except ImportError:
        pass
    return 0.0


def gpu_info() -> dict:
    """Return a dict with GPU name, total VRAM, and free VRAM.

    Used by the health endpoint to report GPU status.

    Returns:
        Dict with keys: available (bool), name (str), total_gb (float),
        free_gb (float).
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "total_gb": vram_total_gb(),
                "free_gb": vram_free_gb(),
            }
    except ImportError:
        pass
    return {"available": False, "name": None, "total_gb": 0.0, "free_gb": 0.0}
