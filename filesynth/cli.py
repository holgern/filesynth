"""Command-line interface for filesynth."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .generator import FileGenerator
from .manifest import Manifest, ManifestValidator
from .utils import format_size, parse_size_range

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """
    filesynth - Generate synthetic test files for upload testing.

    Create random binary test files with configurable sizes, folder structures,
    and content patterns. Perfect for benchmarking and testing cloud storage tools.
    """
    pass


@main.command()
@click.option(
    "-s",
    "--size",
    required=True,
    help='File size (e.g., "10MB") or range (e.g., "1MB-10MB")',
)
@click.option(
    "-c",
    "--count",
    type=int,
    default=1,
    help="Number of files to generate [default: 1]",
)
@click.option(
    "-d", "--depth", type=int, default=0, help="Folder depth level [default: 0]"
)
@click.option(
    "-f",
    "--folders",
    type=int,
    default=2,
    help="Number of folders per level [default: 2]",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="./testdata",
    help="Output directory [default: ./testdata]",
)
@click.option(
    "-p", "--prefix", default="testfile", help="Filename prefix [default: testfile]"
)
@click.option(
    "--pattern",
    type=click.Choice(["random", "zeros", "ones", "repeating", "sequential"]),
    default="random",
    help="Content pattern [default: random]",
)
@click.option(
    "--naming",
    type=click.Choice(["sequential", "uuid", "timestamp"]),
    default="sequential",
    help="Naming scheme [default: sequential]",
)
@click.option("--extension", default=".bin", help="File extension [default: .bin]")
@click.option(
    "--distribution",
    type=click.Choice(["balanced", "random"]),
    default="balanced",
    help="File distribution across folders [default: balanced]",
)
@click.option("--seed", type=int, help="Random seed for reproducibility")
@click.option(
    "--manifest",
    type=click.Path(),
    help="Path to save manifest [default: OUTPUT_NAME_manifest.json]",
)
@click.option("--no-manifest", is_flag=True, help="Do not generate manifest file")
@click.option(
    "--checksum",
    type=click.Choice(["md5", "sha1", "sha256"]),
    default="sha256",
    help="Checksum algorithm for manifest [default: sha256]",
)
@click.option("-v", "--verbose", is_flag=True, help="Show detailed progress")
def gen(
    size: str,
    count: int,
    depth: int,
    folders: int,
    output: str,
    prefix: str,
    pattern: str,
    naming: str,
    extension: str,
    distribution: str,
    seed: Optional[int],
    manifest: Optional[str],
    no_manifest: bool,
    checksum: str,
    verbose: bool,
) -> None:
    """Generate test files with specified parameters."""
    try:
        # Parse size range
        size_range = parse_size_range(size)

        # Validate parameters
        if count < 1:
            console.print("[red]Error: count must be at least 1[/red]")
            sys.exit(1)

        if depth < 0:
            console.print("[red]Error: depth cannot be negative[/red]")
            sys.exit(1)

        if folders < 1:
            console.print("[red]Error: folders must be at least 1[/red]")
            sys.exit(1)

        # Determine manifest path
        manifest_path = None
        if not no_manifest:
            if manifest:
                manifest_path = Path(manifest)
            else:
                # Default: save manifest beside output directory with matching name
                output_path = Path(output)
                output_name = output_path.name
                manifest_path = output_path.parent / f"{output_name}_manifest.json"

        # Show configuration
        if verbose:
            console.print("\n[bold cyan]Configuration:[/bold cyan]")
            console.print(f"  Output directory: {output}")
            console.print(f"  File count: {count}")
            size_min = format_size(size_range[0])
            size_max = format_size(size_range[1])
            console.print(f"  Size range: {size_min} - {size_max}")
            console.print(f"  Folder depth: {depth}")
            console.print(f"  Folders per level: {folders}")
            console.print(f"  Content pattern: {pattern}")
            console.print(f"  Naming scheme: {naming}")
            console.print(f"  Distribution: {distribution}")
            if seed is not None:
                console.print(f"  Random seed: {seed}")
            if manifest_path:
                console.print(f"  Manifest: {manifest_path}")
            console.print()

        # Create generator
        generator = FileGenerator(
            output_dir=output,
            size_range=size_range,
            count=count,
            depth=depth,
            folders_per_level=folders,
            prefix=prefix,
            extension=extension,
            pattern=pattern,
            naming=naming,
            distribution=distribution,
            seed=seed,
            verbose=verbose,
        )

        # Generate files
        console.print("[bold green]Generating files...[/bold green]\n")
        generator.generate(manifest_path, checksum)

        # Get statistics
        stats = generator.get_stats()

        # Display summary
        console.print("\n[bold green]✓ Generation complete![/bold green]\n")

        table = Table(title="Summary", show_header=False, title_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Files Created", str(stats["files_created"]))
        table.add_row("Total Size", stats["total_size_human"])
        table.add_row("Folders Created", str(stats["folders_created"]))
        table.add_row("Max Depth", str(depth))
        table.add_row("Output Directory", str(stats["output_directory"]))

        if manifest_path:
            table.add_row(
                "Manifest",
                str(
                    manifest_path.absolute()
                    if isinstance(manifest_path, Path)
                    else manifest_path
                ),
            )

        console.print(table)
        console.print()

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@main.command()
@click.option(
    "-m", "--manifest", type=click.Path(exists=True), help="Path to manifest file"
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=True),
    help="Output directory to clean (overrides manifest output_directory)",
)
@click.option(
    "--all",
    "clean_all",
    is_flag=True,
    help="Remove entire directory including manifest",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.option("-v", "--verbose", is_flag=True, help="Show detailed progress")
def clean(
    manifest: Optional[str],
    output: Optional[str],
    clean_all: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Remove generated test files using manifest."""
    try:
        # Load manifest
        if not manifest:
            # Try default location
            manifest = "./manifest.json"

        manifest_path = Path(manifest)

        if not manifest_path.exists():
            console.print(f"[red]Error: Manifest file not found: {manifest_path}[/red]")
            console.print(
                "[yellow]Hint: Use --manifest to specify manifest path[/yellow]"
            )
            sys.exit(1)

        manifest_obj = Manifest.load(manifest_path)

        # Determine base directory
        if output:
            base_dir = Path(output)
        else:
            base_dir = Path(
                manifest_obj.get_summary().get("output_directory", "./testdata")
            )

        # Get files from manifest
        files = manifest_obj.get_files()

        if not files:
            console.print("[yellow]No files to clean (manifest is empty)[/yellow]")
            return

        # Show what will be cleaned
        if dry_run:
            console.print(
                "[bold yellow]Dry run - no files will be deleted[/bold yellow]\n"
            )

        console.print(f"[bold cyan]Cleaning files from:[/bold cyan] {base_dir}")
        console.print(f"[bold cyan]Manifest:[/bold cyan] {manifest_path}\n")

        # Track statistics
        deleted_count = 0
        missing_count = 0
        error_count = 0
        folders_to_remove = set()

        # Delete files
        for file_entry in files:
            relative_path = file_entry["path"]
            full_path = base_dir / relative_path

            if not full_path.exists():
                missing_count += 1
                if verbose:
                    console.print(f"[yellow]⚠ Missing:[/yellow] {relative_path}")
                continue

            try:
                if not dry_run:
                    full_path.unlink()
                deleted_count += 1

                if verbose:
                    console.print(f"[green]✓ Deleted:[/green] {relative_path}")

                # Track folder for potential removal
                folder = full_path.parent
                if folder != base_dir:
                    folders_to_remove.add(folder)

            except Exception as e:
                error_count += 1
                console.print(f"[red]✗ Error deleting {relative_path}: {e}[/red]")

        # Remove empty folders
        if not dry_run and folders_to_remove:
            for folder in sorted(
                folders_to_remove, reverse=True
            ):  # Remove deepest first
                try:
                    if folder.exists() and not any(folder.iterdir()):
                        folder.rmdir()
                        if verbose:
                            rel_folder = folder.relative_to(base_dir)
                            console.print(
                                f"[green]✓ Removed empty folder:[/green] {rel_folder}"
                            )
                except Exception as e:
                    if verbose:
                        console.print(
                            f"[yellow]⚠ Could not remove folder {folder}: {e}[/yellow]"
                        )

        # Remove entire directory if requested
        if clean_all and not dry_run:
            try:
                if base_dir.exists():
                    import shutil

                    shutil.rmtree(base_dir)
                    console.print(f"[green]✓ Removed directory:[/green] {base_dir}")

                # Remove manifest
                if manifest_path.exists():
                    manifest_path.unlink()
                    console.print(f"[green]✓ Removed manifest:[/green] {manifest_path}")

            except Exception as e:
                console.print(f"[red]✗ Error removing directory: {e}[/red]")
                error_count += 1

        # Display summary
        console.print("\n[bold cyan]Cleanup Summary:[/bold cyan]")
        console.print(f"  Files deleted: [green]{deleted_count}[/green]")

        if missing_count > 0:
            console.print(f"  Files missing: [yellow]{missing_count}[/yellow]")

        if error_count > 0:
            console.print(f"  Errors: [red]{error_count}[/red]")

        if dry_run:
            msg = "This was a dry run. Run without --dry-run to actually delete files."
            console.print(f"\n[yellow]{msg}[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


@main.command()
@click.option(
    "-m",
    "--manifest",
    type=click.Path(exists=True),
    required=True,
    help="Path to manifest file",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=True),
    help="Directory containing files to validate (overrides manifest output_directory)",
)
@click.option("--strict", is_flag=True, help="Stop on first validation error")
@click.option("-v", "--verbose", is_flag=True, help="Show detailed progress")
def validate(manifest: str, output: Optional[str], strict: bool, verbose: bool) -> None:
    """Validate files against manifest checksums."""
    try:
        # Load manifest
        manifest_path = Path(manifest)
        manifest_obj = Manifest.load(manifest_path)

        # Create validator
        validator = ManifestValidator(manifest_obj, output)

        # Show configuration
        console.print("[bold cyan]Validating files...[/bold cyan]")
        console.print(f"  Manifest: {manifest_path}")
        console.print(f"  Base directory: {validator.base_dir}")
        console.print(f"  Total files: {len(manifest_obj.get_files())}\n")

        # Validate
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating...", total=None)
            success = validator.validate(strict)
            progress.update(task, completed=True)

        # Get results
        results = validator.get_results()

        # Display results
        console.print("\n[bold cyan]Validation Results:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="right")
        table.add_column("Count", justify="right")

        # Files found
        if results["files_missing"] == 0:
            status = "[green]✓ PASS[/green]"
        else:
            status = "[red]✗ FAIL[/red]"
        table.add_row(
            "Files Present",
            status,
            f"{results['files_found']}/{results['total_files']}",
        )

        # Size matches
        if results["size_mismatches"] == 0:
            status = "[green]✓ PASS[/green]"
        else:
            status = "[red]✗ FAIL[/red]"
        table.add_row(
            "Size Matches",
            status,
            f"{results['size_matches']}/{results['files_found']}",
        )

        # Checksum matches
        if results["checksum_mismatches"] == 0:
            status = "[green]✓ PASS[/green]"
        else:
            status = "[red]✗ FAIL[/red]"
        table.add_row(
            "Checksum Matches",
            status,
            f"{results['checksum_matches']}/{results['files_found']}",
        )

        console.print(table)

        # Show errors if any
        if results["errors"] and verbose:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in results["errors"]:
                console.print(f"  [red]•[/red] {error['message']}")

        # Overall result
        console.print()
        if success:
            console.print("[bold green]✓ Validation: PASSED[/bold green]")
        else:
            console.print("[bold red]✗ Validation: FAILED[/bold red]")

        # Exit with appropriate code
        sys.exit(validator.get_exit_code())

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
