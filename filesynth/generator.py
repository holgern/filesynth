"""File generation logic for filesynth."""

import os
import random
from pathlib import Path
from typing import Any, Optional, Union

from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)

from .manifest import Manifest
from .utils import ensure_dir, format_size, generate_filename, generate_folder_structure


class FileGenerator:
    """Generate random test files with various patterns."""

    CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks

    def __init__(
        self,
        output_dir: Union[str, Path],
        size_range: tuple[int, int],
        count: int,
        depth: int = 0,
        folders_per_level: int = 2,
        prefix: str = "testfile",
        extension: str = ".bin",
        pattern: str = "random",
        naming: str = "sequential",
        distribution: str = "balanced",
        seed: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialize file generator.

        Args:
            output_dir: Output directory for generated files
            size_range: Tuple of (min_size, max_size) in bytes
            count: Number of files to generate
            depth: Folder depth level
            folders_per_level: Number of folders at each level
            prefix: Filename prefix
            extension: File extension
            pattern: Content pattern (random, zeros, ones, repeating, sequential)
            naming: Naming scheme (sequential, uuid, timestamp)
            distribution: File distribution (balanced, random)
            seed: Random seed for reproducibility
            verbose: Show detailed progress
        """
        self.output_dir = Path(output_dir)
        self.size_range = size_range
        self.count = count
        self.depth = depth
        self.folders_per_level = folders_per_level
        self.prefix = prefix
        self.extension = extension
        self.pattern = pattern
        self.naming = naming
        self.distribution = distribution
        self.seed = seed
        self.verbose = verbose

        # Set random seed if provided
        if seed is not None:
            random.seed(seed)

        # Generate folder structure
        self.folders = generate_folder_structure(depth, folders_per_level)

        # Statistics
        self.stats = {"files_created": 0, "total_bytes": 0, "folders_created": set()}

    def _get_file_size(self) -> int:
        """Get random file size within range."""
        min_size, max_size = self.size_range
        if min_size == max_size:
            return min_size
        return random.randint(min_size, max_size)

    def _get_folder_path(self, file_index: int) -> str:
        """
        Get folder path for a file based on distribution strategy.

        Args:
            file_index: Index of the file

        Returns:
            Relative folder path
        """
        if not self.folders or self.folders == [""]:
            return ""

        if self.distribution == "balanced":
            # Evenly distribute files across folders
            folder_index = file_index % len(self.folders)
            return self.folders[folder_index]

        elif self.distribution == "random":
            # Randomly select folder
            return random.choice(self.folders)

        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")

    def _generate_content(
        self,
        size: int,
        progress: Optional[Progress] = None,
        task: Optional[TaskID] = None,
    ) -> bytes:
        """
        Generate file content based on pattern.

        Args:
            size: Size of content in bytes
            progress: Rich progress instance
            task: Progress task ID

        Returns:
            Generated content as bytes
        """
        if self.pattern == "random":
            # Generate random bytes in chunks
            content = bytearray()
            remaining = size

            while remaining > 0:
                chunk_size = min(self.CHUNK_SIZE, remaining)
                content.extend(os.urandom(chunk_size))
                remaining -= chunk_size

                if progress and task:
                    progress.update(task, advance=chunk_size)

            return bytes(content)

        elif self.pattern == "zeros":
            if progress and task:
                progress.update(task, advance=size)
            return b"\x00" * size

        elif self.pattern == "ones":
            if progress and task:
                progress.update(task, advance=size)
            return b"\xff" * size

        elif self.pattern == "repeating":
            # Repeating pattern: "ABCD"
            pattern_bytes = b"ABCD"
            repeat_count = (size // len(pattern_bytes)) + 1
            content = (pattern_bytes * repeat_count)[:size]
            if progress and task:
                progress.update(task, advance=size)
            return content

        elif self.pattern == "sequential":
            # Sequential bytes: 0x00 to 0xFF repeated
            pattern_bytes = bytes(range(256))
            repeat_count = (size // len(pattern_bytes)) + 1
            content = (pattern_bytes * repeat_count)[:size]
            if progress and task:
                progress.update(task, advance=size)
            return content

        else:
            raise ValueError(f"Unknown pattern: {self.pattern}")

    def _write_file_chunked(
        self,
        file_path: Path,
        size: int,
        progress: Optional[Progress] = None,
        file_task: Optional[TaskID] = None,
        byte_task: Optional[TaskID] = None,
    ) -> None:
        """
        Write file content in chunks.

        Args:
            file_path: Path to write file
            size: Size of file in bytes
            progress: Rich progress instance
            file_task: File progress task ID
            byte_task: Byte progress task ID
        """
        with open(file_path, "wb") as f:
            if self.pattern == "random":
                # Generate and write in chunks
                remaining = size
                while remaining > 0:
                    chunk_size = min(self.CHUNK_SIZE, remaining)
                    chunk = os.urandom(chunk_size)
                    f.write(chunk)
                    remaining -= chunk_size

                    if progress and byte_task:
                        progress.update(byte_task, advance=chunk_size)

            elif self.pattern in ["zeros", "ones"]:
                # Fast write for simple patterns
                byte_value = b"\x00" if self.pattern == "zeros" else b"\xff"
                remaining = size

                while remaining > 0:
                    chunk_size = min(self.CHUNK_SIZE, remaining)
                    f.write(byte_value * chunk_size)
                    remaining -= chunk_size

                    if progress and byte_task:
                        progress.update(byte_task, advance=chunk_size)

            elif self.pattern in ["repeating", "sequential"]:
                # Pattern-based write
                if self.pattern == "repeating":
                    pattern_bytes = b"ABCD"
                else:  # sequential
                    pattern_bytes = bytes(range(256))

                remaining = size
                while remaining > 0:
                    chunk_size = min(self.CHUNK_SIZE, remaining)
                    repeat_count = (chunk_size // len(pattern_bytes)) + 1
                    chunk = (pattern_bytes * repeat_count)[:chunk_size]
                    f.write(chunk)
                    remaining -= chunk_size

                    if progress and byte_task:
                        progress.update(byte_task, advance=chunk_size)

        if progress and file_task:
            progress.update(file_task, advance=1)

    def generate(
        self,
        manifest_path: Optional[Union[str, Path]] = None,
        checksum_algorithm: str = "sha256",
    ) -> Manifest:
        """
        Generate all files.

        Args:
            manifest_path: Path to save manifest (optional)
            checksum_algorithm: Checksum algorithm for manifest

        Returns:
            Manifest object
        """
        # Create output directory
        ensure_dir(self.output_dir)

        # Calculate total size for progress
        sum(self._get_file_size() for _ in range(self.count))

        # Reset random seed if provided (for consistent size generation)
        if self.seed is not None:
            random.seed(self.seed)

        # Initialize manifest
        manifest = None
        if manifest_path:
            manifest = Manifest(manifest_path)
            manifest.set_config(
                {
                    "size_range": f"{self.size_range[0]}-{self.size_range[1]}",
                    "size_range_human": (
                        f"{format_size(self.size_range[0])}"
                        f"-{format_size(self.size_range[1])}"
                    ),
                    "count": self.count,
                    "depth": self.depth,
                    "folders_per_level": self.folders_per_level,
                    "pattern": self.pattern,
                    "naming": self.naming,
                    "distribution": self.distribution,
                    "seed": self.seed,
                    "checksum_algorithm": checksum_algorithm,
                }
            )

        # Create progress display
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("{task.completed}/{task.total} files"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[size]}"),
            TimeRemainingColumn(),
        ) as progress:
            file_task = progress.add_task(
                "[cyan]Generating files...", total=self.count, size=format_size(0)
            )

            # Generate each file
            for i in range(self.count):
                # Get file size
                file_size = self._get_file_size()

                # Get folder path
                folder_path = self._get_folder_path(i)

                # Create folder if needed
                if folder_path:
                    full_folder_path = self.output_dir / folder_path
                    ensure_dir(full_folder_path)
                    self.stats["folders_created"].add(folder_path)

                # Generate filename
                filename = generate_filename(
                    self.prefix, i, self.extension, self.naming, self.count
                )
                relative_path = (
                    os.path.join(folder_path, filename) if folder_path else filename
                )
                full_path = self.output_dir / relative_path

                # Write file
                self._write_file_chunked(
                    full_path, file_size, progress, file_task, None
                )

                # Update statistics
                self.stats["files_created"] += 1
                self.stats["total_bytes"] += file_size

                # Update progress
                progress.update(file_task, size=format_size(self.stats["total_bytes"]))

                # Add to manifest
                if manifest:
                    manifest.add_file(relative_path, full_path, checksum_algorithm)

        # Finalize manifest
        if manifest:
            manifest.finalize(self.output_dir)
            manifest.save()

        return manifest

    def get_stats(self) -> dict[str, Any]:
        """
        Get generation statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "files_created": self.stats["files_created"],
            "total_bytes": self.stats["total_bytes"],
            "total_size_human": format_size(self.stats["total_bytes"]),
            "folders_created": len(self.stats["folders_created"]),
            "output_directory": str(self.output_dir.absolute()),
        }
