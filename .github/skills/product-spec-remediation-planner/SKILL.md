---
name: product-spec-remediation-planner
description: product-spec-quality-auditor の監査結果（audit_outputs/）をもとに、product-spec-normalizer を安全に修正するための計画を作るときに使う。問題分類・修正優先順位・canonical_item分割案・マッピング修正案・単位変換ルール修正案・人間レビュー用Excel・レビュー結果の取り込み・normalizer修正指示・再監査目標を remediation_outputs/ に出力する。修正計画と人間レビュー支援専用であり、DB・normalizerのSQL/Python・設定ファイルは一切変更しない。
---

# Product Spec Remediation Planner

`product-spec-quality-auditor` の監査結果を読み取り、`product-spec-normalizer` を安全に修正するための
**修正計画**と**人間レビュー成果物**を作るスキル。実際の修正は一切行わない。

## このSkillを使う場面

- 監査（`audit_outputs/quality_audit_report.md`）で問題が見つかり、normalizer を修正したいとき。
- 修正の前に「どこを・どの順で・誰の判断で」直すかを整理したいとき。
- 意味混同疑い・未マッピング・単位不一致・重複などを人間が短時間でレビューできる形にしたいとき。
- 人間レビューの結果を機械可読な修正計画（normalizer への指示書）に変換したいとき。
- 使わない場面: 標準化の実行・修正そのもの（`product-spec-normalizer` の仕事）、
  品質監査そのもの（`product-spec-quality-auditor` の仕事）。

## 入力ファイルの前提

- 監査結果は `audit_outputs/` 配下にある想定:
  `quality_audit_report.md` / `audit_summary.csv` / `suspicious_mappings.csv` /
  `risky_group_merges.csv` / `unmapped_raw_items.csv` / `unit_mismatches.csv` /
  `duplicate_canonical_items.csv` / `low_confidence_mappings.csv` /
  `comparison_missing_rates.csv` / `company_coverage.csv` / `human_review_required.csv`
- **存在しないファイルがあっても処理を止めない。** 不足として `remediation_outputs/_run_meta.json`
  と `remediation_plan.md` に記録する。
  - 特例1: `risky_group_merges.csv` が無い場合は `suspicious_mappings.csv`（`rule_name` 列で
    同じ危険群を持つ）を代替として読み、fallback を記録する。その際は監査側の定義
    （auditor sql/10: 同一 rule_name×canonical_item に **複数の異なる raw_item_name** が
    寄っている群のみ）に合わせて集約し、raw項目が1種類だけの群は対象外として件数を記録する。
  - 特例2: `audit_outputs/raw/canonical_definitions.csv`（canonical_specs の実名一覧）が
    あれば、canonical 候補名を実名と突き合わせて検証する（実在しない候補は
    manual_review_required に降格、既存項目との重複疑いは近似名を提示）。
    無い場合は候補名を「未検証」と明記して confidence を下げる。planner はこの目的でも
    DB には接続しない。
- 人間レビュー後（mode 2）は以下のいずれかがある想定:
  `remediation_outputs/human_review_workbook.xlsx` / `remediation_outputs/reviewed_decisions.csv` /
  `remediation_outputs/reviewed_decision_template.csv`（記入済みなら decisions として扱える）。
- `knowledge.duckdb` はこのSkillでは**参照も変更もしない**。必要な事実はすべて監査CSVから読む。

## 2つの実行モード

### mode 1: `prepare_review` — 監査結果を読み、人間レビュー用の成果物を作る

主な出力: `remediation_plan.md` / `human_review_workbook.xlsx` / `human_review_required.csv` /
`review_dashboard.html` / `reviewed_decision_template.csv` / 各種修正候補CSV。
人間が判断すべき項目を集約し、1行1判断・優先度順で短時間に判断できる形式にする。

### mode 2: `build_change_plan` — 人間レビュー結果を読み、normalizer への修正計画を作る

主な出力: `normalizer_change_plan.md` / `approved_*.csv` / `conversion_blocklist.csv` /
`manual_review_remaining.csv` / `reviewed_decision_errors.csv` / `reaudit_targets.csv`。
このモードでも DB・normalizer ファイルは変更せず、**実行可能な計画の出力のみ**を行う。

## 参照する監査結果

| ファイル | 使い方 |
|---|---|
| `audit_summary.csv` / `quality_audit_report.md` | 現在スコア・総合判定。再監査目標の「現在値」に使う |
| `risky_group_merges.csv`（無ければ `suspicious_mappings.csv`） | 意味混同疑いの群。canonical分割案の主入力 |
| `unmapped_raw_items.csv` | 未マッピング項目の5分類 |
| `unit_mismatches.csv` | 単位不一致の6分類・変換ルール候補と変換禁止候補 |
| `duplicate_canonical_items.csv` | 同一製品×項目の重複の7分類 |
| `low_confidence_mappings.csv` | 自動修正候補/人間レビュー候補/除外候補/canonical見直し候補 |
| `comparison_missing_rates.csv` / `company_coverage.csv` | 優先度付け（影響範囲）の材料 |
| `human_review_required.csv` | レビュー項目の網羅チェック（取りこぼし防止） |

## 人間レビューの位置づけ

- AIの分類・推奨は**すべて候補**であり、確定は人間の `human_decision` だけが行う。
- `human_review_workbook.xlsx` が人間の判断の唯一の記入場所（またはCSVテンプレート）。
- 人間判断とAI推奨が矛盾した場合は**常に人間判断が優先**。AI推奨は記録として残すのみ。
- 人間が `reject` / `needs_source_check` にした項目は修正対象に入れない。

## 絶対に守る制約

- このSkillは**修正計画と人間レビュー支援専用**。
- `knowledge.duckdb` に接続しない（read_only でも接続しない。必要な情報は監査CSVにある）。
- `product-spec-normalizer` の SQL・Python・設定ファイルを変更しない。
- `audit_outputs/` 配下を変更しない（読み取りのみ）。
- 書き込んでよいのは `remediation_outputs/` 配下の新規ファイルのみ。
- 出力するのは修正計画・レビュー用Excel・レビュー結果CSV・normalizer修正指示だけ。
  実際の修正（テーブル・ビュー・辞書・ルールの変更）は `product-spec-normalizer` 側の作業。

## 実行手順

```powershell
# ===== mode 1: prepare_review =====
# 1. 監査CSVを読み込み、問題を分類・優先度付けして _analysis.json と remediation_summary.csv を作る
python .github/skills/product-spec-remediation-planner/scripts/analyze_audit_outputs.py

# 2. remediation_plan.md と修正候補CSV群を作る
python .github/skills/product-spec-remediation-planner/scripts/build_remediation_plan.py

# 3. 人間レビュー用Excel・HTMLダッシュボード・決定テンプレートCSVを作る
python .github/skills/product-spec-remediation-planner/scripts/export_review_workbook.py

# ===== 人間レビュー =====
# remediation_outputs/human_review_workbook.xlsx の human_decision / status / reviewer_note を記入
# （Excelを使わない場合は reviewed_decision_template.csv を記入して reviewed_decisions.csv として保存）

# ===== mode 2: build_change_plan =====
# 4. レビュー済みExcel/CSVを検証・分類し、承認済みCSVと残課題CSVに分ける
python .github/skills/product-spec-remediation-planner/scripts/import_review_decisions.py

# 5. normalizer_change_plan.md と reaudit_targets.csv を作る
python .github/skills/product-spec-remediation-planner/scripts/build_normalizer_change_plan.py
```

入出力先を変える場合は各スクリプトの `--audit-dir` / `--out-dir` を使う。

## 問題分類ルール

すべての指摘は `review_id`（全シート・全CSV共通キー）と `issue_type` を持つ。

| issue_type | 由来 | review_id 接頭辞 |
|---|---|---|
| `risky_group_merge` | risky_group_merges / suspicious_mappings | `RGM-` |
| `unmapped_raw_item` | unmapped_raw_items | `UNM-` |
| `unit_mismatch` | unit_mismatches | `UNI-` |
| `duplicate_canonical_item` | duplicate_canonical_items | `DUP-` |
| `low_confidence_mapping` | low_confidence_mappings | `LCM-` |
| `canonical_split_proposal` | 分割案（RGM/DUPから派生） | `SPL-` |
| `exclusion_candidate` | 除外候補（UNM/LCMから派生） | `EXC-` |

分類の詳細基準は `docs/` の各ガイドにある。共通原則:

- 分類は raw_item_name・notes・値の形からの**規則ベースの推定**であり、confidence を必ず付ける。
- confidence < 0.8 の分類は自動確定しない（人間レビュー行に必ず載せる）。
- どの分類にも当てはまらない場合は `manual_review_required` とし、迷っている理由を書く。

## 修正優先順位の付け方

| 優先度 | 基準 | 例 |
|---|---|---|
| P1 | 比較ビューに**誤った値**が出る恐れ（意味混同・値競合・誤変換） | risky_group_merges、値が食い違う重複 |
| P2 | 値が**欠ける・数値化されない**（変換ルール不足、抽出不備） | unit_mismatches、numeric_parse_failed |
| P3 | カバレッジ不足（未マッピング、会社別の偏り） | unmapped_raw_items |
| P4 | 記録・整備系（notes欠落、低影響の低confidence） | 影響1〜2行の軽微項目 |

同一優先度内は `affected_count`（影響行数）の降順。P1 は全件人間レビュー必須。

## canonical_item 分割判断の基準

`docs/canonical_split_guide.md` に全文。要点:

- **測定条件・対象が違えば別項目**（キャブ付き重量と梱包重量、定格出力と最大出力）。分割する。
- **同じ量の表記ゆれ**（全高/Overall Height/機体高さ）は分割しない。マッピング側で寄せる。
- 分割案は `current_canonical_item` → 複数の `new_canonical_item` と、
  どの raw_item_name がどちらへ行くかを必ずセットで提示する。
- 重点確認する群: 重量/質量/本体重量/梱包重量、最大値/定格値/標準値/平均値、
  消費電力/最大消費電力/待機電力、幅/高さ/奥行/外形寸法、対応規格/取得認証/準拠規格、
  オプション対応/標準対応、使用温度/保管温度。
- 分割の確定は人間の `split_canonical` 判断のみ。AIは案を出すだけ。

## unmapped_raw_items の分類基準

`map_to_existing` / `create_new_canonical` / `exclude_from_comparison` /
`manual_review_required` / `source_extraction_issue` の5分類。理由と confidence を必ず付ける。

- 既存 canonical と同義とみなせる語を含む → `map_to_existing`（候補canonical_itemを添える）
- 比較価値があるが対応する canonical が無い（例: SERVICE CAPACITIES 系） → `create_new_canonical`
- 製品比較に使えない列挙・自由記述（タイヤバリエーション、シリーズ名、色など） → `exclude_from_comparison`
- 名前がヘッダ分解の失敗を示す（例: `TIPPING LOAD / X` の一文字接尾辞） → `source_extraction_issue`
- 上記いずれとも判断できない → `manual_review_required`（迷う理由を書く）

詳細は `docs/mapping_decision_guide.md`。

## unit_mismatches の分類基準

`missing_conversion_rule` / `wrong_canonical_unit` / `wrong_raw_unit_extraction` /
`not_convertible` / `value_contains_condition` / `manual_review_required` の6分類。

- 単位が同義・別表記（km/hr.→km/h）や既知の確定換算（hp→kW） → `missing_conversion_rule`
  （`unit_rule_candidates.csv` に載せる）
- 元単位が複合・条件付きで一意に換算できない（Ah/48V→kWh、Nm@rpm） →
  `not_convertible` または `value_contains_condition`（`conversion_blocklist_candidates.csv` に載せる）
- canonical_unit 側が実態に合わない → `wrong_canonical_unit`
- 元値から単位が正しく切り出されていない → `wrong_raw_unit_extraction`
- 換算式が曖昧なものは**確定しない**。必ず blocklist 候補か manual_review_required に回す。

詳細は `docs/unit_conversion_review_guide.md`。

## duplicate_canonical_items の分類基準

`duplicate_source_rows` / `standard_vs_max_value` / `rated_vs_peak_value` / `body_vs_packaging` /
`option_vs_standard` / `range_or_multi_value` / `manual_review_required` の7分類。

- 値が全て同一（丸め差含む相対差2%未満） → `duplicate_source_rows`（重複排除で解決）
- 値が系統的に大小2系統（定格/最大、標準/ピーク等の疑い） → 該当分類 + canonical分割案を作る
- 値に規格文字列などの混入がある → `manual_review_required`（抽出不備の疑いを注記）
- canonical_item を分けるべき場合は `canonical_split_proposals.csv` に SPL- 行を作る

## low_confidence_mappings の分類

- **自動修正候補**: 根拠が明確で決め打ちできる（同義語辞書に追加するだけ等）。それでも確定は人間承認後。
- **人間レビュー候補**: 意味の解釈が要る（inferred で confidence≤0.65 など）
- **除外候補**: 比較に使えない項目への無理なマッピング
- **canonical設計見直し候補**: 同じ raw 項目が複数 canonical に割れる等、設計側の問題

## human_decision の扱い

固定語彙（これ以外は不備として `reviewed_decision_errors.csv` 行き）:
`approve` / `reject` / `split_canonical` / `map_to_existing` / `create_new_canonical` /
`exclude_from_comparison` / `add_conversion_rule` / `change_canonical_unit` /
`fix_raw_unit_extraction` / `do_not_convert` / `needs_source_check` / `keep_manual_review`

`status` は `pending` / `reviewed` / `deferred`。

修正対象に**入れない**条件（→ `manual_review_remaining.csv`）:
`human_decision` が空欄 / `status` が `pending` / `reject` / `needs_source_check` /
判断と必要項目の矛盾 / 必要な `final_canonical_item`・`final_unit` が空欄 / `apply_flag` が false。

必須項目の対応:

| human_decision | 必須の追加項目 |
|---|---|
| `map_to_existing` / `create_new_canonical` / `split_canonical` | `final_canonical_item` |
| `add_conversion_rule` / `change_canonical_unit` | `final_unit` |
| その他 | なし（`apply_flag` と `status=reviewed` は全件必須） |

## normalizer 修正指示の作り方

- 承認済み判断（approved）だけを入力にする。1指示につき根拠 `review_id` を必ず添える。
- 修正対象は normalizer の具体ファイルに対応付ける:
  同義語・マッピング → `sql/05_build_spec_mapping.sql` / `spec_synonyms`、
  canonical定義 → `sql/04_create_initial_canonical_specs.sql`、
  単位変換 → `sql/06_build_normalized_specs.sql` / `unit_conversions`、
  比較ビュー → `sql/07_create_comparison_views.sql`。
- **既存テーブルの直接変更は指示しない。** `spec_mapping_v2` / `normalized_specs_v2` /
  `product_comparison_core_view_v2` / `product_comparison_full_view_v2` などの
  v2テーブル・ビューを新設し、検証後に切り替える方針で書く。
- rejected / deferred / 不整合の項目は「実行してはいけない修正」として明示的に列挙する。

## 再監査目標

修正後は `product-spec-quality-auditor` を再実行し、以下を最低目標とする
（`reaudit_targets.csv` に現在値と併記して出力する）。

| 指標 | 最低目標 |
|---|---|
| 未マッピング率 | 10%未満 |
| 単位不一致 | 10行未満 |
| 数値化失敗 | 20行未満 |
| 値競合 | 0件または全件説明付き |
| spec_mapping品質 | 12/20以上 |
| normalized_specs品質 | 9/15以上 |
| 総合点 | 75/100以上 |

## 禁止事項

- DBを変更しない（接続もしない）
- normalizerのSQLやPythonを変更しない
- 監査結果を都合よく解釈しない（分類に迷ったら manual_review_required に倒す）
- 低confidence項目を勝手に確定しない
- 意味の違う項目を同じcanonical_itemに寄せない
- 仕様書にない情報を補完しない
- 単位変換ルールが曖昧なものを確定しない（blocklist候補に回す）
- 人間レビューが必要な項目を自動修正扱いにしない
- 人間がrejectした項目を修正対象に入れない
- 人間判断とAI推奨が矛盾する場合にAI推奨を優先しない

## スクリプトとドキュメント

| ファイル | 役割 |
|---|---|
| `scripts/analyze_audit_outputs.py` | 監査CSVを読み、分類・優先度・影響範囲を集計。`_analysis.json` と `remediation_summary.csv` を出力。DB・normalizerには触れない |
| `scripts/build_remediation_plan.py` | 分析結果から `remediation_plan.md` と修正候補CSV群を出力。confidence と人間レビュー要否を付ける |
| `scripts/export_review_workbook.py` | 人間レビュー用Excel（白地黒文字・フィルタ不使用・1行1判断）、`review_dashboard.html`、`reviewed_decision_template.csv`、`human_review_required.csv` を出力。`review_id` を共通キーにする |
| `scripts/import_review_decisions.py` | レビュー済みExcel/CSVを読み、`human_decision`・`status`・`apply_flag` を検証。不備行は `reviewed_decision_errors.csv`、承認行のみ `approved_*.csv` へ |
| `scripts/build_normalizer_change_plan.py` | 承認済み判断から `normalizer_change_plan.md` と `reaudit_targets.csv` を出力 |
| `docs/remediation_policy.md` | 修正方針・優先順位・安全原則の全文 |
| `docs/canonical_split_guide.md` | canonical_item 分割判断の基準と分割案の書式 |
| `docs/mapping_decision_guide.md` | unmapped / low_confidence の分類基準 |
| `docs/unit_conversion_review_guide.md` | 単位不一致の分類・変換ルール追加/禁止の基準 |
| `docs/human_review_guide.md` | レビュー担当者向けのExcel記入手順 |

## 関連ドキュメント

- `.github/skills/product-spec-quality-auditor/SKILL.md` — 入力（監査結果）を作る側
- `.github/skills/product-spec-normalizer/SKILL.md` — 修正計画を実行する側
