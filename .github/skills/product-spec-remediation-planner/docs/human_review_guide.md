# 人間レビュー手順（human_review_workbook.xlsx の使い方）

対象: `remediation_outputs/human_review_workbook.xlsx` を記入するレビュー担当者。

## 全体の流れ

1. `review_dashboard.html` で全体像（総合スコア・重大問題・件数）を把握する
2. Excel の `00_readme` を読む
3. `01_priority_review` を上から順に判断する（P1 が最優先。ここだけでも完了させる）
4. 時間があれば `02_`〜`07_` の各シートで残りを判断する
5. 記入したら Excel を保存し、`build_change_plan` モードの実行を依頼する

## 1行の読み方

各行は「1つの判断」を表す。以下の列を見る:

- `review_id`: 判断のID。問い合わせ・差し戻しはこのIDで行う
- `question`: 何を判断すべきか（1文）
- `ai_recommendation`: AIの推奨。**候補であり、従う義務はない**
- `ai_uncertainty`: AIが迷っている理由。ここが空でない行は特に注意して見る
- `sample_values` / `source_examples`: 判断に必要な代表例（元の raw 項目名・値）
- `affected_count`: この判断が影響する行数
- `decision_options`: この行で選べる human_decision の候補

## 記入する列（これ以外は編集しない）

| 列 | 記入内容 |
|---|---|
| `human_decision` | 下の固定語彙から選ぶ（ドロップダウンあり）。自由記述は不可 |
| `final_canonical_item` | map_to_existing / create_new_canonical / split_canonical のとき必須 |
| `final_unit` | add_conversion_rule / change_canonical_unit のとき必須 |
| `apply_flag` | 修正に反映してよいなら `true`。迷うなら `false`（保留扱いになる） |
| `reviewer_note` | 判断理由・条件・注意点（reject 時は理由を必ず書く） |
| `status` | 判断したら `reviewed`。後回しは `deferred`。未着手は `pending` のまま |

## human_decision の固定語彙

`approve` / `reject` / `split_canonical` / `map_to_existing` / `create_new_canonical` /
`exclude_from_comparison` / `add_conversion_rule` / `change_canonical_unit` /
`fix_raw_unit_extraction` / `do_not_convert` / `needs_source_check` / `keep_manual_review`

- `approve`: AI推奨のとおりでよい
- `reject`: この修正はしない（理由を reviewer_note に必ず書く）
- `needs_source_check`: 元の仕様書・Excelを見ないと判断できない（差し戻し）
- `keep_manual_review`: 今回は判断せず、レビュー対象として残す

## 判断のコツ

- **canonical分割**: 「2つの値を同じ列に並べて製品比較してよいか?」で判断。No なら split_canonical
- **単位変換**: 換算式が一意に書けるものだけ add_conversion_rule。少しでも曖昧なら do_not_convert
- **未マッピング**: 比較に使う見込みがない項目は遠慮なく exclude_from_comparison。
  除外してもデータは消えない（raw_specs に残る）
- **迷ったら確定しない**: needs_source_check / keep_manual_review は正当な判断。
  誤った approve の方が害が大きい

## やってはいけないこと

- 固定語彙以外を human_decision に書く（取り込み時にエラー行として弾かれる）
- `review_id` 列の編集、行の並べ替え・削除（集約行の意味が壊れる）
- AI推奨に理由なく全件 approve を付ける（それは人間レビューではない）

## Excel を使わない場合

`reviewed_decision_template.csv` に同じ内容を記入し、
`remediation_outputs/reviewed_decisions.csv` として保存してもよい。
列: `review_id, issue_type, human_decision, final_canonical_item, final_unit,
apply_flag, reviewer_note, reviewed_by, reviewed_at`
