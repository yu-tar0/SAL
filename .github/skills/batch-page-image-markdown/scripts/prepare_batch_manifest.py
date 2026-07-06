#!/usr/bin/env python
"""Prepare a manifest and optional page Markdown skeletons for batch image transcription."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def natural_key(path: Path) -> list[object]:
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def page_id(path: Path, fallback_index: int) -> str:
    match = re.search(r"page[-_ ]?(\d+)", path.stem, re.IGNORECASE)
    if match:
        return match.group(1).zfill(3)
    match = re.search(r"(\d+)", path.stem)
    if match:
        return match.group(1).zfill(3)
    return str(fallback_index).zfill(3)


def rel_for_md(from_dir: Path, target: Path) -> str:
    return target.resolve().relative_to(from_dir.resolve().parent).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pages_dir", type=Path)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument("--create-skeletons", action="store_true")
    args = parser.parse_args()

    pages_dir = args.pages_dir
    if not pages_dir.exists() or not pages_dir.is_dir():
        raise SystemExit(f"pages_dir not found: {pages_dir}")

    images = sorted(
        [p for p in pages_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS],
        key=natural_key,
    )
    if not images:
        raise SystemExit(f"no page images found in: {pages_dir}")

    md_dir = pages_dir.parent / "md"
    md_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    rows: list[str] = []
    created = 0
    skipped = 0

    for index, image in enumerate(images, start=1):
        pid = page_id(image, index)
        md_name = f"page-{pid}.md"
        md_path = md_dir / md_name
        image_rel = f"../pages/{image.name}"

        if md_path.exists():
            status = "skipped"
            skipped += 1
        else:
            status = "pending"
            if args.create_skeletons:
                md_path.write_text(
                    "\n".join(
                        [
                            f"<!-- page: {pid} source: {image_rel} -->",
                            "",
                            "",
                            "<!-- check: table_ok=false; reading_order_ok=false; uncertain_parts=pending; review_status=auto_generated -->",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )
                created += 1

        rows.append(f"| {pid} | `{image_rel}` | `{md_name}` | {status} |  |")

    manifest = "\n".join(
        [
            "# Batch Page Image Markdown Manifest",
            "",
            "- source_pages: `../pages/`",
            "- output_md: `.`",
            f"- created: {today}",
            f"- updated: {today}",
            f"- chunk_size: {args.chunk_size}",
            "",
            "| page | image | markdown | status | notes |",
            "|---|---|---|---|---|",
            *rows,
            "",
        ]
    )
    (md_dir / "_batch_manifest.md").write_text(manifest, encoding="utf-8")

    print(f"images={len(images)}")
    print(f"manifest={md_dir / '_batch_manifest.md'}")
    print(f"skeletons_created={created}")
    print(f"existing_markdown_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
