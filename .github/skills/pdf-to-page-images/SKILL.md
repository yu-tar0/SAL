---
name: pdf-to-page-images
description: Use this skill when rendering PDFs in this LLM Wiki into numbered page PNG images with scripts/pdf_to_page_images.py, especially before page-by-page visual review, transcription, OCR checking, or pdf-page-image-markdown processing. Use for PDF files under raw/inbox or raw/sources that need outputs such as raw/assets/{document}/pages/page-001.png.
---

# PDF To Page Images

PDF を `scripts/pdf_to_page_images.py` で高解像度のページ画像へ変換するための、この LLM Wiki 専用スキル。

## Inputs

- 対象 PDF は原則として `raw/inbox/` または `raw/sources/` に置く。
- `raw/` 配下の一次資料は編集しない。変換結果は `raw/assets/` 配下に新規作成する。
- PDF 名が長い、曖昧、または日本語で後続処理しにくい場合は `--name` で短い識別子を指定する。

## Command

標準実行:

```powershell
python scripts\pdf_to_page_images.py raw\inbox\資料.pdf --dpi 400
```

出力名を明示する場合:

```powershell
python scripts\pdf_to_page_images.py raw\inbox\資料.pdf --dpi 400 --name short-document-name
```

既存の `page-*.png` を上書きする場合のみ:

```powershell
python scripts\pdf_to_page_images.py raw\inbox\資料.pdf --dpi 400 --name short-document-name --force
```

## Outputs

既定の出力先:

```text
raw/assets/{document}/pages/page-001.png
raw/assets/{document}/pages/page-002.png
```

実行後は標準出力の `Pages` と、実ファイル数を照合する。ページ欠番や空ファイルがある場合、スクリプトはエラーにする。

## Workflow

1. 対象 PDF のパスを確認する。
2. 後続処理で使いやすい資料名を決め、必要なら `--name` を使う。
3. `python scripts\pdf_to_page_images.py ... --dpi 400` を実行する。
4. 出力先 `raw/assets/{document}/pages/` の `page-*.png` 件数を確認する。
5. 必要に応じて代表ページを `view_image` で確認する。
6. Markdown 化する場合は `pdf-page-image-markdown` または `batch-page-image-markdown` に進む。

## Failure Handling

- `PyMuPDF が見つかりません` と出た場合は、依存関係の追加が必要であることをユーザーに伝える。
- 出力ファイルが既に存在する場合は、内容確認なしに `--force` を使わない。
- PDF が壊れている、暗号化されている、またはページ数が 0 の場合は、変換不能として報告する。
- 変換結果が巨大になる場合は、DPI を下げる前に、後続の視認・転記精度への影響を説明する。

## Wiki Integration

- この処理は ingest そのものではなく、PDF ingest 前の準備工程として扱う。
- 画像化しただけでは `wiki/log.md` へ記録しなくてよい。画像化を使って ingest、Markdown 化、Artifact 作成まで進めた場合は該当ワークフローのログに含める。
- 後続の source summary では、原本 PDF を `source_path` に記録し、必要ならページ画像フォルダを `Provenance` に補足する。
