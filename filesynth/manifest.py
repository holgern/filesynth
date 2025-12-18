"""Manifest management for filesynth."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from .utils import calculate_checksum, format_size, get_file_metadata


class Manifest:
    """Manage manifest files for generated test data."""

    VERSION = "1.0"

    def __init__(self, manifest_path: Union[str, Path]):
        """
        Initialize manifest.

        Args:
            manifest_path: Path to manifest file
        """
        self.manifest_path = Path(manifest_path)
        self.data: dict[str, Any] = {
            "version": self.VERSION,
            "generated_at": None,
            "generator_config": {},
            "summary": {},
            "files": [],
        }

    def set_config(self, config: dict[str, Any]) -> None:
        """
        Set generator configuration.

        Args:
            config: Configuration dictionary
        """
        self.data["generator_config"] = config
        self.data["generated_at"] = datetime.now().isoformat() + "Z"

    def add_file(
        self,
        relative_path: str,
        full_path: Union[str, Path],
        checksum_algorithm: str = "sha256",
    ) -> None:
        """
        Add a file to the manifest.

        Args:
            relative_path: Relative path from output directory
            full_path: Full path to the file
            checksum_algorithm: Checksum algorithm to use
        """
        metadata = get_file_metadata(full_path)
        checksum = calculate_checksum(full_path, checksum_algorithm)

        file_entry = {
            "path": relative_path.replace("\\", "/"),  # Normalize path separators
            "size_bytes": metadata["size_bytes"],
            "size_human": format_size(metadata["size_bytes"]),
            "checksum": checksum,
            "checksum_algorithm": checksum_algorithm,
            "created_at": metadata["created_at"],
            "modified_at": metadata["modified_at"],
            "permissions": metadata["permissions"],
        }

        self.data["files"].append(file_entry)

    def finalize(self, output_dir: Union[str, Path]) -> None:
        """
        Finalize manifest with summary statistics.

        Args:
            output_dir: Output directory containing generated files
        """
        output_dir = Path(output_dir)

        # Calculate summary
        total_size = sum(f["size_bytes"] for f in self.data["files"])

        # Count unique folders
        folders = set()
        for file_entry in self.data["files"]:
            file_path = file_entry["path"]
            folder = os.path.dirname(file_path)
            if folder:
                folders.add(folder)
                # Add all parent folders
                parts = folder.split("/")
                for i in range(1, len(parts)):
                    folders.add("/".join(parts[:i]))

        # Calculate max depth
        max_depth = 0
        for file_entry in self.data["files"]:
            depth = file_entry["path"].count("/")
            max_depth = max(max_depth, depth)

        self.data["summary"] = {
            "total_files": len(self.data["files"]),
            "total_size_bytes": total_size,
            "total_size_human": format_size(total_size),
            "folder_count": len(folders),
            "max_depth": max_depth,
            "output_directory": str(output_dir.absolute()),
        }

    def save(self) -> None:
        """Save manifest to file."""
        # Ensure parent directory exists
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.manifest_path, "w") as f:
            json.dump(self.data, f, indent=2)

    @classmethod
    def load(cls, manifest_path: Union[str, Path]) -> "Manifest":
        """
        Load manifest from file.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Manifest instance

        Raises:
            FileNotFoundError: If manifest file doesn't exist
            ValueError: If manifest format is invalid
        """
        manifest_path = Path(manifest_path)

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        with open(manifest_path) as f:
            data = json.load(f)

        # Validate manifest structure
        required_keys = [
            "version",
            "generated_at",
            "generator_config",
            "summary",
            "files",
        ]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Invalid manifest: missing key '{key}'")

        manifest = cls(manifest_path)
        manifest.data = data

        return manifest

    def get_files(self) -> list[dict[str, Any]]:
        """
        Get list of files in manifest.

        Returns:
            List of file entries
        """
        return self.data["files"]

    def get_summary(self) -> dict[str, Any]:
        """
        Get manifest summary.

        Returns:
            Summary dictionary
        """
        return self.data["summary"]

    def get_config(self) -> dict[str, Any]:
        """
        Get generator configuration.

        Returns:
            Configuration dictionary
        """
        return self.data["generator_config"]


class ManifestValidator:
    """Validate files against a manifest."""

    def __init__(self, manifest: Manifest, base_dir: Optional[Union[str, Path]] = None):
        """
        Initialize validator.

        Args:
            manifest: Manifest to validate against
            base_dir: Base directory (overrides manifest output_directory)
        """
        self.manifest = manifest

        # Determine base directory
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Try to get from manifest summary
            output_dir = manifest.get_summary().get("output_directory")
            if output_dir:
                self.base_dir = Path(output_dir)
            else:
                # Default to manifest file's parent directory
                self.base_dir = manifest.manifest_path.parent

        self.results = {
            "total_files": 0,
            "files_found": 0,
            "files_missing": 0,
            "size_matches": 0,
            "size_mismatches": 0,
            "checksum_matches": 0,
            "checksum_mismatches": 0,
            "errors": [],
        }

    def validate(self, strict: bool = False) -> bool:
        """
        Validate all files in manifest.

        Args:
            strict: If True, stop on first error

        Returns:
            True if all validations passed, False otherwise
        """
        files = self.manifest.get_files()
        self.results["total_files"] = len(files)

        for file_entry in files:
            relative_path = file_entry["path"]
            full_path = self.base_dir / relative_path

            # Check if file exists
            if not full_path.exists():
                self.results["files_missing"] += 1
                self.results["errors"].append(
                    {
                        "type": "missing",
                        "path": relative_path,
                        "message": f"File not found: {relative_path}",
                    }
                )
                if strict:
                    return False
                continue

            self.results["files_found"] += 1

            # Check file size
            actual_size = full_path.stat().st_size
            expected_size = file_entry["size_bytes"]

            if actual_size == expected_size:
                self.results["size_matches"] += 1
            else:
                self.results["size_mismatches"] += 1
                msg = f"Size mismatch: expected {expected_size}, got {actual_size}"
                self.results["errors"].append(
                    {
                        "type": "size_mismatch",
                        "path": relative_path,
                        "message": msg,
                    }
                )
                if strict:
                    return False
                continue  # Don't check checksum if size is wrong

            # Check checksum
            algorithm = file_entry.get("checksum_algorithm", "sha256")
            actual_checksum = calculate_checksum(full_path, algorithm)
            expected_checksum = file_entry["checksum"]

            if actual_checksum == expected_checksum:
                self.results["checksum_matches"] += 1
            else:
                self.results["checksum_mismatches"] += 1
                msg = (
                    f"Checksum mismatch: expected {expected_checksum}, "
                    f"got {actual_checksum}"
                )
                self.results["errors"].append(
                    {
                        "type": "checksum_mismatch",
                        "path": relative_path,
                        "message": msg,
                    }
                )
                if strict:
                    return False

        # Validation passes if all files found, sizes match, and checksums match
        return (
            self.results["files_missing"] == 0
            and self.results["size_mismatches"] == 0
            and self.results["checksum_mismatches"] == 0
        )

    def get_results(self) -> dict[str, Any]:
        """
        Get validation results.

        Returns:
            Results dictionary
        """
        return self.results

    def get_exit_code(self) -> int:
        """
        Get exit code based on validation results.

        Returns:
            Exit code:
                0 = success
                1 = files missing
                2 = checksum mismatch
                3 = size mismatch
        """
        if self.results["files_missing"] > 0:
            return 1
        elif self.results["checksum_mismatches"] > 0:
            return 2
        elif self.results["size_mismatches"] > 0:
            return 3
        else:
            return 0
