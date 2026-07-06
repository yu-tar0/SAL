#!/usr/bin/env python
"""Lightweight consistency checks for the LLM Wiki repository."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_DIRS = [
    "raw/inbox",
    "raw/sources",
    "raw/data",
    "raw/archives",
    "raw/assets",
    "wiki/sources",
    "wiki/concepts",
    "wiki/entities",
    "wiki/analyses",
    "artifacts",
    "db",
    "scripts",
]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "wiki/index.md",
    "wiki/overview.md",
    "wiki/log.md",
    "wiki/sources/_source_template.md",
    "wiki/concepts/_concept_template.md",
    "wiki/entities/_entity_template.md",
    "db/schema.sql",
]

WIKILINK_RE = re.compile(r"\[\[([^\]#|]+)(?:[#|][^\]]*)?\]\]")
LOG_HEADING_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] (ingest|query|lint) \| .+")
INDEX_BULLET_PATH_RE = re.compile(r"^-\s+`([^`]+)`:")


@dataclass
class Finding:
    severity: str
    message: str


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "", text)


def collect_wiki_pages(root: Path) -> dict[str, list[Path]]:
    pages: dict[str, list[Path]] = {}
    for path in (root / "wiki").rglob("*.md"):
        pages.setdefault(path.stem, []).append(path)
    return pages


def check_required_paths(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for directory in REQUIRED_DIRS:
        if not (root / directory).is_dir():
            findings.append(Finding("ERROR", f"required directory is missing: {directory}"))
    for file_path in REQUIRED_FILES:
        if not (root / file_path).is_file():
            findings.append(Finding("ERROR", f"required file is missing: {file_path}"))
    return findings


def check_wikilinks(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    pages = collect_wiki_pages(root)
    for path in (root / "wiki").rglob("*.md"):
        text = strip_inline_code(read_text(path))
        for target in WIKILINK_RE.findall(text):
            target = target.strip()
            if target not in pages:
                findings.append(
                    Finding("ERROR", f"{rel(path, root)} links to missing wiki page: [[{target}]]")
                )
            elif len(pages[target]) > 1:
                locations = ", ".join(rel(item, root) for item in pages[target])
                findings.append(
                    Finding("WARN", f"{rel(path, root)} links to ambiguous page [[{target}]]: {locations}")
                )
    return findings


def check_index_paths(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    index_path = root / "wiki" / "index.md"
    if not index_path.exists():
        return findings

    for line in read_text(index_path).splitlines():
        match = INDEX_BULLET_PATH_RE.match(line)
        if not match:
            continue
        candidate = match.group(1)
        if "/" not in candidate and "\\" not in candidate:
            continue
        normalized = candidate.replace("\\", "/")
        if normalized.startswith(("http://", "https://")):
            continue
        if not (root / normalized).exists():
            findings.append(Finding("ERROR", f"wiki/index.md references missing path: {candidate}"))
    return findings


def check_frontmatter(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for directory in ["wiki/sources", "wiki/concepts", "wiki/entities"]:
        for path in (root / directory).glob("*.md"):
            if path.name.startswith("_"):
                continue
            text = read_text(path)
            if not text.startswith("---\n"):
                findings.append(Finding("ERROR", f"{rel(path, root)} is missing YAML frontmatter"))
            if "## Related Links" not in text:
                findings.append(Finding("WARN", f"{rel(path, root)} is missing Related Links section"))
            if "## Provenance" not in text:
                findings.append(Finding("WARN", f"{rel(path, root)} is missing Provenance section"))
            if "## Last Updated" not in text:
                findings.append(Finding("WARN", f"{rel(path, root)} is missing Last Updated section"))
    return findings


def check_log_format(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    log_path = root / "wiki" / "log.md"
    if not log_path.exists():
        return findings

    for line_number, line in enumerate(read_text(log_path).splitlines(), start=1):
        if line.startswith("## ") and not LOG_HEADING_RE.match(line):
            findings.append(
                Finding("WARN", f"wiki/log.md:{line_number} has non-standard heading: {line}")
            )
    return findings


def run_checks(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_required_paths(root))
    findings.extend(check_wikilinks(root))
    findings.extend(check_index_paths(root))
    findings.extend(check_frontmatter(root))
    findings.extend(check_log_format(root))
    return findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM Wiki の基本整合性を検査します。")
    parser.add_argument("--root", type=Path, default=Path("."), help="リポジトリルート")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    findings = run_checks(root)

    if not findings:
        print("OK: no wiki lint findings")
        return 0

    for finding in findings:
        print(f"{finding.severity}: {finding.message}")

    return 1 if any(finding.severity == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
