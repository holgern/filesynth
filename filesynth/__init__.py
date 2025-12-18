"""filesynth - Generate synthetic test files for upload testing."""

__version__ = "0.1.0"

from .cli import main
from .generator import FileGenerator
from .manifest import Manifest, ManifestValidator
from .utils import format_size, parse_size, parse_size_range

__all__ = [
    "main",
    "FileGenerator",
    "Manifest",
    "ManifestValidator",
    "format_size",
    "parse_size",
    "parse_size_range",
]
