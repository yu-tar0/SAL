# Structured Data Layer

このディレクトリは、wiki の補助となる構造化データ層です。

標準の DuckDB ファイルは `db/knowledge.duckdb` とします。SQL 定義は `db/schema.sql` に置き、テーブルの追加・削除と同じ変更で必ず同期します。現在の `db/schema.sql` は、ローダー実行時に `knowledge.duckdb` の実テーブルから自動生成されます。

## 現在の構成

- `db/knowledge.duckdb`: 標準 DB。現在は Case SL12 仕様項目一覧の raw テーブル群と、取り込み履歴の `excel_imports` を保持
- `db/schema.sql`: DB 内全テーブルの CREATE 文。ローダーが実行のたびに再生成して同期
- `db/loaders.md`: 入力ファイルとローダー・テーブルの対応表
- `db/scripts/load_excel_raw_to_duckdb.py`: Excel を列名そのままで raw テーブル化する汎用ローダー
- `db/scripts/view_duckdb.py`: 人間がブラウザでテーブルを確認するための読み取り専用ビューア

## 役割

- `raw/`: 一次資料、元 CSV、Excel、JSON、PDF などを保持する
- `db/`: 比較、集計、フィルタ、ランキングに使う定量・構造化データを保持する
- `wiki/`: 要約、解釈、概念、定性情報、分析結果を保持する
- `artifacts/`: wiki と DB から作った表示用レポートを保持する

使い分けの基本は、保存と人間編集は `raw/data/` の CSV / Excel / JSON / Parquet、活用と分析は `db/knowledge.duckdb` です。

CSV や Excel の原文に注記つきの値が混じる場合は、DB 側でも原文列を優先して保持します。たとえば `2026（発表）` や `N/A` のような値が数値と混在する列は TEXT のまま保存し、必要なら別に正規化した数値列を持って集計します。

## 基本方針

- 最初は `knowledge.duckdb` 1つで運用する
- DuckDB は Python の `duckdb` パッケージのみで扱う。duckdb CLI や GUI クライアント（DBeaver 等）は使わず、操作をスクリプト経由の再現可能な形に一本化する
- SQL 定義は `db/schema.sql` にまとめ、DuckDB の変更と同じ変更で管理する
- DuckDB の一時ファイルや WAL は `db/.gitignore` で除外する
- `raw/` の既存ファイルは編集しない
- DB の各行は、可能な限り `sources` または `raw/` 上の原本へ辿れるようにする
- raw の特定ページ、行、時刻などに紐づく行には `raw_path` と `raw_locator` を持たせる
- wiki ページには、必要に応じて対応する `db_entity_id` や `db_source_id` を frontmatter に持たせる
- 行単位の長文メモや判断理由は wiki の Markdown に置き、DB 側の `wiki_path` や `note_id` から参照する
- 矛盾する値は上書きせず、`observations.conflict_status` や wiki 本文で `競合` / `未確定` として残す

## Excel の取り込み

Excel を列名そのままで DuckDB に入れるときは `db/scripts/load_excel_raw_to_duckdb.py` を使います。

```powershell
python db/scripts/load_excel_raw_to_duckdb.py raw/inbox/CASE_SAL/Case_SL12_仕様項目一覧.xlsx
```

- シートごとに `case_sl12_仕様項目一覧_仕様` のような raw テーブルを作る（プレフィックスはファイル名から自動生成、`--prefix` で指定可能）
- 列名は Excel の先頭行をそのまま使う。ファイルごとに列名が違っても、ファイル×シート単位の独立テーブルなので衝突しない
- 各行に `raw_path` / `sheet_name` / `row_no`（Excel 上の行番号）を付け、原本へ辿れるようにする
- 取り込み履歴を `excel_imports` テーブルに記録する
- 同じファイルを再実行すると既存テーブルを置き換える（再取り込み可能）
- 実行のたびに `db/schema.sql` を自動再生成して同期する

入力ファイルとテーブルの対応は `db/loaders.md` に記録します。

## 中身の確認

依存パッケージ（`duckdb` `openpyxl`）は `requirements.txt` で管理し、導入済みです。

人間がテーブルを眺めるときは、ブラウザベースの読み取り専用ビューアを使います。

```powershell
python db/scripts/view_duckdb.py
```

- `http://127.0.0.1:8765/` が開く。localhost のみで待ち受け、外部には公開しない
- 左のテーブル一覧をクリックするとプレビュー表示。列ヘッダークリックでソート、入力欄で表示行の絞り込み、100行単位のページ送り
- 上部の入力欄から SELECT / WITH / DESCRIBE / SUMMARIZE / SHOW / EXPLAIN を実行できる（Ctrl+Enter でも実行）
- 接続は常に `read_only=True` かつリクエストごとに開閉するため、書き込みは一切できず、ビューアを開いたままローダーも実行できる
- 依存は Python 標準ライブラリと `duckdb` パッケージのみ

LLM やスクリプトからの確認は Python ワンライナーで行います。

```powershell
# テーブル一覧と行数
python -c "import duckdb; con=duckdb.connect('db/knowledge.duckdb', read_only=True); print(con.execute('SELECT table_name, sheet_name, row_count FROM excel_imports ORDER BY table_name').fetchall())"

# 任意のクエリ
python -c "import duckdb; con=duckdb.connect('db/knowledge.duckdb', read_only=True); print(con.execute('SELECT * FROM \"case_sl12_仕様項目一覧_概要\"').fetchall())"
```

確認時は `read_only=True` で開き、更新はローダー経由に寄せます。

`knowledge.duckdb` を作り直す場合は、`db/knowledge.duckdb` を削除して `db/loaders.md` の対応表にあるローダーを再実行すれば、`raw/` の原本から同じ状態を再生成できます。

## 使い分け

定量・構造化情報は DB に置きます。

- 数値仕様
- 日付や期間
- 分類ラベル
- 関係性
- 比較表
- 集計可能な観察事実

定性情報は wiki に置きます。

- 要約
- 背景
- 解釈
- pros / cons
- 未解決の問い
- 文脈つきの分析

短い定性メモは DB の `notes` や `value_text` に置いてよいですが、長文、自由記述、思考メモ、機種別の詳細レビューは Markdown に置きます。DB には `wiki_path` と `note_id` を残し、SQL で絞り込んだ行から本文へ辿れるようにします。

原本への参照は別に扱います。`source_id` は source メタデータ、`raw_path` は原本ファイル、`raw_locator` は原本内の位置、`wiki_path` は Markdown メモ、`note_id` は Markdown 内の特定メモを指します。
