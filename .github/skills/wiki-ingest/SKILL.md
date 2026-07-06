---
name: wiki-ingest
description: Use this skill when running ingest for the LLM Wiki: reading a source, classifying it, extracting claims at the right depth, merging or creating source/concept/entity pages, maintaining backlinks, and updating index/log with human approval.
---

# Wiki Ingest

LLM Wiki の ingest を、分類駆動かつ merge 優先で安定実行するためのスキル。`AGENTS.md` のコアルールを前提に、ingest 実行時にだけ詳細手順をロードする。

## 目的

- `Read -> Classify -> Extract -> Update/Create pages -> Cross-link -> Update index/log` を固定順序で実行する。
- 既存ページの再利用と merge を優先し、重複ページを避ける。
- document classification に応じて抽出深度を変える。
- page 先頭の one-line summary、source 参照、双方向 backlink をそろえる。
- 構造化できる観察事実がある場合は、`db/schema.sql` に沿って `db/knowledge.duckdb` の更新候補を整理する。

## 実行前チェック

1. `wiki/index.md` を読み、関連しそうな source / concept / entity / analysis を洗い出す。
2. 既存ページ名と用語表記を確認し、正規の概念名・固有名詞表記を決める。
3. `raw/` は編集しない。必要な入力が PDF の場合は、既存のページ画像化・page Markdown 化フローを先に済ませる。
4. DB 更新が関係する場合は、`db/schema.sql` と `db/README.md` を読み、既存の `db/knowledge.duckdb` があるか確認する。

## Step-by-step

### 1. Read

- 対象ソースと、必要なら対応する page Markdown を読む。
- 長文資料では章立て・節構造・図表・数値・固有名詞を先に把握する。

### 2. Classify

以下のいずれに近いかを判定する。

- `research_paper`
- `proposal`
- `meeting_notes`
- `book_chapter`
- `web_article`
- `video_summary`
- `tweet_or_short_post`
- `dataset`
- `image`
- `other`

### 3. Set extraction depth

- `research_paper` / `proposal` / `book_chapter`: セクションごとに主要 claim、方法、数値、結論、制約を抽出する。
- `meeting_notes`: 決定事項、未決事項、アクション、発言主体、日時を優先する。
- `web_article` / `video_summary`: 主張、根拠、引用可能な事実、再利用価値のある論点に絞る。
- `tweet_or_short_post`: 主な洞察、立場、明示された事実だけを抽出する。過剰な概念展開はしない。
- `dataset` / `image`: 変数、軸、凡例、注記、観察可能な事実を優先する。

### 4. Triage

承認前に以下をまとめる。

- document classification
- 抽出深度の方針
- 主なテーマ・キーポイント
- 影響を受ける既存ページ
- 新規作成候補ページ
- merge 候補ページ
- DB 更新候補。対象テーブル、キー、追加・更新・競合候補を分ける。
- 注意すべき矛盾、未確定点、命名の衝突

### 5. Extract

- 主要 claim を箇条書きで抽出する。
- claim には、可能な限り根拠 source または page / raw 参照を付ける。
- 競合する記述は、解消せずに `競合` `未確定` として保持する。
- 数値、分類、日付、関係性などは、`sources` / `entities` / `observations` / `relationships` のどれに入るかを整理する。
- DB に入れる候補には、`source_id`、単位、信頼度、競合状態をできるだけ添える。

### 6. Update DB when approved

- 人間の承認後にだけ DB を更新する。
- 標準 DB は `db/knowledge.duckdb` とする。
- スキーマは `db/schema.sql` を正とする。
- 既存値と競合する値は削除・上書きせず、`conflict_status` を使う。
- DuckDB が未導入または DB 更新を実行できない場合は、DB 更新候補を wiki / log に残し、未実行であることを明示する。

### 7. Update/Create pages

- source summary は `wiki/sources/_source_template.md` を使う。
- concept は `wiki/concepts/_concept_template.md` を使う。
- entity は `wiki/entities/_entity_template.md` を使う。
- 既存ページがあれば原則 merge を優先する。
- 新規作成は、既存ページへ自然に統合できないときだけ行う。
- すべてのページ先頭に one-line summary を置く。

### 8. Cross-link

- 関連概念・人物・資料へ `[[Wikilinks]]` を張る。
- 新規ページを作ったときは、必要な既存ページ側にも戻り導線を足して backlinks を双方向で維持する。
- 用語統一を優先し、別名・略称は `aliases` か本文冒頭で吸収する。

### 9. Update index/log

- `wiki/index.md` にカテゴリ別目次、1 行 summary、必要メタデータを追加または更新する。
- `wiki/log.md` に `## [YYYY-MM-DD] ingest | タイトル` 形式で追記する。
- DB を更新した場合は、対象 DB、テーブル、追加・更新件数、未解決の競合を log に残す。

## ページ構造ルール

- frontmatter を必ず入れる。
- page 先頭に one-line summary を置く。
- `TL;DR` を置く。
- 主要 claim は source 参照可能にする。
- `Related Links` と `Provenance` を置く。
- `Last Updated` を更新する。

## 命名ルール

- concept: `wiki/concepts/概念名.md`
- person entity: `wiki/entities/Firstname-Lastname.md`
- その他 entity: 既存ページの代表表記に合わせる。
- 既存ページと表記差がある場合は、新規作成より先に merge 先を検討する。

## 品質チェック

- `wiki/index.md` から辿れるか。
- 1 行 summary だけで関連性を判断できるか。
- 新規 page が既存 page の重複になっていないか。
- backlinks が片方向で終わっていないか。
- claim に出典があるか。
- 競合や未確定点が黙って上書きされていないか。
- DB 行が source / raw へ辿れるか。
- wiki ページと DB ID の対応が必要な場合、frontmatter に残っているか。
