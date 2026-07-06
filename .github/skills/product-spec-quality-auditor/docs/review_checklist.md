# 人間レビューチェックリスト（review_checklist.md）

監査スクリプト実行後、`audit_outputs/` の CSV を見ながら以下を確認する。
このチェックが終わるまで、比較ビューの数値を対外資料に使わない。

## 0. 前提確認

- [ ] `quality_audit_report.md` の第1節（総合点・判定）と第4節（重大な問題）を読んだ
- [ ] `raw/_run_meta.json` で「missing_object」になったテーブル・ビューを把握した
      （不足はレポートの「テーブル設計」に載る）

## 1. 怪しいマッピング（suspicious_mappings.csv）— 最優先

各行について「raw_item_name の意味」と「canonical_item の定義」が同じ測定対象・同じ条件かを確認する。

- [ ] **重量系**: 本体重量 / 運転質量 / 梱包重量 / 輸送重量 / キャブ付き・なしが混ざっていないか
- [ ] **定格・最大系**: 最大値 / 定格値 / 標準値 / 平均値が同じ canonical に入っていないか
- [ ] **電力系**: 消費電力 / 最大消費電力 / 待機電力の混同がないか
- [ ] **寸法系**: 全長・全幅・全高と「外形寸法（W×D×H の複合値）」の分解が正しいか
- [ ] **規格系**: 対応規格 / 取得認証 / 準拠規格を同一視していないか
- [ ] **オプション系**: オプション対応の値が標準対応として比較表に出ていないか
- [ ] **温度系**: 使用（動作）温度と保管温度の混同がないか
- 判断結果は normalizer 側のレビューフロー（normalization_issues / 辞書）に反映する。
  **この Skill では DB・辞書を書き換えない。**

## 2. 低confidence マッピング（low_confidence_mappings.csv）

- [ ] confidence<0.5 は全件、<0.7 は少なくとも会社×canonical_item ごとに1件は原本と突き合わせた
- [ ] notes の根拠が実際の仕様書の記述と合っているか
- [ ] 「confidence は低いが正しい」ものと「誤マッピング」を区別してメモした

## 3. 未マッピング項目（unmapped_raw_items.csv）

- [ ] 出現回数（n_rows）が多い項目から、辞書追加すべきか比較対象外かを判断した
- [ ] 複数社に出る項目（比較価値が高い）を優先した

## 4. 重複・単位・数値化

- [ ] duplicate_canonical_items.csv: 値が食い違う組（n_distinct_values > 1）の採用値を確認した
- [ ] unit_mismatches.csv: 不足している変換ルール（unit_conversions への追加候補）を列挙した
- [ ] raw/numeric_parse_failures.csv: 複合値（"1534 / Ext 888" 等）の分解方針を決めた
- [ ] raw/conversion_factor_review.csv: 同じ単位ペアで係数がばらついていないか確認した
- [ ] raw/forced_numeric_candidates.csv: 範囲・約値を単一数値化したものが誤解を生まないか確認した

## 5. 比較ビュー

- [ ] comparison_missing_rates.csv: 欠損率の高い列を「残す / priority を下げる / 取り込みを増やす」のどれにするか決めた
- [ ] raw/comparison_core_sample.csv を目視し、列名が比較表として読めるか、
      数値列にテキストが混ざっていないかを確認した
- [ ] raw/company_missing_priority1.csv: 会社ごとに欠けている最重要項目の原因
      （原本に無い / 取り込み漏れ / マッピング漏れ）を切り分けた

## 6. issue 管理

- [ ] raw/open_issues_list.csv の open 件数と内訳を把握した
- [ ] raw/low_confidence_not_issued.csv / raw/unmapped_not_issued.csv の「見逃し」を issue 化するよう
      normalizer 側の作業として起票した

## 7. レポートの確定

- [ ] レビュー結果（黒と確認した混同、白と確認した候補）を quality_audit_report.md の
      第8節・第10節・第12節に反映した
- [ ] 混同が確認された場合、score_rubric.md の原則に従い spec_mapping 品質の点数を下方修正した
- [ ] 「問題なし」と書いた項目にはすべて根拠（0件だった AUDIT ブロック名）を付けた
