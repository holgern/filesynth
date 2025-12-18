"""Tests for file generator."""

import tempfile
from pathlib import Path

from filesynth.generator import FileGenerator


class TestFileGenerator:
    """Tests for FileGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = FileGenerator(
                output_dir=tmpdir,
                size_range=(1024, 2048),
                count=10,
                depth=2,
                folders_per_level=3,
                prefix="test",
                extension=".bin",
                pattern="random",
                naming="sequential",
                distribution="balanced",
                seed=42,
            )

            assert generator.output_dir == Path(tmpdir)
            assert generator.size_range == (1024, 2048)
            assert generator.count == 10
            assert generator.depth == 2
            assert generator.folders_per_level == 3
            assert generator.prefix == "test"
            assert generator.extension == ".bin"
            assert generator.pattern == "random"
            assert generator.naming == "sequential"
            assert generator.distribution == "balanced"
            assert generator.seed == 42

    def test_generate_flat_structure(self):
        """Test generating files with flat structure (depth=0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=5,
                depth=0,
                pattern="zeros",
            )

            generator.generate()

            # Check files were created
            assert output_dir.exists()
            files = list(output_dir.glob("*.bin"))
            assert len(files) == 5

            # Check file sizes
            for file in files:
                assert file.stat().st_size == 100

            # Check statistics
            stats = generator.get_stats()
            assert stats["files_created"] == 5
            assert stats["total_bytes"] == 500
            assert stats["folders_created"] == 0

    def test_generate_with_depth(self):
        """Test generating files with folder depth."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=8,
                depth=2,
                folders_per_level=2,
                pattern="zeros",
            )

            generator.generate()

            # Check files were created
            files = list(output_dir.rglob("*.bin"))
            assert len(files) == 8

            # Check folder structure exists
            folders = [f for f in output_dir.rglob("*") if f.is_dir()]
            assert len(folders) > 0

            # Check statistics
            stats = generator.get_stats()
            assert stats["files_created"] == 8
            assert stats["folders_created"] > 0

    def test_generate_with_size_range(self):
        """Test generating files with size range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 200),
                count=10,
                depth=0,
                pattern="zeros",
                seed=42,  # For reproducibility
            )

            generator.generate()

            # Check files have varying sizes
            files = list(output_dir.glob("*.bin"))
            sizes = [f.stat().st_size for f in files]

            # All sizes should be within range
            assert all(100 <= size <= 200 for size in sizes)

            # With seed, we should have some variation
            # (not all files should be same size)
            assert len(set(sizes)) > 1

    def test_generate_pattern_zeros(self):
        """Test generating files with zeros pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=1,
                depth=0,
                pattern="zeros",
            )

            generator.generate()

            # Read file and check content
            files = list(output_dir.glob("*.bin"))
            content = files[0].read_bytes()

            assert len(content) == 100
            assert all(b == 0 for b in content)

    def test_generate_pattern_ones(self):
        """Test generating files with ones pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=1,
                depth=0,
                pattern="ones",
            )

            generator.generate()

            # Read file and check content
            files = list(output_dir.glob("*.bin"))
            content = files[0].read_bytes()

            assert len(content) == 100
            assert all(b == 255 for b in content)

    def test_generate_pattern_repeating(self):
        """Test generating files with repeating pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=1,
                depth=0,
                pattern="repeating",
            )

            generator.generate()

            # Read file and check content
            files = list(output_dir.glob("*.bin"))
            content = files[0].read_bytes()

            assert len(content) == 100
            # Check pattern repeats (ABCD)
            assert content[:4] == b"ABCD"
            assert content[4:8] == b"ABCD"

    def test_generate_pattern_sequential(self):
        """Test generating files with sequential pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(300, 300),
                count=1,
                depth=0,
                pattern="sequential",
            )

            generator.generate()

            # Read file and check content
            files = list(output_dir.glob("*.bin"))
            content = files[0].read_bytes()

            assert len(content) == 300
            # Check sequential pattern (0-255 repeated)
            assert content[:256] == bytes(range(256))
            assert content[256:260] == bytes(range(4))

    def test_generate_pattern_random(self):
        """Test generating files with random pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(1000, 1000),
                count=1,
                depth=0,
                pattern="random",
            )

            generator.generate()

            # Read file and check content is random
            files = list(output_dir.glob("*.bin"))
            content = files[0].read_bytes()

            assert len(content) == 1000

            # Random data should have good entropy
            # (not all zeros, not all same value)
            unique_bytes = len(set(content))
            assert unique_bytes > 10  # Should have many different byte values

    def test_generate_naming_sequential(self):
        """Test sequential file naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=10,
                depth=0,
                prefix="test",
                naming="sequential",
                pattern="zeros",
            )

            generator.generate()

            files = sorted(output_dir.glob("*.bin"))
            filenames = [f.name for f in files]

            assert "test_01.bin" in filenames
            assert "test_10.bin" in filenames

    def test_generate_naming_uuid(self):
        """Test UUID file naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=3,
                depth=0,
                prefix="test",
                naming="uuid",
                pattern="zeros",
            )

            generator.generate()

            files = list(output_dir.glob("*.bin"))

            # Check all files have UUID-like names
            for file in files:
                assert file.name.startswith("test_")
                assert file.name.endswith(".bin")
                # UUID should make filename longer
                assert len(file.name) > len("test_.bin")

    def test_generate_naming_timestamp(self):
        """Test timestamp file naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=3,
                depth=0,
                prefix="test",
                naming="timestamp",
                pattern="zeros",
            )

            generator.generate()

            files = list(output_dir.glob("*.bin"))

            # Check all files have timestamp in name
            for file in files:
                assert file.name.startswith("test_")
                assert file.name.endswith(".bin")
                # Should contain timestamp pattern (YYYYMMDD_HHMMSS)
                assert "_" in file.name

    def test_generate_distribution_balanced(self):
        """Test balanced file distribution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=8,
                depth=2,
                folders_per_level=2,
                distribution="balanced",
                pattern="zeros",
                seed=42,
            )

            generator.generate()

            # Count files in each folder
            folders = [f for f in output_dir.rglob("*") if f.is_dir()]
            file_counts = []

            for folder in folders:
                files = list(folder.glob("*.bin"))
                if files:
                    file_counts.append(len(files))

            # With balanced distribution, files should be relatively even
            if len(file_counts) > 1:
                assert max(file_counts) - min(file_counts) <= 1

    def test_generate_with_manifest(self):
        """Test generating with manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            manifest_path = Path(tmpdir) / "manifest.json"

            generator = FileGenerator(
                output_dir=output_dir,
                size_range=(100, 100),
                count=5,
                depth=0,
                pattern="zeros",
            )

            manifest = generator.generate(manifest_path, "sha256")

            # Check manifest was created
            assert manifest_path.exists()

            # Check manifest content
            assert manifest is not None
            files = manifest.get_files()
            assert len(files) == 5

            # Check each file has checksum
            for file_entry in files:
                assert "checksum" in file_entry
                assert file_entry["checksum_algorithm"] == "sha256"

    def test_generate_with_seed_reproducibility(self):
        """Test that same seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "output1"
            output_dir2 = Path(tmpdir) / "output2"

            # Generate with same seed
            generator1 = FileGenerator(
                output_dir=output_dir1,
                size_range=(100, 200),
                count=10,
                depth=0,
                pattern="random",
                seed=42,
            )
            generator1.generate()

            generator2 = FileGenerator(
                output_dir=output_dir2,
                size_range=(100, 200),
                count=10,
                depth=0,
                pattern="random",
                seed=42,
            )
            generator2.generate()

            # Check file sizes match (with same seed)
            files1 = sorted(output_dir1.glob("*.bin"))
            files2 = sorted(output_dir2.glob("*.bin"))

            sizes1 = [f.stat().st_size for f in files1]
            sizes2 = [f.stat().st_size for f in files2]

            assert sizes1 == sizes2
