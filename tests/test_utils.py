"""Tests for utility functions."""

import os
import tempfile
from pathlib import Path

import pytest

from filesynth.utils import (
    calculate_checksum,
    ensure_dir,
    format_size,
    generate_filename,
    generate_folder_structure,
    get_file_metadata,
    parse_size,
    parse_size_range,
)


class TestParseSize:
    """Tests for parse_size function."""

    def test_parse_bytes(self):
        """Test parsing bytes."""
        assert parse_size("100B") == 100
        assert parse_size("100") == 100

    def test_parse_kilobytes(self):
        """Test parsing kilobytes."""
        assert parse_size("1KB") == 1024
        assert parse_size("10KB") == 10240

    def test_parse_megabytes(self):
        """Test parsing megabytes."""
        assert parse_size("1MB") == 1048576
        assert parse_size("10MB") == 10485760

    def test_parse_gigabytes(self):
        """Test parsing gigabytes."""
        assert parse_size("1GB") == 1073741824
        assert parse_size("2GB") == 2147483648

    def test_parse_terabytes(self):
        """Test parsing terabytes."""
        assert parse_size("1TB") == 1099511627776

    def test_parse_float(self):
        """Test parsing float values."""
        assert parse_size("1.5MB") == 1572864
        assert parse_size("0.5GB") == 536870912

    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        assert parse_size("10mb") == 10485760
        assert parse_size("10MB") == 10485760
        assert parse_size("10Mb") == 10485760

    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        assert parse_size("10 MB") == 10485760
        assert parse_size("  10MB  ") == 10485760

    def test_invalid_format(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("invalid")

        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("10XB")

    def test_invalid_number(self):
        """Test invalid number raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("abcMB")

    def test_negative_size(self):
        """Test negative size raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_size("-10MB")


class TestParseSizeRange:
    """Tests for parse_size_range function."""

    def test_parse_single_size(self):
        """Test parsing single size."""
        min_size, max_size = parse_size_range("10MB")
        assert min_size == 10485760
        assert max_size == 10485760

    def test_parse_size_range(self):
        """Test parsing size range."""
        min_size, max_size = parse_size_range("1MB-10MB")
        assert min_size == 1048576
        assert max_size == 10485760

    def test_parse_range_with_spaces(self):
        """Test parsing range with spaces."""
        min_size, max_size = parse_size_range("1MB - 10MB")
        assert min_size == 1048576
        assert max_size == 10485760

    def test_invalid_range_format(self):
        """Test invalid range format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size range"):
            parse_size_range("1MB-10MB-20MB")

    def test_min_greater_than_max(self):
        """Test min > max raises ValueError."""
        with pytest.raises(
            ValueError, match="Min size.*cannot be greater than max size"
        ):
            parse_size_range("10MB-1MB")


class TestFormatSize:
    """Tests for format_size function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_size(100) == "100.00 B"
        assert format_size(1023) == "1023.00 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.00 KB"
        assert format_size(1536) == "1.50 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1048576) == "1.00 MB"
        assert format_size(10485760) == "10.00 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1073741824) == "1.00 GB"
        assert format_size(2147483648) == "2.00 GB"

    def test_format_terabytes(self):
        """Test formatting terabytes."""
        assert format_size(1099511627776) == "1.00 TB"

    def test_format_zero(self):
        """Test formatting zero."""
        assert format_size(0) == "0.00 B"


class TestCalculateChecksum:
    """Tests for calculate_checksum function."""

    def test_calculate_md5(self):
        """Test calculating MD5 checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path, "md5")
            assert checksum == "65a8e27d8879283831b664bd8b7f0ad4"
        finally:
            os.unlink(temp_path)

    def test_calculate_sha1(self):
        """Test calculating SHA1 checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path, "sha1")
            assert checksum == "0a0a9f2a6772942557ab5355d76af442f8f65e01"
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256(self):
        """Test calculating SHA256 checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path, "sha256")
            assert (
                checksum
                == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            )
        finally:
            os.unlink(temp_path)

    def test_unsupported_algorithm(self):
        """Test unsupported algorithm raises ValueError."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported algorithm"):
                calculate_checksum(temp_path, "invalid")
        finally:
            os.unlink(temp_path)


class TestGenerateFilename:
    """Tests for generate_filename function."""

    def test_sequential_naming(self):
        """Test sequential naming."""
        assert generate_filename("test", 0, ".bin", "sequential", 10) == "test_01.bin"
        assert generate_filename("test", 9, ".bin", "sequential", 10) == "test_10.bin"
        assert (
            generate_filename("test", 99, ".bin", "sequential", 1000) == "test_0100.bin"
        )

    def test_sequential_padding(self):
        """Test sequential naming with padding."""
        assert generate_filename("test", 0, ".bin", "sequential", 100) == "test_001.bin"
        assert (
            generate_filename("test", 0, ".bin", "sequential", 1000) == "test_0001.bin"
        )

    def test_uuid_naming(self):
        """Test UUID naming."""
        filename = generate_filename("test", 0, ".bin", "uuid", 10)
        assert filename.startswith("test_")
        assert filename.endswith(".bin")
        assert len(filename) > len("test_.bin")  # Has UUID

    def test_timestamp_naming(self):
        """Test timestamp naming."""
        filename = generate_filename("test", 0, ".bin", "timestamp", 10)
        assert filename.startswith("test_")
        assert filename.endswith(".bin")
        assert "_01.bin" in filename  # Has index

    def test_extension_without_dot(self):
        """Test extension without dot is handled."""
        assert generate_filename("test", 0, "bin", "sequential", 10) == "test_01.bin"

    def test_empty_extension(self):
        """Test empty extension."""
        assert generate_filename("test", 0, "", "sequential", 10) == "test_01"

    def test_invalid_naming_scheme(self):
        """Test invalid naming scheme raises ValueError."""
        with pytest.raises(ValueError, match="Unknown naming scheme"):
            generate_filename("test", 0, ".bin", "invalid", 10)


class TestGenerateFolderStructure:
    """Tests for generate_folder_structure function."""

    def test_depth_zero(self):
        """Test depth 0 returns empty string."""
        folders = generate_folder_structure(0, 2)
        assert folders == [""]

    def test_depth_one(self):
        """Test depth 1 returns flat folders."""
        folders = generate_folder_structure(1, 2)
        assert len(folders) == 2
        assert "folder_01" in folders
        assert "folder_02" in folders

    def test_depth_two(self):
        """Test depth 2 returns nested folders."""
        folders = generate_folder_structure(2, 2)
        assert len(folders) == 4
        assert os.path.join("folder_01", "folder_01") in folders
        assert os.path.join("folder_01", "folder_02") in folders
        assert os.path.join("folder_02", "folder_01") in folders
        assert os.path.join("folder_02", "folder_02") in folders

    def test_depth_three(self):
        """Test depth 3 returns deeply nested folders."""
        folders = generate_folder_structure(3, 2)
        assert len(folders) == 8

    def test_different_folder_counts(self):
        """Test different folder counts per level."""
        folders = generate_folder_structure(1, 3)
        assert len(folders) == 3

        folders = generate_folder_structure(2, 3)
        assert len(folders) == 9


class TestGetFileMetadata:
    """Tests for get_file_metadata function."""

    def test_get_metadata(self):
        """Test getting file metadata."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Hello, World!")
            temp_path = f.name

        try:
            metadata = get_file_metadata(temp_path)

            assert "size_bytes" in metadata
            assert metadata["size_bytes"] == 13

            assert "modified_at" in metadata
            assert "created_at" in metadata
            assert "permissions" in metadata
        finally:
            os.unlink(temp_path)


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_ensure_dir_creates_directory(self):
        """Test ensure_dir creates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "subdir" / "nested"
            result = ensure_dir(test_path)

            assert test_path.exists()
            assert test_path.is_dir()
            assert result == test_path

    def test_ensure_dir_existing_directory(self):
        """Test ensure_dir with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir)
            result = ensure_dir(test_path)

            assert test_path.exists()
            assert result == test_path
