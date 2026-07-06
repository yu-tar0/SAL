# 修正方針（remediation policy）

`product-spec-remediation-planner` が修正計画を作るときの原則。

## 基本原則

1. **このSkillは計画専用。** 修正の実行は `product-spec-normalizer` 側の作業であり、
   ここでは DB・SQL・Python・設定ファイルに一切触れない。
2. **人間判断が最終決定。** AIの分類・推奨・confidence はすべて候補。
   人間の `human_decision` と矛盾したら人間判断を採る。AI推奨は記録として残す。
3. **迷ったら保留に倒す。** 分類に確信が持てない項目は `manual_review_required`、
   換算式が曖昧な単位は blocklist 候補にする。「たぶん大丈夫」で確定しない。
4. **既存テーブルは壊さない。** 修正指示は v2 テーブル・ビュー
   （`spec_mapping_v2` / `normalized_specs_v2` / 比較ビュー `_v2`）の新設として書き、
   再監査で品質を確認してから切り替える前提にする。
5. **すべての指示に根拠を付ける。** 修正指示1件につき、由来の `review_id` を必ず添える。
   review_id から監査CSVの元行まで遡れること。

## 修正優先順位

| 優先度 | 基準 | 典型例 | 扱い |
|---|---|---|---|
| P1 | 比較ビューに誤った値が出る恐れ | 意味混同（risky_group_merges）、値が食い違う重複、誤変換 | 全件人間レビュー必須。最優先で計画に載せる |
| P2 | 値が欠ける・数値化されない | 変換ルール不足、numeric_parse_failed、抽出不備 | ルール追加は候補提示→人間承認 |
| P3 | カバレッジ不足 | 未マッピング項目、会社別の偏り | 件数の多い raw_item_name から順に |
| P4 | 記録・整備系 | notes欠落、影響1〜2行の低confidence | まとめて低優先で処理 |

同一優先度内の並び順は `affected_count`（影響行数）の降順。

「誤った値が比較に出る」(P1) は「値が欠ける」(P2) より常に優先する。
欠損はユーザーに見えるが、誤値は気づかれずに意思決定を汚染するため。

## confidence の付け方

- 0.9 以上: 機械的に確定できる根拠がある（値が完全一致の重複など）。それでも人間承認は必要。
- 0.7〜0.89: 規則ベースの推定が強く支持される。人間レビューで確認。
- 0.5〜0.69: 推定に不確実性がある。人間レビュー必須、AI推奨は参考扱い。
- 0.5 未満: 実質的に分類不能。`manual_review_required` にする。

confidence は「AIの分類が正しい確率の見積もり」であり、修正してよい確率ではない。

## 修正対象から除外する条件

以下は承認済み修正に**入れない**（`manual_review_remaining.csv` に出す）:

- `human_decision` が空欄・固定語彙外
- `status` が `pending` または `deferred`
- `human_decision` が `reject` / `needs_source_check` / `keep_manual_review`
- `human_decision` と必要項目の矛盾（下表）
- `apply_flag` が false または空欄

| human_decision | 必須項目 | 欠けたときの扱い |
|---|---|---|
| `map_to_existing` / `create_new_canonical` / `split_canonical` | `final_canonical_item` | missing_required_field |
| `add_conversion_rule` / `change_canonical_unit` | `final_unit` | missing_required_field |

## 再監査目標（最低ライン）

- 未マッピング率: 10%未満
- 単位不一致: 10行未満
- 数値化失敗: 20行未満
- 値競合: 0件、または全件に説明（notes）付き
- spec_mapping品質: 12/20以上
- normalized_specs品質: 9/15以上
- 総合点: 75/100以上

目標未達なら normalizer 修正→再監査を繰り返す。2巡しても届かない場合は
canonical 設計の見直し、または normalizer の部分作り直しを検討する。
