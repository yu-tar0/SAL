---
name: batch-page-image-markdown
description: Use this skill when converting multiple page images in a specified folder into faithful per-page Markdown files by repeatedly applying the pdf-page-image-markdown skill to every image in sequence without stopping for per-page user confirmation. Use when the user wants reliable batch processing, resumable progress, and one Markdown file produced for each image.
---

# Batch Page Image Markdown

複数のページ画像に対して、ユーザーが普段 `pdf-page-image-markdown` で1ページずつ行っている作業を、Codex が代わりに連続実行するための上位スキル。

目的は「自動OCRパイプラインを作ること」ではなく、「添付画像または指定フォルダ内のページ画像を、1ページずつ視覚確認し、`pdf-page-image-markdown` と同じ品質ルールで Markdown 化し、ページごとの確認待ちで止まらず最後まで進めること」である。

## 適用条件

- ユーザーが「指定フォルダ内の複数画像を順番にMarkdown化したい」と依頼した。
- ユーザーが複数のページ画像を添付し、「これを順番にMarkdown化して」と依頼した。
- `raw/assets/{資料名}/pages/page-001.png` のようなページ画像が複数ある。
- 各画像に対して、原文忠実なページ単位 Markdown を作りたい。
- 実行後に、画像枚数分の `md/page-XXX.md` が揃っている状態にしたい。
- ユーザーが手作業で1ページずつ繰り返している処理を、Codex 側でまとめて代行してほしい。

## 基本方針

- 1枚の画像を Markdown 化する変換ルール、ページブロック形式、品質チェックは必ず `pdf-page-image-markdown` に従う。
- 画像は1ページずつ実際に視覚確認して Markdown 化する。
- ページごとのユーザー確認では停止しない。全ページを処理してからまとめて報告する。
- 標準では、最初のページから順に最後のページまで処理する。
- 画像はファイル名の自然順で処理する。`page-001.png`, `page-002.png` のようなゼロ埋め連番を優先する。
- 添付画像の場合は、ユーザーが指定した順序があればそれを優先し、指定がなければ添付順に処理する。
- 既存の `md/page-XXX.md` がある場合は上書きせず、内容を確認してから再処理する。
- 不確実箇所は本文に混ぜず、各ページの check コメントや `[unclear: ...]` / `[illegible]` に残す。
- manifest は必須ではない。ページ数が多い場合、途中再開が必要な場合、またはユーザーが求めた場合だけ作成する。

## 入力と出力

入力フォルダ例:

```text
raw/assets/{資料名}/pages/
```

出力フォルダ例:

```text
raw/assets/{資料名}/md/
```

各画像の出力例:

```text
raw/assets/{資料名}/pages/page-001.png
raw/assets/{資料名}/md/page-001.md
```

必要に応じた進捗管理ファイル:

```text
raw/assets/{資料名}/md/_batch_manifest.md
```

## ワークフロー

1. ユーザー指定の画像フォルダを確認する。
2. 対象画像を列挙し、自然順に並べる。拡張子は `.png`, `.jpg`, `.jpeg`, `.webp` を対象にする。
3. 出力先 `../md/` を決める。通常は画像フォルダの兄弟ディレクトリ `md/` とする。
4. 出力先がなければ作成する。
5. 既存 Markdown の有無を確認し、処理済み・未処理・要更新を把握する。
6. ページ数が多い、または途中再開が必要な場合だけ `md/_batch_manifest.md` を作成する。
7. 1ページ目から順に、各画像を実際に視覚確認する。
8. 各画像に `pdf-page-image-markdown` の変換ルールを適用して Markdown 化する。
9. 出力ファイルの先頭に `<!-- page: XXX source: ../pages/page-XXX.png -->` を置く。
10. 出力ファイルの末尾に `<!-- check: table_ok=...; reading_order_ok=...; uncertain_parts=...; review_status=auto_generated -->` を置く。
11. ページごとのユーザー確認は行わず、次の画像へ進む。ただし画像が読めない、ページ順が不明、既存ファイル上書きが必要な場合だけ停止して報告する。
12. 全ページ完了後、対象画像数と生成 Markdown 数を照合する。
13. 不確実箇所、欠番、既存ファイルのスキップ、上書きしなかったファイルをまとめて報告する。
14. ユーザーが求めた場合だけ `{資料名}.pages.md` へ結合する。

## 事前チェック

処理開始前に以下を確認する。

- 画像フォルダが存在する。
- 対象画像が1枚以上ある。
- ファイル名からページ番号を抽出できる。抽出できない場合は自然順でよいが、その旨を報告する。
- 出力先 `md/` に既存ファイルがある場合、上書きせず状態を分類する。
- ページ数が多い場合、まとめて報告する単位。指定がなければ最後に一括報告する。
- 画像が大きすぎる、または細部が読めない場合は、DPI を上げて再画像化する候補として報告する。

## Manifest 形式（必要な場合のみ）

`md/_batch_manifest.md` は次の形式にする。

```md
# Batch Page Image Markdown Manifest

- source_pages: `../pages/`
- output_md: `.`
- created: YYYY-MM-DD
- updated: YYYY-MM-DD
- chunk_size: 5

| page | image | markdown | status | notes |
|---|---|---|---|---|
| 001 | `../pages/page-001.png` | `page-001.md` | pending |  |
```

ステータス:

- `pending`: 未処理。
- `done`: Markdown 作成済み。
- `skipped`: 既存ファイルがあり、上書きしていない。
- `needs_review`: 読み取り不確実箇所がある。
- `blocked`: 画像が読めない、ページ順が不明、またはユーザー判断が必要。

## 出力テンプレート

各ページ Markdown は最低限次の形にする。

```md
<!-- page: 001 source: ../pages/page-001.png -->

# （ページ内の最上位見出し）

（画像に見えている本文を原文忠実に Markdown 化する）

<!-- check: table_ok=true/false; reading_order_ok=true/false; uncertain_parts=none; review_status=auto_generated -->
```

## 進捗管理

- 作業開始時に、総ページ数、未処理ページ、既存 Markdown を短く報告する。
- 各ページの処理前に、対象画像と出力先を必要最小限で把握する。
- 各ページの処理後にユーザー確認を求めない。
- 完了時に、作成・更新・スキップした Markdown と不確実箇所をまとめて報告する。
- 途中で中断した場合、次回は既存 Markdown、`review_status`、必要なら `md/_batch_manifest.md` を見て再開位置を判断する。

## 既存 Markdown の扱い

- 既存ファイルがあり、末尾の `review_status=approved` が確認できる場合は原則スキップする。
- `needs_update`、`uncertain_parts` が `none` 以外、または check コメントがない場合は要更新候補として扱う。
- ユーザーが明示的に上書き許可していない場合、既存ファイルは上書きせず完了報告に含める。

## 完了条件

- 対象画像すべてに対応する `md/page-XXX.md` が存在する。
- 各 Markdown にページ先頭コメントと末尾 check コメントがある。
- 自動作成したページには `review_status=auto_generated` または同等の未承認状態がある。
- ページ番号、画像ファイル名、Markdown ファイル名に抜けや重複がない。
- manifest を作った場合は、全ページが `done`、`needs_review`、または `skipped` のいずれかで、`pending` が残っていない。

## 注意点

- 複数ページを処理しても、各ページの内容は画像ごとに独立して変換する。
- 読めない文字、曖昧な表、図中の小さい文字は推測で埋めない。
- ページ順に疑義がある場合は処理前に報告する。
- 画像フォルダの外にある一次資料や `raw/` の既存ファイルは編集しない。
- 画像を見られない実行環境では、本文変換まで完了できない。その場合は空テンプレートだけを量産せず、画像確認が必要であることを報告する。
