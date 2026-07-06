#!/usr/bin/env python
"""Merge page Markdown files into a single file while preserving page boundaries."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_INPUT_DIR = Path.cwd()
DEFAULT_OUTPUT_NAME = "merged.md"
DEFAULT_PATTERN = "page-*.md"


def page_number(path: Path) -> int:
    match = re.search(r"page-(\d+)(?:_[^.]+)?\.md$", path.name)
    if not match:
        raise ValueError(f"ページ番号を解釈できません: {path.name}")
    return int(match.group(1))


def validate_input_dir(input_dir: Path) -> None:
    if not input_dir.exists():
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    if not input_dir.is_dir():
        raise ValueError(f"入力先がディレクトリではありません: {input_dir}")


def collect_page_files(input_dir: Path, pattern: str) -> list[Path]:
    files = [path for path in input_dir.glob(pattern) if path.is_file()]
    files.sort(key=page_number)
    return files


def build_merged_markdown(files: list[Path]) -> str:
    if not files:
        raise ValueError("結合対象の md ファイルが見つかりません。")

    parts: list[str] = []
    for index, path in enumerate(files):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"空の md ファイルです: {path}")

        page_no = page_number(path)
        parts.append(
            "\n".join(
                [
                    f"<!-- source: {path.name} -->",
                    f"## Page {page_no:03d}",
                    "",
                    content,
                ]
            )
        )

        if index < len(files) - 1:
            parts.append("---")

    return "\n\n".join(parts).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="指定したフォルダ内のページ Markdown を 1 つの Markdown に統合します。"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"入力ディレクトリ。既定値: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=f"出力ファイル。未指定時は入力ディレクトリ内の {DEFAULT_OUTPUT_NAME}",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help=f"対象ファイルの glob パターン。既定値: {DEFAULT_PATTERN}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ファイルは書き出さず、対象件数だけ表示します。",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    input_dir = args.input_dir
    validate_input_dir(input_dir)

    output_path = args.output if args.output else input_dir / DEFAULT_OUTPUT_NAME
    if output_path.parent != input_dir:
        raise ValueError("出力先は入力ディレクトリと同じ階層にしてください。")

    files = [path for path in collect_page_files(input_dir, args.pattern) if path.resolve() != output_path.resolve()]
    merged_markdown = build_merged_markdown(files)

    if args.dry_run:
        print(f"Input dir: {input_dir}")
        print(f"Matched files: {len(files)}")
        print(f"Output: {output_path}")
        return 0

    output_path.write_text(merged_markdown, encoding="utf-8")

    print(f"Input dir: {input_dir}")
    print(f"Matched files: {len(files)}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)