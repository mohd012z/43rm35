"""Convert repository diff metadata into a Lola advisory ChangeSet."""

from dataclasses import dataclass
import re
from pathlib import PurePosixPath
from typing import Optional, Tuple

from .dispatch import ChangeSet


SOURCE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".kt", ".kts", ".c", ".cc", ".cpp", ".h", ".hpp"}


@dataclass(frozen=True)
class DiffFile:
    path: str
    patch: Optional[str] = None


@dataclass(frozen=True)
class ChangeExtractionResult:
    status: str
    change_set: ChangeSet
    uncertainties: Tuple[str, ...] = ()


def _source_file(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in SOURCE_SUFFIXES


def _python_functions(patch: str) -> Tuple[str, ...]:
    names = []
    # Git unified diffs often expose the enclosing function in the hunk body
    # as a context line, so inspect context and added definitions but ignore removals.
    pattern = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    for raw_line in patch.splitlines():
        if raw_line.startswith(("---", "+++", "@@", "-")):
            continue
        line = raw_line[1:] if raw_line.startswith(("+", " ")) else raw_line
        match = pattern.match(line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    return tuple(names)


def extract_change_set(
    *,
    base_sha: str,
    reviewed_sha: str,
    files: Tuple[DiffFile, ...],
) -> ChangeExtractionResult:
    """Extract changed paths/functions while explicitly retaining uncertainty."""
    head = reviewed_sha.strip()
    base = base_sha.strip()
    normalized_files = tuple(
        DiffFile(item.path.replace("\\", "/"), item.patch)
        for item in files
        if item.path.strip()
    )

    empty = ChangeSet(reviewed_sha=head, base_sha=base)
    if not head:
        return ChangeExtractionResult("UNBOUND", empty)

    if not normalized_files:
        return ChangeExtractionResult("NO_ACTION", empty)

    changed_files = tuple(item.path for item in normalized_files)
    functions = []
    uncertainties = []

    for item in normalized_files:
        if not _source_file(item.path):
            continue
        if item.patch is None:
            uncertainties.append(f"{item.path}:functions_unknown")
            continue
        if item.path.lower().endswith(".py"):
            for name in _python_functions(item.patch):
                if name not in functions:
                    functions.append(name)
        else:
            # Other source languages remain file-level changes until a language
            # extractor is added; do not pretend function-level scope is known.
            uncertainties.append(f"{item.path}:functions_unknown")

    change_set = ChangeSet(
        reviewed_sha=head,
        base_sha=base,
        changed_files=changed_files,
        changed_functions=tuple(functions),
    )
    status = "EXTRACTED_WITH_UNCERTAINTY" if uncertainties else "EXTRACTED"
    return ChangeExtractionResult(status, change_set, tuple(uncertainties))
