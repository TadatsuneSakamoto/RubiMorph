"""Safe file and directory conversion helpers for RubiMorph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .convert import convert_text_flexible
from .custom_profiles import CustomFormatProfile
from .types import Diagnostic, RenderOptions

TEXT_EXTENSIONS = {".txt", ".md"}


@dataclass(frozen=True)
class FileConversionResult:
    source: Path
    destination: Path
    diagnostics: list[Diagnostic]
    written: bool


def convert_file(
    source: Path,
    destination: Path,
    source_platform: str | None,
    target_platform: str | None,
    options: RenderOptions | None = None,
    dry_run: bool = False,
    source_profile: CustomFormatProfile | None = None,
    target_profile: CustomFormatProfile | None = None,
) -> FileConversionResult:
    """Convert one UTF-8 text file without overwriting the input path."""

    safe_destination = safe_destination_for(source, destination)
    text = source.read_text(encoding="utf-8")
    result = convert_text_flexible(
        text,
        source_platform=source_platform,
        target_platform=target_platform,
        source_profile=source_profile,
        target_profile=target_profile,
        options=options,
    )
    if not dry_run:
        safe_destination.parent.mkdir(parents=True, exist_ok=True)
        safe_destination.write_text(result.output, encoding="utf-8", newline="\n")
    return FileConversionResult(
        source=source,
        destination=safe_destination,
        diagnostics=result.diagnostics,
        written=not dry_run,
    )


def convert_directory(
    input_dir: Path,
    output_dir: Path,
    source_platform: str | None,
    target_platform: str | None,
    options: RenderOptions | None = None,
    dry_run: bool = False,
    source_profile: CustomFormatProfile | None = None,
    target_profile: CustomFormatProfile | None = None,
) -> list[FileConversionResult]:
    """Convert .txt and .md files while preserving subfolder structure."""

    if not input_dir.is_dir():
        raise NotADirectoryError(input_dir)

    results: list[FileConversionResult] = []
    targets = sorted(path for path in input_dir.rglob("*") if path.suffix.lower() in TEXT_EXTENSIONS)
    for source in targets:
        relative = source.relative_to(input_dir)
        destination = output_dir / relative
        results.append(
            convert_file(
                source=source,
                destination=destination,
                source_platform=source_platform,
                target_platform=target_platform,
                options=options,
                dry_run=dry_run,
                source_profile=source_profile,
                target_profile=target_profile,
            )
        )
    return results


def safe_destination_for(source: Path, destination: Path) -> Path:
    try:
        if source.resolve() == destination.resolve():
            return destination.with_name(f"{destination.stem}_converted{destination.suffix}")
    except OSError:
        pass
    return destination
