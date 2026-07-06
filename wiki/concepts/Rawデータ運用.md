---
type: concept
title: Rawデータ運用
created: 2026-05-26
updated: 2026-06-07
tags:
  - raw-data
  - ingest
  - provenance
  - structured-data
summary: raw 配下の一次資料を編集せず保持し、ingest と provenance 管理へつなげる運用ルール。
---

# Rawデータ運用

> One-line summary: raw 配下の一次資料を編集せず保持し、ingest と provenance 管理へつなげる運用ルール。

## TL;DR

`raw/` は一次資料の保管庫であり、LLM は既存ファイルを編集しない。新しい資料は原則 `raw/inbox/` に置き、ingest 後に `raw/sources/` へ移す。CSV、Excel、JSON、Parquet などの元データは `raw/data/` に置き、古い版や廃止版は `raw/archives/` に保持する。画像や添付など、本文資料を補助する素材は `raw/assets/` に置く。資料の種類ごとに、保存先、ingest 観点、wiki / DB 反映先、Artifact 化の要否を判断する。

## 基本フロー

1. `raw/inbox/` に未処理資料を置く。
2. `ingest [filename]` で Triage-first ingest を開始する。
3. 影響範囲、更新候補、矛盾や注意点を確認する。
4. 承認後、必要に応じて `db/knowledge.duckdb`、`wiki/sources/`、関連する `concepts` / `entities` / `analyses`、`wiki/index.md`、`wiki/log.md` を更新する。
5. ingest 済み資料は `raw/sources/` に保持する。画像・添付素材は必要に応じて `raw/assets/` に置く。

## データ種別ごとの対応

| 種別 | 主な置き場所 | ingest 観点 | 主な反映先 | Artifact 化の条件 |
| --- | --- | --- | --- | --- |
| 論文 / PDF | `raw/inbox/` -> `raw/sources/` | 問題設定、手法、結果、限界、関連研究、引用価値 | `wiki/sources/`, `wiki/concepts/`, `wiki/entities/` | 比較表、研究整理、発表資料として再利用する場合 |
| Web記事 / URLメモ | `raw/inbox/` -> `raw/sources/` | 主張、公開日、著者、一次情報か二次情報か、更新可能性 | `wiki/sources/`, `wiki/concepts/` | 複数記事の比較や時系列整理が必要な場合 |
| 書籍メモ / 読書ノート | `raw/inbox/` -> `raw/sources/` | 著者の主張、概念、引用候補、自分の解釈との差分 | `wiki/sources/`, `wiki/concepts/`, `wiki/analyses/` | 章別要約、読書レポート、概念マップにする場合 |
| 会話ログ / アイデアメモ | `raw/inbox/` -> `raw/sources/` | 仮説、未確定事項、意思決定、後で検証すべき問い | `wiki/analyses/`, `wiki/concepts/` | 研究方針、設計メモ、意思決定記録として残す場合 |
| 表データ / CSV / スプレッドシート | `raw/data/` -> 必要に応じて `raw/archives/` | カラム定義、取得元、前処理有無、欠損、再現性、DB 反映キー | `db/`, `wiki/sources/`, `wiki/entities/`, `wiki/analyses/` | ダッシュボード、集計表、比較レポートにする場合 |
| 画像 / 図 / スクリーンショット | `raw/assets/` | 何を示す素材か、出典、対応する本文資料、再利用可否 | 関連する `sources` / `concepts` / `analyses` | 図解、スライド、HTML表示物で使う場合 |
| コード / 実験ログ | `raw/inbox/` -> `raw/sources/` | 実行条件、入力、出力、パラメータ、再現手順、失敗例 | `wiki/sources/`, `wiki/analyses/`, `wiki/concepts/` | 実験レポート、手順書、検証結果として共有する場合 |

## 判断ルール

- その資料自体が知識の根拠になるなら `raw/inbox/` に置く。
- 本文の補助素材で、単独では知識として扱いにくいものは `raw/assets/` に置く。
- ingest 後も、元資料の内容は `raw/` 側に残す。
- 要約や解釈は `wiki/` に置き、一次資料そのものを書き換えない。
- 後から見て根拠を追えるように、wiki 側には元資料名、取得元、日付、未確定点を残す。
- source summary では、取得元情報を本文の自由記述だけにせず、frontmatter の固定項目として `source_path` `origin_type` `origin_reference` `origin_captured_on` `origin_captured_by` `provenance_status` を持つ。
- 複数資料を統合した整理、印刷・共有・発表に使う整理は [[Artifacts運用]] に従って `artifacts/` 化を検討する。
- 比較・集計できる構造化データは [[構造化データ運用]] に従って `db/` 化を検討する。

## 取得元管理の実務ルール

- URL で再取得できる資料は、`origin_type: url` とし、`origin_reference` に URL を入れる。
- メール添付、チャット添付、共有フォルダ配布物は、`origin_reference` に URL の代わりに「送信者 or 配布元 + 経路 + 識別子」を入れる。
- 紙資料や口頭受領をスキャンしたものは、`origin_type: manual_scan` とし、受領経路とスキャン日時を `Provenance` に残す。
- 取得元が曖昧な場合でも空欄にせず、分かっている範囲を書いたうえで `provenance_status: partial` または `uncertain` を付ける。
- source summary の作成時点で取得元を確定できない場合は、`未解決の問い` に確認事項を残す。

## PDFからMarkdownへの変換方針

PDF は一次資料として `raw/` に保持し、Markdown 化した内容は派生資料として扱う。日本語資料が多い前提では、当面は PDF を高解像度のページ画像へ変換し、VS Code 上の AI エージェントでページ単位 Markdown 化する画像LLM軽量ルートを第一候補として試す。変換時は、単なるテキスト抽出ではなく、見出し構造、段落、表、脚注、ページ番号、図表キャプション、引用、数式、OCR 品質を確認する。

利用環境が分かれる場合は、資料の機密性と利用可能なツールを優先して処理場所を決める。自宅環境では Codex CLI + VS Code、会社環境では GitHub Copilot Enterprise + VS Code を主軸にする。ChatGPT 5.5 / M365 Copilot は補助・比較・難ページ対応に回す。ページ単位 Markdown は `raw/assets/{資料名}/md/page-001.md` のように保存し、必要に応じて `{資料名}.pages.md` に結合する。

標準運用では、Markdown 化はまとめ打ちせず、1 ページずつ作成して人間確認を挟みながら進める。特に初回資料、新しい資料タイプ、表や図が多いページでは、`page-001.md` を確認してから `page-002.md` へ進む。

詳細な比較と判断理由は [[2026-05-26_PDFからMarkdown変換品質]] を参照する。

## 注意点

- Web記事やニュースは更新・削除される可能性があるため、取得日とURLを残す。
- 論文や書籍の断定的な要約では、著者の主張と自分の解釈を混ぜない。
- 会話ログやメモは未確定情報を含みやすいため、仮説、決定事項、保留事項を分ける。
- 表データは、加工済みか未加工かを明示する。可能なら元データと処理後データを混同しない。
- 画像やスクリーンショットは権利や出典が曖昧になりやすいため、再配布・Artifact 利用時に注意する。
- 新情報が既存 wiki と矛盾する場合は上書きせず、「競合」「未確定」として残す。

## Related Links

- [[overview]]
- [[Artifacts運用]]
- [[2026-05-26_PDFからMarkdown変換品質]]

## Provenance

- 2026-05-26 に、`raw/` に置く資料種別ごとの実務フローとして作成。
- 2026-05-26 に、PDF から Markdown へ変換する際の品質観点と環境別の使い分けを追加。
- 2026-05-26 に、画像LLM軽量ルートを第一候補とし、Docling / Marker を拡張候補として位置づけ直した。
- 2026-05-26 に、会社環境では ZIP を使わずページ画像を直接渡す方針に変更。
- 2026-05-26 に、自宅環境は Codex CLI + VS Code、会社環境は GitHub Copilot Enterprise + VS Code を主軸にする方針へ更新。
- 2026-05-26 に、source summary の frontmatter で取得元を管理する固定項目を追加。
- 外部一次資料には基づかない内部運用メモ。

## Last Updated

2026-06-07
