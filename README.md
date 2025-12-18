# filesynth

Generate synthetic test files for cloud upload testing and benchmarking.


## Overview

**filesynth** is a powerful CLI tool designed to create random binary test files with configurable sizes, folder structures, and content patterns. Perfect for benchmarking and testing cloud storage tools, backup solutions, and data transfer applications.

### Key Features

- 🎲 **Flexible File Generation**: Single size or size ranges (e.g., `1MB-10MB`)
- 📁 **Folder Structures**: Configurable depth and distribution
- 🎨 **Content Patterns**: Random, zeros, ones, repeating, sequential
- 🔐 **Integrity Validation**: SHA256/SHA1/MD5 checksums
- 📋 **Manifest System**: Track files with metadata for validation
- 🧹 **Smart Cleanup**: Remove generated files using manifest
- 🔄 **Reproducible**: Optional seed for consistent generation
- ✨ **Beautiful Output**: Rich terminal UI with progress bars

## Installation

### From Source

```bash
git clone https://github.com/holgern/filesynth.git
cd filesynth
pip install -e .
```

### Using pip (when published)

```bash
pip install filesynth
```

## Quick Start

### Generate Test Files

```bash
# Generate 10 files of 5MB each
filesynth gen -s 5MB -c 10

# Generate 50 files with size range 1MB-10MB
filesynth gen -s 1MB-10MB -c 50 -o testdata

# Generate with folder structure (depth=2, 3 folders per level)
filesynth gen -s 500KB -c 30 -d 2 -f 3 -o nested_data
```

### Validate Files

```bash
# Validate files match manifest checksums
filesynth validate -m testdata_manifest.json
```

### Clean Up

```bash
# Remove generated files (keeps manifest)
filesynth clean -m testdata_manifest.json

# Dry run to see what would be deleted
filesynth clean -m testdata_manifest.json --dry-run

# Remove everything including manifest
filesynth clean -m testdata_manifest.json --all
```

## Usage Examples

### Cloud Upload Testing Workflow

This is the primary use case - testing cloud upload/download and verifying file integrity:

```bash
# 1. Generate test files with manifest
filesynth gen -s 1MB-5MB -c 50 -d 2 -o upload_test

# 2. Upload to cloud using your tool
your-cloud-tool upload upload_test

# 3. Delete local files to save space
filesynth clean -m upload_test_manifest.json

# 4. Download from cloud
your-cloud-tool download downloaded_test

# 5. Validate downloaded files match original checksums
filesynth validate -m upload_test_manifest.json -o downloaded_test
```

### Multiple Test Datasets

The manifest is automatically named to match the output directory, allowing multiple datasets:

```bash
# Create multiple test datasets
filesynth gen -s 100KB -c 10 -o small_files
filesynth gen -s 10MB -c 5 -o large_files
filesynth gen -s 1MB-5MB -c 20 -o mixed_files

# Results in:
# - small_files/ and small_files_manifest.json
# - large_files/ and large_files_manifest.json
# - mixed_files/ and mixed_files_manifest.json

# Validate independently
filesynth validate -m small_files_manifest.json
filesynth validate -m large_files_manifest.json
```

### Content Patterns

Different patterns for testing compression, deduplication, and transfer:

```bash
# Random data (realistic, not compressible)
filesynth gen -s 10MB -c 5 --pattern random -o random_data

# Zeros (highly compressible)
filesynth gen -s 10MB -c 5 --pattern zeros -o zeros_data

# Test compression ratio
filesynth gen -s 10MB -c 5 --pattern ones -o ones_data

# Repeating pattern (partially compressible)
filesynth gen -s 10MB -c 5 --pattern repeating -o repeat_data

# Sequential bytes (0x00 to 0xFF repeated)
filesynth gen -s 10MB -c 5 --pattern sequential -o seq_data
```

### Reproducible Generation

Use seeds for consistent, reproducible test data:

```bash
# Generate with seed
filesynth gen -s 1MB-5MB -c 20 --seed 42 -o reproducible

# Same command with same seed produces identical files
filesynth gen -s 1MB-5MB -c 20 --seed 42 -o reproducible_copy
```

### File Naming Schemes

```bash
# Sequential (default): testfile_001.bin, testfile_002.bin
filesynth gen -s 1MB -c 10 --naming sequential

# UUID: testfile_a3f2b1c4-5d6e-7f8g.bin
filesynth gen -s 1MB -c 10 --naming uuid

# Timestamp: testfile_20231217_143052_001.bin
filesynth gen -s 1MB -c 10 --naming timestamp
```

### Folder Distribution

```bash
# Balanced: Evenly distribute files across folders
filesynth gen -s 1MB -c 100 -d 3 -f 3 --distribution balanced

# Random: Randomly place files (realistic scenario)
filesynth gen -s 1MB -c 100 -d 3 -f 3 --distribution random
```

## Command Reference

### `gen` - Generate Files

```
filesynth gen [OPTIONS]

Options:
  -s, --size TEXT           File size or range (e.g., "10MB", "1MB-10MB") [required]
  -c, --count INTEGER       Number of files to generate [default: 1]
  -d, --depth INTEGER       Folder depth level [default: 0]
  -f, --folders INTEGER     Folders per level [default: 2]
  -o, --output PATH         Output directory [default: ./testdata]
  -p, --prefix TEXT         Filename prefix [default: testfile]
  --pattern TEXT            Content pattern: random, zeros, ones, repeating, sequential
                            [default: random]
  --naming TEXT             Naming scheme: sequential, uuid, timestamp
                            [default: sequential]
  --extension TEXT          File extension [default: .bin]
  --distribution TEXT       Distribution: balanced, random [default: balanced]
  --seed INTEGER            Random seed for reproducibility
  --manifest PATH           Custom manifest path
  --no-manifest             Don't generate manifest
  --checksum TEXT           Algorithm: md5, sha1, sha256 [default: sha256]
  -v, --verbose             Show detailed progress
```

### `validate` - Verify Files

```
filesynth validate [OPTIONS]

Options:
  -m, --manifest PATH       Path to manifest file [required]
  -o, --output PATH         Directory containing files to validate
  --strict                  Stop on first validation error
  -v, --verbose             Show detailed error messages
```

**Exit Codes:**
- `0` - All validations passed
- `1` - Files missing
- `2` - Checksum mismatch
- `3` - Size mismatch

### `clean` - Remove Files

```
filesynth clean [OPTIONS]

Options:
  -m, --manifest PATH       Path to manifest file
  -o, --output PATH         Output directory to clean
  --all                     Remove entire directory including manifest
  --dry-run                 Preview what would be deleted
  -v, --verbose             Show detailed progress
```

## Manifest Format

The manifest is a JSON file containing:

```json
{
  "version": "1.0",
  "generated_at": "2025-12-17T14:30:52Z",
  "generator_config": {
    "size_range": "1048576-10485760",
    "size_range_human": "1.00 MB-10.00 MB",
    "count": 50,
    "depth": 2,
    "pattern": "random",
    "seed": 42,
    "checksum_algorithm": "sha256"
  },
  "summary": {
    "total_files": 50,
    "total_size_bytes": 275456000,
    "total_size_human": "262.68 MB",
    "folder_count": 4,
    "max_depth": 2
  },
  "files": [
    {
      "path": "folder_01/folder_02/testfile_001.bin",
      "size_bytes": 5242880,
      "size_human": "5.00 MB",
      "checksum": "a3f2b1c4d5e6f7g8h9i0...",
      "checksum_algorithm": "sha256",
      "created_at": "2025-12-17T14:30:52Z",
      "modified_at": "2025-12-17T14:30:52Z",
      "permissions": "644"
    }
  ]
}
```

## Use Cases

### 1. Cloud Storage Benchmarking

Test upload/download speeds and verify data integrity:

```bash
# Generate diverse test set
filesynth gen -s 100KB-50MB -c 100 -d 2 -o benchmark

# Upload and measure performance
time your-cloud-tool upload benchmark

# Validate integrity after download
filesynth validate -m benchmark_manifest.json -o downloaded
```

### 2. Backup Solution Testing

Test backup/restore workflows:

```bash
# Create test data
filesynth gen -s 1MB-100MB -c 50 -d 3 -o backup_test

# Run backup
your-backup-tool backup backup_test

# Restore to different location
your-backup-tool restore backup_test_restored

# Verify restoration
filesynth validate -m backup_test_manifest.json -o backup_test_restored
```

### 3. Data Transfer Validation

Verify file transfers (FTP, rsync, etc.):

```bash
# Generate test files
filesynth gen -s 10MB -c 20 -o transfer_test

# Transfer files
rsync -avz transfer_test/ remote:/destination/

# Validate on remote
filesynth validate -m transfer_test_manifest.json -o /destination
```

### 4. Deduplication Testing

Test deduplication with identical files:

```bash
# Create files with zeros pattern (should deduplicate well)
filesynth gen -s 100MB -c 10 --pattern zeros -o dedup_test

# Upload to dedup-enabled storage
your-tool upload dedup_test

# Check storage usage vs. actual file size
```

### 5. Compression Testing

Compare compression ratios with different patterns:

```bash
filesynth gen -s 100MB -c 5 --pattern random -o test_random
filesynth gen -s 100MB -c 5 --pattern zeros -o test_zeros
filesynth gen -s 100MB -c 5 --pattern repeating -o test_repeat

# Test compression on each dataset
tar czf test_random.tar.gz test_random
tar czf test_zeros.tar.gz test_zeros
tar czf test_repeat.tar.gz test_repeat

# Compare compressed sizes
ls -lh *.tar.gz
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/holgern/filesynth.git
cd filesynth
pip install -e ".[dev]"
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=filesynth --cov-report=html

# Run specific test file
pytest tests/test_generator.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Run linting
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Run pre-commit on all files
pre-commit run --all-files
```

## Requirements

- Python 3.9+
- click >= 8.0.0
- rich >= 13.0.0

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Holger Nahrstaedt (nahrstaedt@gmail.com)

## Links

- GitHub: https://github.com/holgern/filesynth
- Issues: https://github.com/holgern/filesynth/issues

## Acknowledgments

Built with:
- [Click](https://click.palletsprojects.com/) - Command-line interface framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
