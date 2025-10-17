"""
Utility helpers for file I/O and safe temp handling.
"""
import os
import tempfile
from typing import Tuple


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def temp_paths(prefix: str, suffix: str = "") -> Tuple[str, str]:
    base = next(tempfile._get_candidate_names())  # deterministic enough for demo
    return (f"temp_{prefix}_{base}{suffix}", f"temp_{prefix}_{base}_out{suffix}")


def file_sizes_equal(path_a: str, path_b: str) -> bool:
    try:
        return os.path.getsize(path_a) == os.path.getsize(path_b)
    except OSError:
        return False


