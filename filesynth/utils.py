"""Utility functions for filesynth."""

import hashlib
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Union


def parse_size(size_str: str) -> int:
    """
    Parse a size string to bytes.

    Args:
        size_str: Size string like "10MB", "1.5GB", "500KB"

    Returns:
        Size in bytes

    Examples:
        >>> parse_size("10MB")
        10485760
        >>> parse_size("1.5GB")
        1610612736
    """
    size_str = size_str.strip().upper()

    # Define units
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    # Match number and unit
    match = re.match(r"^([\d.]+)\s*([KMGT]?B?)$", size_str)
    if not match:
        raise ValueError(
            f"Invalid size format: {size_str}. Use format like '10MB', '1.5GB', etc."
        )

    number, unit = match.groups()

    # Default to bytes if no unit specified
    if not unit or unit == "B":
        unit = "B"

    if unit not in units:
        raise ValueError(
            f"Unknown unit: {unit}. Valid units: {', '.join(units.keys())}"
        )

    try:
        size_bytes = int(float(number) * units[unit])
    except ValueError as e:
        raise ValueError(f"Invalid number: {number}") from e

    if size_bytes < 0:
        raise ValueError("Size cannot be negative")

    return size_bytes


def parse_size_range(size_range: str) -> tuple[int, int]:
    """
    Parse a size range string to tuple of (min_bytes, max_bytes).

    Args:
        size_range: Size range like "1MB-10MB" or single size "5MB"

    Returns:
        Tuple of (min_bytes, max_bytes)

    Examples:
        >>> parse_size_range("1MB-10MB")
        (1048576, 10485760)
        >>> parse_size_range("5MB")
        (5242880, 5242880)
    """
    if "-" in size_range:
        parts = size_range.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid size range: {size_range}. Use format like '1MB-10MB'"
            )

        min_size = parse_size(parts[0].strip())
        max_size = parse_size(parts[1].strip())

        if min_size > max_size:
            raise ValueError(
                f"Min size ({min_size}) cannot be greater than max size ({max_size})"
            )

        return min_size, max_size
    else:
        size = parse_size(size_range)
        return size, size


def format_size(size_bytes: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "10.50 MB"

    Examples:
        >>> format_size(10485760)
        '10.00 MB'
        >>> format_size(1536)
        '1.50 KB'
    """
    size_float = float(size_bytes)
    unit = "B"

    for u in ["B", "KB", "MB", "GB", "TB"]:
        unit = u
        if size_float < 1024.0 or unit == "TB":
            break
        size_float /= 1024.0

    return f"{size_float:.2f} {unit}"


def calculate_checksum(
    file_path: Union[str, Path], algorithm: str = "sha256", chunk_size: int = 8192
) -> str:
    """
    Calculate checksum of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        chunk_size: Read chunk size in bytes

    Returns:
        Hexadecimal checksum string
    """
    if algorithm not in ["md5", "sha1", "sha256"]:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def generate_filename(
    prefix: str,
    index: int,
    extension: str,
    naming: str = "sequential",
    total_count: int = 0,
) -> str:
    """
    Generate a filename based on naming scheme.

    Args:
        prefix: Filename prefix
        index: File index (0-based)
        extension: File extension (with or without dot)
        naming: Naming scheme ('sequential', 'uuid', 'timestamp')
        total_count: Total number of files (for zero-padding)

    Returns:
        Generated filename

    Examples:
        >>> generate_filename("test", 0, ".bin", "sequential", 100)
        'test_001.bin'
        >>> generate_filename("test", 42, ".bin", "timestamp", 1000)
        'test_20231217_143052_0042.bin'
    """
    # Ensure extension starts with dot
    if extension and not extension.startswith("."):
        extension = "." + extension

    if naming == "sequential":
        # Determine padding based on total count
        padding = len(str(total_count)) if total_count > 0 else 3
        return f"{prefix}_{str(index + 1).zfill(padding)}{extension}"

    elif naming == "uuid":
        return f"{prefix}_{uuid.uuid4()}{extension}"

    elif naming == "timestamp":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        padding = len(str(total_count)) if total_count > 0 else 4
        return f"{prefix}_{timestamp}_{str(index + 1).zfill(padding)}{extension}"

    else:
        raise ValueError(f"Unknown naming scheme: {naming}")


def generate_folder_structure(
    depth: int, folders_per_level: int, total_folders: int = 0
) -> list:
    """
    Generate folder paths for a given depth and folders per level.

    Args:
        depth: Maximum folder depth
        folders_per_level: Number of folders at each level
        total_folders: Total folders needed (0 for all combinations)

    Returns:
        List of folder paths (relative)

    Examples:
        >>> generate_folder_structure(2, 2, 0)
        ['folder_01/folder_01', 'folder_01/folder_02',
         'folder_02/folder_01', 'folder_02/folder_02']
    """
    if depth == 0:
        return [""]

    def _generate_paths(current_depth: int, current_path: str = "") -> list:
        if current_depth == 0:
            return [current_path.rstrip("/")]

        paths = []
        for i in range(1, folders_per_level + 1):
            folder_name = f"folder_{str(i).zfill(2)}"
            new_path = (
                os.path.join(current_path, folder_name) if current_path else folder_name
            )
            paths.extend(_generate_paths(current_depth - 1, new_path))

        return paths

    all_paths = _generate_paths(depth)

    # If total_folders specified and less than all possible paths, return subset
    if total_folders > 0 and total_folders < len(all_paths):
        return all_paths[:total_folders]

    return all_paths


def get_file_metadata(file_path: Union[str, Path]) -> dict:
    """
    Get file metadata including size, modification time, and permissions.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with metadata
    """
    stat = os.stat(file_path)

    return {
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat() + "Z",
        "permissions": oct(stat.st_mode)[-3:],
    }


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, create if it doesn't.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
