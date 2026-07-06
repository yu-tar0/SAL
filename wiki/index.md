# Index

## Overview

- [[overview]]: 研究テーマ全体の概観と現在の焦点。

## Sources

- `wiki/sources/_source_template.md`: source summary 作成時に使うテンプレート。取得元メタデータの固定項目を含む。

## Concepts

- [[Artifacts運用]]: `wiki/` の知識や必要に応じた `raw` 資料を、Markdown 正本と標準の `web` HTMLとして可視化するための運用概念。`a4` / `slides` は明示依頼時だけ追加する。
- [[Rawデータ運用]]: `raw/` に置く一次資料を種類ごとに扱い分け、ingest・wiki反映・Artifact化へつなげるための運用概念。取得元メタデータの管理方針と PDF から Markdown への変換方針も含む。
- [[構造化データ運用]]: DuckDB による `db/` 層を使い、比較・集計できる定量情報や関係性を `wiki/` と provenance 付きで接続する運用概念。

## Structured Data

- `db/schema.sql`: 標準 DuckDB `db/knowledge.duckdb` の汎用スキーマ。`sources`、`entities`、`observations`、`relationships` を中心に始める。
- `db/README.md`: `raw/`、`db/`、`wiki/`、`artifacts/` の役割分担と DuckDB 初期化方針。

## Maintenance

- `README.md`: LLM Wiki default としての使い始め、ingest、query、DB、Artifact、保守コマンドの入口。
- `AGENTS.md`: Codex / LLM が守る運用ルール。ingest、query、lint、artifacts の基本原則を含む。
- `.gitignore`: Python キャッシュ、ローカル仮想環境、DuckDB 実体・一時ファイル、OS / editor ノイズの除外設定。
- `scripts/lint_wiki.py`: 必須パス、Wikilink、索引パス、主要ページ構造、ログ見出しを確認する軽量 lint。
- `scripts/pdf_to_page_images.py`: PDF を `raw/assets/{資料名}/pages/page-001.png` 形式へ画像化する補助スクリプト。

## Entities

- まだありません。

## Analyses

- [[2026-05-26_PDFからMarkdown変換品質]]: PDF を raw データとして扱う際の Markdown 変換品質、環境別の使い分け、レビュー観点を整理。

## Artifacts

- `artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.md`: 現行 `knowledge.duckdb` の `avant_loader_specs_raw` を直接参照し、AVANT の個別機種 15 台と電動モデルを比較表として整理した Markdown 正本。
- `artifacts/2026-07-02-comparison-avant-loader-specs-current-db/2026-07-02-comparison-avant-loader-specs-current-db.web.html`: 上記 current-db 版比較表のブラウザ閲覧用 HTML。
- `artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.md`: DuckDB に入っている AVANT SAL 仕様を使い、数値レンジ比較と分類比較を 1 ページで確認できるようにした比較表の試作。
- `artifacts/2026-07-02-comparison-avant-loader-specs-prototype/2026-07-02-comparison-avant-loader-specs-prototype.web.html`: 上記試作のブラウザ閲覧用 HTML。
- `artifacts/2026-06-30-summary-sal-birth-evolution-electric/2026-06-30-summary-sal-birth-evolution-electric.md`: SAL の成立背景、多用途化、電動油圧 SAL の構成パターンを整理した Artifact 正本。
- `artifacts/2026-06-30-summary-sal-birth-evolution-electric/2026-06-30-summary-sal-birth-evolution-electric.web.html`: 上記 Artifact のブラウザ閲覧用 HTML。
- `artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.md`: html-artifact スキルの標準出力が `web.html` のみになっていることを確認する試作。
- `artifacts/2026-06-01-summary-artifact-web-default-test/2026-06-01-summary-artifact-web-default-test.web.html`: 上記試作のブラウザ閲覧用HTML。

今後の Artifact は、`md` を内容正本、`web.html` を標準の閲覧入口として扱う。`a4.html` と `slides.html` は明示依頼時だけ追加出力する。生成スキル検証用サンプルは通常の Artifacts 一覧には載せず、`artifacts/samples/` に分離する。
