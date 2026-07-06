---
name: pdf-page-image-markdown
description: Use this skill when converting page-numbered PDF images into faithful Markdown pages for the LLM Wiki, especially from raw/assets/{document}/pages/page-001.png into raw/assets/{document}/md/page-001.md. Use when transcribing page by page, checking quality one page at a time with a human before moving to the next page, and optionally creating a combined pages Markdown.
---

# PDF Page Image Markdown

PDF を高解像度ページ画像へ変換した後、各ページ画像を原文忠実な Markdown にするためのスキル。主処理は自宅環境では Codex CLI + VS Code、会社環境では GitHub Copilot Enterprise + VS Code を想定する。ChatGPT 5.5 / M365 Copilot は補助・比較・難ページ対応として扱う。

## 適用条件

- `raw/assets/{資料名}/pages/page-001.png` のようなページ画像を Markdown 化する。
- PDF 由来の画像を、要約ではなく原文忠実な中間 Markdown にする。
- ページ単位で処理し、後で結合・レビュー・wiki ingest に使う。
- 1ページずつ Markdown 化し、各ページを人間が確認してから次ページへ進めたい。
- 表、脚注、図表キャプション、数式、縦書き、スキャン PDF などの崩れを確認したい。

## 出力先

ページ単位 Markdown:

```text
raw/assets/{資料名}/md/page-001.md
raw/assets/{資料名}/md/page-002.md
```

結合版 Markdown:

```text
raw/assets/{資料名}/{資料名}.pages.md
```

ページ画像が未作成なら、先に以下を実行する。

```text
python scripts/pdf_to_page_images.py raw/inbox/{資料名}.pdf --dpi 400
```

PDF からページ画像を作る前段の判断・命名・検証は `pdf-to-page-images` スキルに従う。

## 変換ルール

- 画像を正とし、見えている内容だけを Markdown 化する。
- 要約、補足、言い換え、推測、翻訳をしない。
- 原文の語句、記号、数字、単位、句読点を可能な限り保持する。
- 見出し階層は `#`, `##`, `###` で再現する。
- 箇条書き、番号付きリスト、インデントを再現する。
- ヘッダー、フッター、ページ番号は本文と無関係なら除外する。
- 章タイトル、資料名、節名として意味があるヘッダーは残す。
- 表は可能な限り Markdown テーブルにする。崩れる場合は HTML `<table>` を使う。
- 図や画像は `![Figure: 簡潔な説明](../figures/page-001-fig-1.png)` のようなプレースホルダーにする。
- 図中の読めるテキスト、軸ラベル、凡例、キャプションは抽出する。
- 図の保存と取り扱い: 図はページ Markdown と同じ資料フォルダ内の `figures/` に保存する（例: `raw/assets/{資料名}/figures/page-001-fig-1.png`）。可能であればユーザーが手動でクロップして保存することを標準とする。ファイル名は `page-XXX-fig-N.png` とし、Markdown からは相対パス `../figures/...` を使う。自動クロップを使用する場合は、必ず人が校正すること。
- 数式は可能な限り LaTeX にする。判読できない文字は `[illegible]` とする。
- 脚注は本文後に `## Footnotes` として置く。
- 判読不能箇所は `[illegible]`、ほぼ読めるが一部不確かな場合のみ `[unclear: ...]` とする。

## ページブロック形式

各ページ Markdown の先頭:

```md
<!-- page: 001 source: ../pages/page-001.png -->
```

`source` には、ページ Markdown から見た元画像の相対パスを入れる。絶対パスは使わない。

各ページ Markdown の末尾:

```md
<!-- check: table_ok=true/false; reading_order_ok=true/false; uncertain_parts=... -->
```

`uncertain_parts` がない場合は `none` とする。

## ワークフロー

1. 対象画像を1ページずつ確認する。
2. `raw/assets/{資料名}/md/` を作成する。
3. ページごとに `page-001.md` 形式で保存する。
4. 表・数式・図・脚注・固有名詞・数値は元画像と突き合わせる。
5. そのページの Markdown を人間に提示し、原文忠実性を確認してもらう。
6. 修正があればそのページだけ直し、OK が出てから次ページへ進む。
7. 不確実な箇所は本文に混ぜず、`[illegible]` / `[unclear: ...]` / check コメントで明示する。
8. 必要に応じてページ単位 Markdown を `{資料名}.pages.md` に結合する。
9. wiki に反映する場合は、`wiki/sources/`、関連 `concepts` / `entities`、`wiki/index.md`、`wiki/log.md` へ統合する。

## レビュー記録（Reviewed metadata）

- 各ページの末尾にある `<!-- check: ... -->` コメントにレビュー結果のメタデータを付与してください。フォーマット例:

	<!-- check: table_ok=true; reading_order_ok=true; uncertain_parts=none; reviewed_by=yutaro.yoda; reviewed_on=2026-05-27; review_status=approved -->

- `reviewed_by`: レビュー実施者の識別子（例: `yutaro.yoda`）
- `reviewed_on`: レビュー日（YYYY-MM-DD）
- `review_status`: `approved` / `needs_update` などのステータス

- 自動処理やCIで変更を検出しやすくするため、このコメントは1行で完結させてください。

## 品質チェック

- 読み順が自然か。
- 見出し階層が過剰または不足していないか。
- 表のセル対応、空欄、注記、単位が崩れていないか。
- 図表キャプションと本文参照が対応しているか。
- 脚注・参考文献が本文に混ざっていないか。
- 数値、固有名詞、日付、引用符が原文どおりか。
- 肩書き、所属、括弧内注記、年齢、社名などの小さな文字を落としていないか。
- 判読不能箇所を推測で埋めていないか。
- Markdown として後続 ingest しやすい構造になっているか。
