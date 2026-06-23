"""Pre-publication scanner for the RubiMorph source tree and archives."""

from __future__ import annotations

import argparse
import fnmatch
import io
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


PRIVATE_AI_TOOL_MARKER = "co" + "dex"
PRIVATE_MANUSCRIPT_DIR = "novel" + "_sources"

VCS_DIRS = {".git", ".hg", ".svn"}
FORBIDDEN_GENERATED_DIRS = {
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "logs",
    "release",
    "temp",
    "tmp",
}
FORBIDDEN_PRIVATE_DIRS = {
    "ai-work",
    "internal-notes",
    "local-work",
    PRIVATE_MANUSCRIPT_DIR,
    "private-notes",
}
FORBIDDEN_ENV_DIRS = {".cache", ".mypy_cache", ".ruff_cache", ".tox", ".venv", "venv"}
SKIP_DESCENT_DIRS = VCS_DIRS | FORBIDDEN_GENERATED_DIRS | FORBIDDEN_PRIVATE_DIRS | FORBIDDEN_ENV_DIRS
ARCHIVE_FORBIDDEN_DIRS = SKIP_DESCENT_DIRS | {"node_modules"}

FORBIDDEN_FILE_PATTERNS: list[tuple[str, str]] = [
    (".env", "secret configuration file"),
    (".env.*", "secret configuration file"),
    ("*.private", "private file"),
    ("*.private.*", "private file"),
    ("*.local", "local-only file"),
    ("*.local.*", "local-only file"),
    ("*.pyc", "python bytecode cache"),
    ("*.pyo", "python bytecode cache"),
    ("*.pem", "private key or certificate material"),
    ("*.pfx", "private key or certificate material"),
    ("*.p12", "private key or certificate material"),
    ("*.key", "private key material"),
    ("*credential*", "credential material"),
    ("id_rsa", "private key material"),
    ("id_ed25519", "private key material"),
    ("*.worklog", "private work log"),
    ("AI_*.md", "private AI work note"),
]

TEXT_EXTENSIONS = {
    "",
    ".bat",
    ".cmd",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".iss",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".spec",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yml",
    ".yaml",
}

ALLOWED_ACTIONS_PATTERNS = [
    re.compile(r"\$\{\{\s*github\.token\s*\}\}"),
    re.compile(r"\$\{\{\s*secrets\.[A-Za-z_][A-Za-z0-9_]*\s*\}\}"),
]


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str
    line: int | None = None


def build_content_rules() -> list[tuple[str, re.Pattern[str]]]:
    local_path = r"(?i)\bC:\\(?:" + PRIVATE_AI_TOOL_MARKER + r"|GitHub|Users)\\"
    parts = {
        "private_ai_tool_marker": re.escape(PRIVATE_AI_TOOL_MARKER),
        "begin_private_key": r"BEGIN [A-Z ]*PRIVATE KEY",
        "private_key": r"PRIVATE KEY",
        "api_key": r"\bAPI_KEY\b",
        "access_token": r"\bACCESS_TOKEN\b|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9_]+",
        "password_assignment": r"\bPASSWORD\s*=",
        "secret_assignment": r"\bSECRET\s*=",
        "credential_word": r"(?i)\bcredential\b",
        "local_windows_path": local_path,
        "unix_home_path": r"/(?:home|Users)/[^/\s]+/",
        "private_network_ip": r"\b(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[0-1]))\.\d{1,3}\.\d{1,3}\b",
        "high_entropy_secret_assignment": (
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{24,}"
        ),
    }
    return [(name, re.compile(pattern)) for name, pattern in parts.items()]


CONTENT_RULES = build_content_rules()
BINARY_RULE_NAMES = {
    "access_token",
    "begin_private_key",
    "local_windows_path",
    "private_ai_tool_marker",
    "unix_home_path",
}

ALLOWLISTED_RULE_PATHS = {
    "scripts/check_public_tree.py": {
        "api_key",
        "begin_private_key",
        "credential_word",
        "high_entropy_secret_assignment",
        "password_assignment",
        "private_key",
        "secret_assignment",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan RubiMorph files before public release.")
    parser.add_argument(
        "root",
        nargs="?",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root, staging directory, or archive to scan.",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Compatibility option. Generated paths are always reported as findings.",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Scan the filesystem tree instead of Git tracked/planned files.",
    )
    return parser.parse_args()


def normalize(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def git_candidate_files(root: Path) -> list[Path] | None:
    if not (root / ".git").exists():
        return None
    commands = [
        ["git", "-C", str(root), "ls-files"],
        ["git", "-C", str(root), "ls-files", "-o", "--exclude-standard"],
    ]
    files: list[Path] = []
    try:
        for command in commands:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            files.extend(root / line for line in result.stdout.splitlines() if line.strip())
    except (OSError, subprocess.CalledProcessError):
        return None
    return sorted(set(files))


def filesystem_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        dirnames[:] = [dirname for dirname in dirnames if dirname not in SKIP_DESCENT_DIRS]
        for filename in filenames:
            files.append(current / filename)
    return sorted(files)


def candidate_files(root: Path, all_files: bool) -> list[Path]:
    if not all_files:
        files = git_candidate_files(root)
        if files is not None:
            return [path for path in files if not has_forbidden_path_part(path.relative_to(root).parts)]
    return filesystem_candidate_files(root)


def has_forbidden_path_part(parts: tuple[str, ...]) -> bool:
    return any(part in SKIP_DESCENT_DIRS for part in parts[:-1])


def path_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        for dirname in list(dirnames):
            path = current / dirname
            rel = normalize(path, root)
            if PRIVATE_AI_TOOL_MARKER in rel.lower():
                findings.append(Finding(rel, "private_ai_tool_path", "remove before publication"))
            if dirname in FORBIDDEN_GENERATED_DIRS:
                findings.append(Finding(rel, "generated_directory", "remove before publication"))
            elif dirname in FORBIDDEN_PRIVATE_DIRS:
                findings.append(Finding(rel, "private_directory", "remove before publication"))
            elif dirname in FORBIDDEN_ENV_DIRS or dirname == "node_modules":
                findings.append(Finding(rel, "local_environment_directory", "remove before publication"))
        dirnames[:] = [dirname for dirname in dirnames if dirname not in SKIP_DESCENT_DIRS]
        for filename in filenames:
            rel = normalize(current / filename, root)
            if PRIVATE_AI_TOOL_MARKER in rel.lower():
                findings.append(Finding(rel, "private_ai_tool_path", "remove before publication"))
            for pattern, reason in FORBIDDEN_FILE_PATTERNS:
                if fnmatch.fnmatch(filename, pattern):
                    findings.append(Finding(rel, "blocked_filename", reason))
                    break
    return findings


def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\0" in data[:4096]:
        return None
    for encoding in ("utf-8-sig", "utf-16", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def strip_allowed_actions(line: str) -> str:
    result = line
    for pattern in ALLOWED_ACTIONS_PATTERNS:
        result = pattern.sub("", result)
    return result


def is_rule_allowed(path: str, rule: str) -> bool:
    normalized = path.replace("\\", "/").split("!", 1)[-1]
    for allowed_path, rules in ALLOWLISTED_RULE_PATHS.items():
        if normalized == allowed_path or normalized.endswith(f"/{allowed_path}"):
            return rule in rules
    return False


def scan_text(path: str, text: str, *, binary: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    rules = CONTENT_RULES
    if binary:
        rules = [(name, pattern) for name, pattern in CONTENT_RULES if name in BINARY_RULE_NAMES]
    for number, line in enumerate(text.splitlines(), start=1):
        checked = strip_allowed_actions(line)
        for rule, pattern in rules:
            if is_rule_allowed(path, rule):
                continue
            if pattern.search(checked):
                findings.append(Finding(path, rule, "matched forbidden content", number))
    return findings


def binary_strings(data: bytes) -> str:
    ascii_chunks = re.findall(rb"[\x20-\x7e]{5,}", data)
    utf16_chunks = re.findall(rb"(?:[\x20-\x7e]\x00){5,}", data)
    parts = [chunk.decode("ascii", errors="ignore") for chunk in ascii_chunks]
    parts.extend(chunk.decode("utf-16le", errors="ignore") for chunk in utf16_chunks)
    return "\n".join(parts)


def scan_file(path: Path, root: Path) -> list[Finding]:
    rel = normalize(path, root)
    findings: list[Finding] = []
    if path.suffix.lower() == ".zip":
        findings.extend(scan_zip(path, root))
    text = read_text(path) if is_text_like(path) else None
    if text is not None:
        findings.extend(scan_text(rel, text))
        return findings
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [Finding(rel, "read_error", str(exc))]
    extracted = binary_strings(data)
    if extracted:
        findings.extend(scan_text(rel, extracted, binary=True))
    return findings


def archive_path_findings(archive_rel: str, entry_name: str) -> list[Finding]:
    findings: list[Finding] = []
    location = f"{archive_rel}!{entry_name}"
    parts = tuple(part for part in entry_name.replace("\\", "/").split("/") if part)
    if PRIVATE_AI_TOOL_MARKER in entry_name.lower():
        findings.append(Finding(location, "private_ai_tool_path", "remove before publication"))
    path_parts = parts if entry_name.endswith("/") else parts[:-1]
    for part in path_parts:
        if part in ARCHIVE_FORBIDDEN_DIRS:
            findings.append(
                Finding(location, "blocked_archive_directory", "remove before publication")
            )
            break
    base = parts[-1] if parts else ""
    for pattern, reason in FORBIDDEN_FILE_PATTERNS:
        if fnmatch.fnmatch(base, pattern):
            if reason == "python bytecode cache" and is_allowed_runtime_bytecode(location):
                continue
            findings.append(Finding(location, "blocked_archive_entry", reason))
            break
    return findings


def is_allowed_runtime_bytecode(location: str) -> bool:
    normalized = location.replace("\\", "/")
    return (
        normalized.endswith(".pyc")
        and (
            "/_internal/base_library.zip!" in normalized
            or normalized.startswith("_internal/base_library.zip!")
        )
    )


def scan_zip(path: Path, root: Path) -> list[Finding]:
    rel = normalize(path, root)
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [Finding(rel, "zip_read_error", str(exc))]
    return scan_zip_bytes(data, rel)


def scan_zip_bytes(data: bytes, archive_rel: str, depth: int = 0) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                name = info.filename.replace("\\", "/")
                location = f"{archive_rel}!{name}"
                findings.extend(archive_path_findings(archive_rel, name))
                if info.is_dir() or info.file_size > 10_000_000:
                    continue
                entry_data = archive.read(info)
                suffix = Path(name).suffix.lower()
                if suffix == ".zip" and depth < 2:
                    findings.extend(scan_zip_bytes(entry_data, location, depth + 1))
                elif suffix in TEXT_EXTENSIONS:
                    text = None
                    for encoding in ("utf-8-sig", "utf-16", "cp932"):
                        try:
                            text = entry_data.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    if text:
                        findings.extend(scan_text(location, text))
                else:
                    extracted = binary_strings(entry_data)
                    if extracted:
                        findings.extend(scan_text(location, extracted, binary=True))
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append(Finding(archive_rel, "zip_read_error", str(exc)))
    return findings


def scan_archive(path: Path) -> tuple[int, list[Finding]]:
    root = path.parent
    return 1, scan_file(path, root)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if root.is_file():
        files_count, findings = scan_archive(root)
    elif root.is_dir():
        files = candidate_files(root, args.all_files)
        findings = path_findings(root)
        for path in files:
            if path.exists() and path.is_file():
                findings.extend(scan_file(path, root))
        files_count = len(files)
    else:
        print(f"Scan target was not found: {root}", file=sys.stderr)
        return 2

    print(f"Scanned files: {files_count}")
    if findings:
        print("Public tree check failed:")
        for finding in findings:
            location = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
            print(f"- {location}: {finding.rule} ({finding.detail})")
        return 1

    print("Public tree check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
