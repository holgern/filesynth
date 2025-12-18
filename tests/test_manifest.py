"""Tests for manifest management."""

import json
import tempfile
from pathlib import Path

import pytest

from filesynth.manifest import Manifest, ManifestValidator


class TestManifest:
    """Tests for Manifest class."""

    def test_manifest_initialization(self):
        """Test manifest initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            assert manifest.manifest_path == manifest_path
            assert manifest.data["version"] == Manifest.VERSION
            assert manifest.data["files"] == []

    def test_set_config(self):
        """Test setting configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            config = {"size": "1MB-10MB", "count": 100, "pattern": "random"}
            manifest.set_config(config)

            assert manifest.data["generator_config"] == config
            assert manifest.data["generated_at"] is not None

    def test_add_file(self):
        """Test adding file to manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.bin"
            test_file.write_bytes(b"Hello, World!")

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            # Add file
            manifest.add_file("test.bin", test_file, "sha256")

            assert len(manifest.data["files"]) == 1
            file_entry = manifest.data["files"][0]

            assert file_entry["path"] == "test.bin"
            assert file_entry["size_bytes"] == 13
            assert "checksum" in file_entry
            assert file_entry["checksum_algorithm"] == "sha256"

    def test_finalize(self):
        """Test finalizing manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            folder = output_dir / "folder_01"
            folder.mkdir()

            file1 = output_dir / "file1.bin"
            file1.write_bytes(b"A" * 100)

            file2 = folder / "file2.bin"
            file2.write_bytes(b"B" * 200)

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            manifest.add_file("file1.bin", file1)
            manifest.add_file("folder_01/file2.bin", file2)

            manifest.finalize(output_dir)

            summary = manifest.data["summary"]
            assert summary["total_files"] == 2
            assert summary["total_size_bytes"] == 300
            assert summary["folder_count"] == 1
            assert summary["max_depth"] == 1

    def test_save_and_load(self):
        """Test saving and loading manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            config = {"count": 10}
            manifest.set_config(config)
            manifest.save()

            assert manifest_path.exists()

            # Load manifest
            loaded_manifest = Manifest.load(manifest_path)

            assert loaded_manifest.data["version"] == Manifest.VERSION
            assert loaded_manifest.data["generator_config"] == config

    def test_load_nonexistent_manifest(self):
        """Test loading nonexistent manifest raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "nonexistent.json"

            with pytest.raises(FileNotFoundError):
                Manifest.load(manifest_path)

    def test_load_invalid_manifest(self):
        """Test loading invalid manifest raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "invalid.json"

            # Write invalid JSON
            with open(manifest_path, "w") as f:
                json.dump({"invalid": "data"}, f)

            with pytest.raises(ValueError, match="Invalid manifest"):
                Manifest.load(manifest_path)

    def test_get_methods(self):
        """Test get methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            config = {"count": 10}
            manifest.set_config(config)

            assert manifest.get_config() == config
            assert manifest.get_files() == []
            assert manifest.get_summary() == {}


class TestManifestValidator:
    """Tests for ManifestValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)

            validator = ManifestValidator(manifest, tmpdir)

            assert validator.manifest == manifest
            assert validator.base_dir == Path(tmpdir)

    def test_validate_all_pass(self):
        """Test validation passes when all files match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create test file
            test_file = output_dir / "test.bin"
            test_content = b"Hello, World!"
            test_file.write_bytes(test_content)

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)
            manifest.add_file("test.bin", test_file, "sha256")
            manifest.finalize(output_dir)
            manifest.save()

            # Validate
            validator = ManifestValidator(manifest, output_dir)
            success = validator.validate()

            assert success is True

            results = validator.get_results()
            assert results["total_files"] == 1
            assert results["files_found"] == 1
            assert results["files_missing"] == 0
            assert results["size_matches"] == 1
            assert results["checksum_matches"] == 1
            assert validator.get_exit_code() == 0

    def test_validate_missing_file(self):
        """Test validation fails when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create test file
            test_file = output_dir / "test.bin"
            test_file.write_bytes(b"Hello, World!")

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)
            manifest.add_file("test.bin", test_file, "sha256")
            manifest.finalize(output_dir)

            # Delete file before validation
            test_file.unlink()

            # Validate
            validator = ManifestValidator(manifest, output_dir)
            success = validator.validate()

            assert success is False

            results = validator.get_results()
            assert results["files_missing"] == 1
            assert results["files_found"] == 0
            assert validator.get_exit_code() == 1

    def test_validate_size_mismatch(self):
        """Test validation fails when file size doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create test file
            test_file = output_dir / "test.bin"
            test_file.write_bytes(b"Hello, World!")

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)
            manifest.add_file("test.bin", test_file, "sha256")
            manifest.finalize(output_dir)

            # Modify file (change size)
            test_file.write_bytes(b"Different content!")

            # Validate
            validator = ManifestValidator(manifest, output_dir)
            success = validator.validate()

            assert success is False

            results = validator.get_results()
            assert results["size_mismatches"] == 1
            assert validator.get_exit_code() == 3

    def test_validate_checksum_mismatch(self):
        """Test validation fails when checksum doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create test file
            test_file = output_dir / "test.bin"
            test_file.write_bytes(b"Hello, World!")

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)
            manifest.add_file("test.bin", test_file, "sha256")
            manifest.finalize(output_dir)

            # Modify file (same size, different content)
            test_file.write_bytes(b"Goodbye World")  # Same length

            # Validate
            validator = ManifestValidator(manifest, output_dir)
            success = validator.validate()

            assert success is False

            results = validator.get_results()
            assert results["checksum_mismatches"] == 1
            assert validator.get_exit_code() == 2

    def test_validate_strict_mode(self):
        """Test strict mode stops on first error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create test files
            file1 = output_dir / "file1.bin"
            file1.write_bytes(b"File 1")

            file2 = output_dir / "file2.bin"
            file2.write_bytes(b"File 2")

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest = Manifest(manifest_path)
            manifest.add_file("file1.bin", file1, "sha256")
            manifest.add_file("file2.bin", file2, "sha256")
            manifest.finalize(output_dir)

            # Delete first file
            file1.unlink()

            # Validate in strict mode
            validator = ManifestValidator(manifest, output_dir)
            success = validator.validate(strict=True)

            assert success is False

            # Should stop after first error
            results = validator.get_results()
            assert results["files_missing"] == 1
