# マッピング判断ガイド（unmapped / low_confidence）

## unmapped_raw_items の5分類

各未マッピング項目を以下のいずれかに分類し、理由と confidence を付ける。

### `map_to_existing` — 既存 canonical_item に対応付ける

- 既存 canonical と同義とみなせる語を含む（例: `Max. Flow Rate` → `aux_hydraulic_flow`）
- 必ず候補 canonical_item を添える。候補が複数あり絞れないなら `manual_review_required` にする
- 対応する修正: `spec_synonyms` への追加（`spec_mapping_v2` 再構築時に反映）

### `create_new_canonical` — 新しい canonical_item を作る

- 比較価値がある量だが、対応する canonical が存在しない
  （例: `SERVICE CAPACITIES / Engine oil w/ filter` → `engine_oil_capacity`）
- 目安: 2社以上が同種の項目を持つ、または priority の高いカテゴリの量である
- 新規候補には display_name_ja / category / canonical_unit / value_type の案を添える

### `exclude_from_comparison` — 比較対象外にする

- 製品比較に使えない列挙・自由記述・バリエーション
  （例: タイヤサイズのバリエーション行 `Turf: 29 x 12.50 - 15`、`シリーズ`、色、備考）
- 1社しか持たず比較にならない自社固有項目（ただし重要スペックなら create_new_canonical を検討）
- 除外はデータ削除ではない。raw_specs には残し、mapping で対象外印を付けるだけ

### `source_extraction_issue` — 元データの抽出不備

- raw_item_name がヘッダ分解の失敗を示す（例: `TIPPING LOAD / X` の一文字接尾辞、
  同名項目が `TIPPING LOAD` / `TIPPING LOADS` / `TIPPING LOAD PATHS` に分裂）
- 値と単位が分離されていない、複数値が1セルに詰まっている痕跡
- 対応する修正はマッピングではなく取り込み側（raw_specs 構築）の見直し

### `manual_review_required` — 上記いずれとも判断できない

- 必ず「AIが迷っている理由」を書く（候補が複数/ 意味が読めない / 元表を見ないと判断不能 など）

## low_confidence_mappings の4分類

| 分類 | 基準 | 後続処理 |
|---|---|---|
| 自動修正候補 | 根拠が明確（notes に確定的な理由がある、単位からの推定が一意） | それでも人間承認後にのみ確定 |
| 人間レビュー候補 | mapping_method が inferred で confidence ≤ 0.65、意味の解釈が要る | 優先度付きでExcelに載せる |
| 除外候補 | 比較に使えない項目への無理なマッピング | exclusion_candidates へ |
| canonical設計見直し候補 | 同一 raw 項目が複数 canonical に割れる、canonical の粒度が合わない | canonical_split_proposals / 設計課題へ |

## 禁止

- 意味の違う項目を同じ canonical_item に寄せない（迷ったら分割案 or manual_review）
- 低confidence項目を勝手に確定しない
- 候補 canonical_item を「近そうだから」で選ばない。定義（canonical_specs の
  display_name / unit / value_type）と突き合わせて根拠を書く
