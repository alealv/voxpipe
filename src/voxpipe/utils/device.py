"""Device detection for PyTorch."""

from __future__ import annotations

import torch


def get_best_device() -> torch.device:
    """Detect and return the best available compute device.

    Returns:
        torch.device for MPS (Apple Silicon), CUDA, or CPU.
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def device_name(device: torch.device) -> str:
    """Return human-readable device name.

    Args:
        device: PyTorch device.

    Returns:
        Human-readable description.
    """
    match device.type:
        case "mps":
            return "Apple Silicon GPU (MPS)"
        case "cuda":
            return "NVIDIA GPU (CUDA)"
        case _:
            return "CPU"
