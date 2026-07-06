# 運用手順（product-spec-normalizer）

## 前提

- DuckDB は Python 経由でのみ操作する。確認は `read_only=True`、更新はスクリプト経由。
- 標準 DB は `db/knowledge.duckdb`。パイプラインは既存 raw テーブルに書き込まない。

## 通常サイクル

```powershell
# 1. 調査（read_only）: 構造が変わったとき・初回のみ
python .github/skills/product-spec-normalizer/scripts/inspect_duckdb.py --out db/review/profile_report.md

# 2. パイプライン実行（02 DDL → 03 raw → 04 canonical/辞書 → 05 mapping → 06 normalized → 07 views）
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py

# 3. レビュー用 CSV 出力（db/review/ 配下）
python .github/skills/product-spec-normalizer/scripts/export_review_files.py

# 4. レビュー結果を反映して部分再実行
#    - 同義語/パターン/単位ルールの追加 → sql/04 を編集
#    - 取り込み対象の追加/変更 → sql/03 を編集
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --steps 04 05 06 07
```

各 SQL は冒頭で自分の層のテーブルだけを DELETE してから作り直すため、何度でも再実行できる。

## 新しい Excel / テーブルが追加されたとき

1. まず既存ローダーで取り込む: `python db/scripts/load_excel_raw_to_duckdb.py raw/inbox/<file>.xlsx`
2. `inspect_duckdb.py` で新テーブルの列シグネチャを確認する。
   - 既知の族（例: `giant_*_仕様比較`、`multione_*_仕様一覧`、`case_*_仕様項目一覧_仕様` など）と同じ構造なら、
     `sql/03_build_raw_specs.sql` の該当ブロックの UNION にテーブル名を1行足す。
   - 新しい構造なら、既存ブロックを手本に新しい INSERT ブロックを書く（product_id の付与・
     unit_system・source_rank を忘れない）。
3. 新製品が増える場合は products のブロックも更新する。
4. パイプラインを全実行し、品質チェック 9（uncovered_source_tables）で取り込み漏れがないか確認する。
5. 新しい項目名は unmapped_items に出るので、mapping_review_guide.md に従って辞書に追加する。

## スキーマ同期（AGENTS.md の DB 運用方針）

- `normalize_specs.py` は実行後に `db/schema.sql` を DB の実テーブルから自動再生成する
  （`load_excel_raw_to_duckdb.py` と同じ方式・同じフォーマット）。
- 標準化テーブルの DDL を変えたときは、`sql/02` を編集 → パイプライン実行、で schema.sql まで同期される。
- `--no-schema-sync` を付けると再生成をスキップできる（調査目的の部分実行時など）。

## やり直し・撤去

```powershell
# 標準化オブジェクトだけを全削除（既存 raw テーブル・excel_imports は無傷）
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --drop
```

## issues の管理

- `normalization_issues` は毎回のパイプライン実行で自動再生成される行（unmapped_item, low_confidence,
  unit_no_rule, unit_missing, numeric_parse_failed, scope_excluded）と、手動で追記する行が混在する。
- レビューで解決したものは、根本対応（辞書追加など）をしてから再実行すれば消える。
  「対応しない」と決めたものは status='wont_fix' に更新して残す（Python 経由で UPDATE）。

## 比較表の利用

```python
import duckdb
con = duckdb.connect("db/knowledge.duckdb", read_only=True)
core = con.execute("SELECT * FROM product_comparison_core_view ORDER BY company, product_name").df()
full = con.execute("SELECT * FROM product_comparison_full_view").df()
```

- 比較ビューの各セルは `best_normalized_specs`（confidence 降順 → 一次シート優先 → metric 優先で採用した1行）に基づく。
- 採用されなかった値も normalized_specs に残っているため、疑わしいセルは
  `SELECT * FROM normalized_specs WHERE product_id=? AND canonical_item=?` で全候補を確認できる。
