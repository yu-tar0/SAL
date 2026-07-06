#!/usr/bin/env python
"""Render a PDF into page-numbered PNG files for LLM review."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_DPI = 400


def slugify_pdf_name(path: Path) -> str:
    stem = path.stem.strip()
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem)
    stem = re.sub(r"\s+", "_", stem)
    return stem or "document"


def ensure_within(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    if child_resolved != parent_resolved and parent_resolved not in child_resolved.parents:
        raise ValueError(f"出力先が許可ディレクトリ外です: {child_resolved}")


def validate_pdf_path(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF が見つかりません: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"PDF ファイルではありません: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"拡張子が .pdf ではありません: {pdf_path}")


def validate_dpi(dpi: int) -> None:
    if dpi <= 0:
        raise ValueError("--dpi は正の整数で指定してください。")


def build_output_dir(pdf_path: Path, output_root: Path, name: str | None) -> Path:
    document_name = name.strip() if name else slugify_pdf_name(pdf_path)
    if not document_name:
        raise ValueError("--name が空です。")

    output_dir = output_root / document_name / "pages"
    ensure_within(output_dir, output_root)
    return output_dir


def verify_page_outputs(output_dir: Path, page_count: int) -> None:
    expected = [output_dir / f"page-{i:03d}.png" for i in range(1, page_count + 1)]
    missing = [str(path) for path in expected if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(f"ページ欠番または空ファイルを検出しました: {missing[:10]}")


def render_with_pymupdf(pdf_path: Path, output_dir: Path, dpi: int, force: bool) -> int:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF が見つかりません。`python -m pip install pymupdf` を実行してください。"
        ) from exc

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    try:
        page_count = doc.page_count
        if page_count <= 0:
            raise RuntimeError("PDF のページ数が 0 です。")

        for index in range(page_count):
            output_file = output_dir / f"page-{index + 1:03d}.png"
            if output_file.exists() and not force:
                raise FileExistsError(
                    f"出力ファイルが既に存在します: {output_file} "
                    "上書きする場合は --force を指定してください。"
                )

            page = doc.load_page(index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(output_file)

            if not output_file.exists() or output_file.stat().st_size == 0:
                raise RuntimeError(f"画像出力に失敗しました: {output_file}")

        return page_count
    finally:
        doc.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PDF を高解像度 PNG に変換し、page-001.png 形式で保存します。"
    )
    parser.add_argument("pdf", type=Path, help="変換する PDF ファイル")
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"画像化する DPI。既定値: {DEFAULT_DPI}",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("raw") / "assets",
        help="出力ルートディレクトリ。既定値: raw/assets",
    )
    parser.add_argument(
        "--name",
        help="出力サブディレクトリ名。未指定時は PDF ファイル名から生成します。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="既存の page-*.png を上書きします。",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    pdf_path = args.pdf
    validate_pdf_path(pdf_path)
    validate_dpi(args.dpi)

    output_dir = build_output_dir(pdf_path, args.output_root, args.name)
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = render_with_pymupdf(pdf_path, output_dir, args.dpi, args.force)
    verify_page_outputs(output_dir, page_count)

    print(f"PDF: {pdf_path}")
    print(f"Pages: {page_count}")
    print(f"DPI: {args.dpi}")
    print(f"Output: {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
