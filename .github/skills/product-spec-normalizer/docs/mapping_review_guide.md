# マッピングレビューガイド

レビューの目的は「自動マッピングの初期案を、辞書（sql/04）を育てながら確定させる」こと。
レビュー対象は `db/review/` に出力される CSV。

## レビューの順番

1. **unmapped_items.csv** — 未マッピング項目
   - 会社×項目名ごとに集約されている。sample_value を見て判断する。
   - 判断は3択:
     a. 既存 canonical に対応する → `spec_synonyms` に1行追加（確度が高い場合）または `spec_patterns` に規則追加（条件付き/低確度の場合）
     b. 新しい比較軸として必要 → `canonical_specs` に項目を追加してから a を行う
     c. 比較不要（会社固有・管理情報など）→ 何もしない。気になるなら issues を wont_fix にする
2. **low_confidence_mappings.csv** — confidence<0.7
   - inferred / unit_based の推定が正しいか確認。正しければ synonyms に昇格（0.9〜1.0 になる）、
     間違いなら patterns の規則を修正・削除。
3. **unit_mismatches.csv** — 変換できなかった単位
   - 変換式が明確なら `unit_conversions` に追加。
   - 導出が必要（Ah×V→kWh 等）や意味が曖昧なら、テキストのまま維持する判断を notes に残す。
4. **duplicate_values.csv** — 同一製品×項目の値の食い違い
   - min/max の差を見る。丸め・単位系・測定条件（キャブ有無、タイヤ違い、レンジ違い）が原因のことが多い。
   - 採用ルール（best_normalized_specs の order）で正しい方が選ばれているか確認し、
     必要なら該当マッピングの confidence を調整して採用順を変える。
5. **numeric_parse_failures.csv** — 数値化失敗
   - "1534 / Ext 888"（標準/延長）のような複合値は、分解して別 canonical にするか、
     テキストのまま残すかを決める。自動での分解は行わない。
6. **high_missing_rate_items.csv / company_skewed_items.csv**
   - 欠損率が高い・特定社にしか無い項目は、比較軸として維持するか priority を 3 に落とすか判断する。

## 辞書の書き方

### spec_synonyms（確度の高い1対1）

```sql
-- key は psn_item_key() 適用後の文字列（小文字・脚注記号除去・空白1個・全角/半角ダッシュ→'-'）
('service weight', 'operating_weight', 'synonym', 'GIANT'),
```

- key の確認方法: `SELECT psn_item_key('Service weight')` を Python 経由で実行。
- 複合キーは `大分類 / 中分類 / 項目` の連結、条件付きは `項目 [条件]` の形で raw_specs に入っている。

### spec_patterns（条件付き・判断を伴うもの）

```sql
-- (pattern_id, item_regex, company_regex, category_regex, unit_regex, canonical_item, method, confidence, notes)
(60, '^working hydraulics$', 'GIANT', NULL, NULL, 'aux_hydraulic_flow', 'inferred', 0.6, '要レビュー'),
```

- pattern_id 昇順で最初に一致した規則が使われる。特殊な規則ほど小さい番号にする。
- 同じ項目名でも単位で意味が変わる場合は unit_regex を使う（例: 'battery capacity' の kWh / Ah）。
- confidence の目安: 単位や文脈から確実 0.8–0.9 / 妥当な推定 0.6–0.7 / 弱い推定 0.5。

### unit_conversions

```sql
('gpm', 'L/min', 3.785411784, 'US ガロン'),
```

- from_unit は `psn_unit_key()` 適用後のキー（小文字、空白・ピリオド・中黒除去）。
- 同名単位で次元が違う場合（lbs=質量/力）は、to_unit の違いで両方登録してよい。
  canonical_specs 側の canonical_unit が変換先を決めるため衝突しない。

## 統合してよいか迷ったときの基準

- **統合してよい**: 表記だけの違い（Weight / 運転質量 / Service weight）、単位系だけの違い、脚注記号の有無。
- **inferred で保留**: 測定条件が併記されている（50cm、High Range、w/standard tires）、
  部位が違う可能性（Cab Height と全高）、回路が違う可能性（Working hydraulics と補助油圧）。
- **統合しない**: 条件が不明（直進か屈曲か不明な転倒荷重）、導出が必要、複合値、
  会社独自の概念（Bob-Tach 等）。→ 別 canonical にするか manual のまま残す。

## レビュー結果の反映

```powershell
# sql/04 を編集後、辞書から下流だけ再実行
python .github/skills/product-spec-normalizer/scripts/normalize_specs.py --steps 04 05 06 07
python .github/skills/product-spec-normalizer/scripts/export_review_files.py
```

unmapped_items と low_confidence が減っていること、duplicate_values に悪化がないことを確認する。
