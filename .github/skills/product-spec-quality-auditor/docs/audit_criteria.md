# 監査基準（audit_criteria.md）

`product-spec-quality-auditor` が何をどう確認するかの定義。
各観点は sql/ の「-- AUDIT: <名前>」ブロックに対応する。
機械的に判定できない観点は「レビュー材料を出す」ところまでが SQL の仕事で、
最終判断は人間またはエージェントが行う。

## 1. データ保全（sql/02）

| 確認内容 | AUDIT ブロック | 判定 |
|---|---|---|
| 既存テーブルが変更・削除されていないか | raw_source_row_reachability, uncovered_source_tables | raw_specs が参照する元テーブルが実在しない → NG |
| raw データが保持されているか | raw_specs_source_gaps | source 欠落 0 件が正常 |
| 元テーブル・元列・元行・元値・元単位を追跡できるか | normalized_specs_source_gaps, original_value_traceability | present 行で original_value 欠落 → NG |
| normalized 側から raw 側へ戻れるか | normalized_to_raw_traceability | 戻れない行 0 件が正常 |
| source 情報が欠落していないか | mapping_source_gaps | 欠落 0 件が正常 |

## 2. テーブル設計（sql/01）

- 期待オブジェクト: products / raw_specs / canonical_specs / spec_mapping /
  normalized_specs / normalization_issues / product_comparison_core_view /
  product_comparison_full_view（＋補助: spec_synonyms / spec_patterns / unit_conversions / best_normalized_specs）
- 不足はエラーではなく「不足」としてレポートに記録する（expected_objects_presence）。
- 列定義（standard_object_columns）で、識別子（product_id / canonical_item / raw_spec_id 等）、
  source 列、confidence 列の有無を確認する。
- NULL の多さは SUMMARIZE（sql/07 の missing_rates）と各 *_gaps で確認する。
- 追加データへの耐性: 監査 SQL がエラーなく流れること自体が「スキーマが安定している」ことの確認になる
  （エラーは運用しやすさの減点）。

## 3. raw_specs 品質（sql/03）

- products_raw_spec_counts: 全製品に raw 行があるか。0 行は NG、項目数 10 未満は REVIEW。
- raw_products_not_in_master: 製品マスタとの整合。
- raw_item_counts_by_company: 会社間で項目数の桁が違えば取り込み漏れの疑い。
- raw_value_unit_not_separated: 「数値+単位」が raw_value_text に残っている行（分離漏れ候補）。
- raw_duplicate_rows: 縦持ち化の二重取り込み。
- raw_items_per_source_table: 横持ち→縦持ち化の網羅性（source_column の数で列展開を確認）。

## 4. canonical_specs 品質（sql/04）

- canonical_definitions を全件出力し、比較軸としての妥当性（粒度・単位・型・priority）は人間が確認する。
- 機械チェック: 定義欠落（canonical_field_gaps）、表示名重複、未使用項目、
  抽象的すぎる項目名の候補（canonical_abstract_name_candidates）。
- canonical_company_specific_candidates: 1社しかマッピングされていない項目
  ＝会社固有項目を無理に標準化した疑い。
- canonical_product_coverage: priority が高いのにカバー率が低い項目は比較軸として機能していない。

## 5. spec_mapping 品質（sql/05）— 最重要

- mapping_summary / unmapped_raw_items: 未マッピング件数と割合。
- low_confidence_mappings / confidence_band_counts: confidence 0.7 未満・0.5 未満。
- raw_item_multi_canonical_same_company: 同一会社で同じ raw_item_name が複数 canonical に割当（混同疑い）。
- risky_semantic_mappings / risky_group_merges: 重点確認項目。
  以下の語群を含む項目の非 exact マッピングを全件列挙し、
  「異なる raw_item_name が同一 canonical_item に統合されている」組を強い疑いとして検出する。
  - 重量・質量・本体重量・梱包重量
  - 最大値・定格値・標準値・平均値
  - 消費電力・最大消費電力・待機電力
  - 幅・高さ・奥行・外形寸法
  - 対応規格・取得認証・準拠規格
  - オプション対応・標準対応
  - 使用温度・保管温度
- confidence_overrated_candidates: inferred>0.8、pattern/unit_based>0.9、
  notes なしの高 confidence は過大評価の疑い。
- auto_mapped_should_be_manual_candidates: confidence<0.6 の inferred/unit_based は
  本来 manual_required にすべきだった疑い。
- mapping_success_by_company: 会社別の成功率。特定の会社だけ低ければ辞書の偏り。

## 6. normalized_specs 品質（sql/06）

- unit_mismatches: normalized_unit ≠ canonical_unit（present 行のみ）。0 件が正常。
- numeric_parse_failures: numeric 扱いで数値化できていない行。
- forced_numeric_candidates: 「約」「〜」「/」など複合値を無理に数値化した疑い。
- conversion_factor_review: 単位ペアごとの実効変換係数。同一ペアで係数がばらつけば変換バグ。
- normalized_zero_or_negative: 物理量で 0 以下は変換ミスの疑い。
- duplicate_canonical_items: 同一製品×項目の重複。値が食い違う組は採用値の確認が必要。
- best_view_uniqueness: best_normalized_specs は製品×項目で一意（0 行が正常）。
- notes_missing_low_confidence: 推定を含むのに判断理由が残っていない行。

## 7. comparison_view 品質（sql/07）

- comparison_core_counts / duplicates: 1行1製品・重複なし・products と件数一致。
- comparison_*_missing_rates: SUMMARIZE による列別欠損率。80% 以上は比較列として機能していない。
- comparison_core_sample: 列名の分かりやすさ・数値/テキスト混在の目視確認用。
- priority1_coverage_in_views / important_items_not_in_views: 重要項目の落ち・列追加漏れの確認材料。

## 8. issue 管理（sql/08）

- issues_by_type: issue_type / severity / status の分類状況。
- issues_missing_reference: product_id も raw_item_name も無い issue はレビュー粒度として不十分。
- low_confidence_not_issued / unmapped_not_issued: 本来 issue に入れるべき項目の見逃し検出。
- open_issues_list: 人間レビュー待ちの全件。

## 会社別カバレッジ（sql/09）

- company_summary: 会社別の製品数・raw行数・マッピング成功率・平均 confidence。
- canonical_coverage_matrix / company_missing_priority1: 会社×項目の欠け方。
- company_skewed_canonical_items: 1社しか値を持たない項目は比較軸として再考。

## 判定の原則

- 「問題なし」と書けるのは、対応する AUDIT ブロックが 0 件（または OK）を返した場合のみ。
  根拠のない「問題なし」は書かない。
- 候補リスト系（risky_* / *_candidates）は疑いの列挙であり、それ自体は NG 確定ではない。
  レビューで白と判断したものはレポートにその旨を根拠付きで書く。
