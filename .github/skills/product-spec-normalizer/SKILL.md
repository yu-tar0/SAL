---
name: product-spec-normalizer
description: knowledge.duckdb に取り込んだ各社の製品仕様テーブル（項目名・単位・粒度・表記が会社ごとにバラバラ）を、raw / canonical / mapping / normalized の4層に整理し、横比較できる製品比較ビューを作るときに使う。既存テーブルは壊さず、標準化用の追加テーブル・ビュー・マッピング表だけを作る。
---

# Product Spec Normalizer

各社でバラバラな製品仕様データを、レビュー可能な形で標準化し、DuckDB 上で横比較できるようにするスキル。

## このスキルを使うべき場面

- 仕様書 PDF / Excel 由来の製品仕様テーブルが `db/knowledge.duckdb` に取り込み済みで、会社ごとに項目名・単位・縦横の持ち方が異なるとき。
- 「横比較できる製品比較表」を DuckDB 上に作りたいとき。
- 新しい会社・新しい製品の仕様テーブルを追加取り込みした後、標準化を再実行するとき。
- 使わない場面: 元 Excel の取り込み自体（それは `db/scripts/load_excel_raw_to_duckdb.py` の仕事）、定性情報の整理（それは wiki の仕事）。

## 入力ファイルと DB の前提

- 対象 DB は `db/knowledge.duckdb` 1つ。元データは `raw/inbox/` / `raw/data/` の Excel を `load_excel_raw_to_duckdb.py` で取り込んだ raw テーブル群。
- raw テーブルは `raw_path` / `sheet_name` / `row_no` のメタ列を持ち、原本に辿れる。
- DuckDB の操作は必ず Python 経由（CLI・DBeaver 不使用）。確認は `read_only=True`、更新はこのスキルのスクリプト経由で行う。
- 既存テーブルの列名・構造は整っていない前提。テーブル追加のたびに構造が変わりうる。

## 4層の設計

| 層 | テーブル | 役割 |
|---|---|---|
| raw | `raw_specs` | 元の項目名・値・単位・列名・テーブル名を無加工で縦持ちに集約。元行への参照を保持 |
| canonical | `canonical_specs` | 比較に使う標準仕様項目の定義（単位・型・優先度・カテゴリ） |
| mapping | `spec_mapping`（+辞書 `spec_synonyms` / `spec_patterns`） | 会社×製品×元項目 → 標準項目の対応と confidence |
| normalized | `normalized_specs` | 値と単位を正規化した比較可能な仕様。比較ビューの元 |

補助: `products`（製品マスタ）、`unit_conversions`（明示的な単位変換ルール）、`normalization_issues`（要レビュー事項）、
ビュー `best_normalized_specs` / `product_comparison_core_view` / `product_comparison_full_view` / `product_comparison_view`。

## 実行手順

```powershell
# 0. （初回・構造が変わったとき）既存テーブルの調査
python .github/skills/product-spec-normalizer/scripts/inspect_duckdb.py --out db/review/profile_report.md

# 1. パイプライン実行（sql/02〜07 を順に実行し、db/schema.sql も同期）
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py

# 2. レビュー用 CSV の出力（品質チェック + マッピング全量 + 比較表）
python .github/skills/product-spec-normalizer/scripts/export_review_files.py

# 3. レビュー結果を sql/04（同義語・パターン・単位ルール）に反映して部分再実行
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --steps 04 05 06 07
```

やり直したいときは `--drop` で標準化オブジェクトだけを全削除できる（既存 raw テーブルには触れない）。

## DuckDB 調査手順

1. `scripts/inspect_duckdb.py` を read_only で実行し、以下を確認する:
   テーブル一覧・行数・元 Excel、列シグネチャによるグループ（同じ構造のテーブル族）、
   製品名/会社名/型番/仕様項目/値/単位に相当する列、サンプル行。
2. 縦持ちか横持ちかをシグネチャで判断する（`仕様項目`+`仕様値` 列があれば縦持ち、
   製品名が列に埋まっていれば横持ち、`US値`+`メートル値` は単位系併記）。
3. 新しい構造のテーブル族が見つかったら、`sql/03_build_raw_specs.sql` に取り込みブロックを追加する。
   `--items` オプションで項目名の表記ゆれ一覧を出し、`sql/04` の辞書に追加する。

## 標準化方針

- 元データは絶対に上書きしない。標準化はすべて追加テーブル・ビューで行う。
- raw_specs には元の表記を無加工で入れる。複合キー（大分類/中分類/項目）は ` / ` 連結、
  サブ項目・条件は ` [条件]` 形式で項目名に含め、情報を落とさない。
- 1つの元行に metric / US 併記がある場合は別 raw 行として両方保持し、正規化段階で
  「変換成功 > metric > US > その他」の優先で1行に絞る。
- 空欄・記号は value_status で区別する: `N/A`→not_applicable、`—`→not_disclosed、
  値なし→missing（比較ビューでは NULL）、`optional`→optional、判断不能→unknown。
- 重複ソース（例: カタログ集約と型式別シート）は source_rank で優先度を付け、両方保持する。

## マッピング方針

- 3段階で割り当てる。上から順に優先:
  1. `spec_synonyms`（確度の高い1対1対応）→ method=exact(1.0) / synonym(0.9)
  2. `spec_patterns`（正規表現+会社/カテゴリ/単位の条件付き）→ method=pattern / unit_based / inferred（confidence は規則ごとに定義）
  3. どれにも当たらない → method=manual_required(0.0)、`normalization_issues` に記録
- 意味が近いが完全一致しない項目は無理に統合しない。統合する場合は inferred + confidence<=0.7 + notes に根拠を書く
  （例: GIANT の "Working hydraulics" → aux_hydraulic_flow は 0.6 でレビュー対象）。
- 条件が不明な項目は canonical 側を分ける（例: 直進/屈曲が不明な転倒荷重は `tipping_load` として
  `tipping_load_straight` と別項目にする）。
- 会社固有の項目（装備・オプション・タイヤ別寸法など）は、比較軸として必要と判断するまで
  canonical 層に入れない（v1 ではスコープ外として issues に記録）。

## 単位変換方針

- `unit_conversions` にある明示ルールのみ変換する。ルールが無い組み合わせは数値化せず
  テキスト保持し、issue（unit_no_rule / unit_missing）にする。
- 単位表記は `psn_unit_key()` で正規化して照合する（'lb.'→'lb'、'GPM'→'gpm' 等）。
- 同じ単位表記でも次元が違うもの（lbs=質量/力）は、canonical 側の単位で変換先が決まるため安全。
- 導出を伴う変換（例: Ah×V→kWh）はしない。issue に残して人間が判断する。
- カタログの `US値 (メートル値)` 併記は括弧内のメートル側を採用し、confidence を 0.95 倍する。

## confidence の付け方

| 状況 | confidence |
|---|---|
| canonical 名と同一表記 (exact) | 1.0 |
| 確度の高い同義語 (synonym) | 0.9 |
| 単位から判別 (unit_based) | 0.6–0.9（規則ごと） |
| パターン一致 (pattern) | 0.65–0.9（規則ごと） |
| 意味が近いとの推定 (inferred) | 0.5–0.8（要レビュー） |
| 未マッピング (manual_required) | 0.0 |

さらに正規化段階で、テキストからの数値抽出 ×0.95、カタログ併記の分解 ×0.95 を掛ける。
推定を含む行は必ず notes に根拠・条件を書く。

## 人間レビューが必要なケース

- `normalization_issues` の open 行すべて。特に:
  - unmapped_item: 辞書追加か「比較対象外」の判断
  - low_confidence (<0.7): inferred / unit_based の妥当性確認
  - unit_no_rule / unit_missing: 変換ルール追加か、テキストのまま維持の判断
  - numeric_parse_failed: 複合値（"1534 / Ext 888" 等）の分解方針
- 品質チェック duplicate_values で同一製品×同一項目に異なる値が出たもの（採用値の確認）。
- 測定条件が異なる可能性のある比較（オープンキャブ質量 vs キャブ付、hp のグロス/ネット、
  転倒荷重の直進/屈曲、ROC の 50% 規約差）。
- 詳細は docs/mapping_review_guide.md を参照。

## 出力テーブル一覧

| オブジェクト | 種別 | 内容 |
|---|---|---|
| products | TABLE | 製品マスタ（1行1製品、product_id='会社:型式'） |
| raw_specs | TABLE | raw層。元表記のままの縦持ち仕様 |
| canonical_specs | TABLE | 標準仕様項目の定義 |
| spec_synonyms / spec_patterns | TABLE | マッピング辞書（レビューで育てる対象） |
| unit_conversions | TABLE | 明示的な単位変換ルール |
| spec_mapping | TABLE | mapping層。元項目→標準項目の対応 + confidence |
| normalized_specs | TABLE | normalized層。正規化済み仕様値 |
| normalization_issues | TABLE | 要レビュー事項（status で管理） |
| best_normalized_specs | VIEW | 製品×項目ごとの採用1行 |
| product_comparison_core_view | VIEW | コア項目の比較表（1行1製品） |
| product_comparison_full_view | VIEW | priority<=2 のフル比較表 |
| product_comparison_view | VIEW | core のエイリアス |

## 品質チェック

`sql/08_quality_checks.sql`（`export_review_files.py` が CSV 化）:

1. unmapped_items — マッピングされていない raw_item_name
2. low_confidence_mappings — confidence<0.7 のマッピング
3. unit_mismatches — canonical_unit と original_unit が不整合（変換不能）
4. duplicate_values — 同一製品×同一 canonical_item に異なる値
5. numeric_parse_failures — 数値型なのに数値化できなかったもの
6. high_missing_rate_items — 比較ビューで欠損率が高い項目
7. company_skewed_items — 1〜2社にしか存在しない項目（項目名の偏り）
8. open_issues — issues のサマリー
9. uncovered_source_tables — raw_specs に取り込んでいない元テーブル

## 禁止事項

- 既存テーブルを上書きしない（DROP/UPDATE/DELETE はこのスキルが作る標準化オブジェクトのみ）。
- 根拠のない項目統合をしない。意味が近いだけの項目は inferred + 低confidence + notes で保留する。
- 仕様書にない情報を補完しない。欠損は欠損として value_status で区別する。
- 単位変換ルールが曖昧なものを変換しない。unit_conversions に無い変換・導出計算は行わない。
- 比較しやすさのために意味を変えない（条件不明の転倒荷重を「直進」と断定する等は不可）。
- 不明点を勝手に確定しない。仮説は confidence と notes を付けて normalization_issues に残す。

## 関連ドキュメント

- docs/operation_guide.md — 運用手順（再実行・テーブル追加時・スキーマ同期）
- docs/mapping_review_guide.md — マッピングレビューの観点と辞書の育て方
- docs/assumptions.md — 今回の初期構築で置いた仮定・スコープ外の一覧
