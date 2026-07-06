-- 05_mapping_quality_audit.sql
-- 目的: spec_mapping 品質の監査（最重要）。未マッピング・低confidence・多重割当・意味混同の疑いを検出する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。
-- 注意: risky_* は「疑い候補」のリスト。混同かどうかの最終判断は人間/エージェントが行う。

-- AUDIT: mapping_summary
-- 未マッピング（manual_required / canonical なし）の件数と割合
SELECT
    COUNT(*) AS total_mappings,
    COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND mapping_method <> 'manual_required') AS mapped,
    COUNT(*) FILTER (WHERE canonical_item IS NULL OR mapping_method = 'manual_required') AS unmapped,
    ROUND(100.0 * COUNT(*) FILTER (WHERE canonical_item IS NULL OR mapping_method = 'manual_required')
          / NULLIF(COUNT(*), 0), 1) AS unmapped_pct
FROM spec_mapping;

-- AUDIT: unmapped_raw_items
-- 未マッピングの raw_item_name 一覧（辞書追加か比較対象外かの判断材料）
SELECT m.company, m.raw_item_name,
       COUNT(DISTINCT m.product_id) AS products,
       COUNT(*) AS n_rows,
       min(m.notes) AS notes_example
FROM spec_mapping m
WHERE m.canonical_item IS NULL OR m.mapping_method = 'manual_required'
GROUP BY m.company, m.raw_item_name
ORDER BY n_rows DESC, m.company, m.raw_item_name;

-- AUDIT: low_confidence_mappings
-- confidence < 0.7 のマッピング（未マッピング=0.0 は除く）
SELECT m.company, m.product_id, p.product_name, m.source_table, m.raw_item_name,
       m.canonical_item, m.mapping_method, m.confidence, m.notes
FROM spec_mapping m
LEFT JOIN products p USING (product_id)
WHERE m.canonical_item IS NOT NULL
  AND m.confidence > 0 AND m.confidence < 0.7
ORDER BY m.confidence, m.company, m.raw_item_name;

-- AUDIT: confidence_band_counts
SELECT
    COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND confidence > 0 AND confidence < 0.5) AS mapped_conf_lt_050,
    COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND confidence > 0 AND confidence < 0.7) AS mapped_conf_lt_070,
    COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND mapping_method <> 'manual_required') AS mapped_total
FROM spec_mapping;

-- AUDIT: raw_item_multi_canonical_same_company
-- 同一会社内で、同じ raw_item_name が複数の canonical_item に割り当てられている（多重割当・混同の疑い）
SELECT company, raw_item_name,
       COUNT(DISTINCT canonical_item) AS n_canonical,
       string_agg(DISTINCT canonical_item, ' | ') AS canonical_items
FROM spec_mapping
WHERE canonical_item IS NOT NULL
GROUP BY company, raw_item_name
HAVING COUNT(DISTINCT canonical_item) > 1
ORDER BY n_canonical DESC, company, raw_item_name;

-- AUDIT: raw_item_multi_canonical_cross_company
-- 会社をまたいで同じ raw_item_name が別の canonical_item に割り当てられている
-- （会社ごとの文脈差なら妥当なこともある。レビュー用）
SELECT raw_item_name,
       COUNT(DISTINCT canonical_item) AS n_canonical,
       string_agg(DISTINCT canonical_item, ' | ') AS canonical_items,
       string_agg(DISTINCT company, ' | ') AS companies
FROM spec_mapping
WHERE canonical_item IS NOT NULL
GROUP BY raw_item_name
HAVING COUNT(DISTINCT canonical_item) > 1
ORDER BY n_canonical DESC, raw_item_name;

-- AUDIT: mapping_method_counts
SELECT mapping_method, COUNT(*) AS n,
       ROUND(AVG(confidence), 3) AS avg_confidence,
       MIN(confidence) AS min_confidence,
       MAX(confidence) AS max_confidence
FROM spec_mapping
GROUP BY mapping_method
ORDER BY n DESC;

-- AUDIT: manual_required_count
SELECT COUNT(*) AS manual_required_rows,
       COUNT(DISTINCT raw_item_name) AS manual_required_items
FROM spec_mapping
WHERE mapping_method = 'manual_required';

-- AUDIT: confidence_overrated_candidates
-- confidence の過大評価候補（推定なのに高すぎる／根拠 notes がない高confidence）
SELECT m.company, m.product_id, m.raw_item_name, m.canonical_item,
       m.mapping_method, m.confidence, m.notes
FROM spec_mapping m
WHERE (m.mapping_method = 'inferred' AND m.confidence > 0.8)
   OR (m.mapping_method IN ('pattern', 'unit_based') AND m.confidence > 0.9)
   OR (m.mapping_method NOT IN ('exact', 'synonym') AND m.confidence >= 0.9
       AND (m.notes IS NULL OR m.notes = ''))
ORDER BY m.confidence DESC, m.company;

-- AUDIT: auto_mapped_should_be_manual_candidates
-- 本来 manual_required にすべき疑いのある自動マッピング（低confidence の推定でnotesなし）
SELECT m.company, m.product_id, m.raw_item_name, m.canonical_item,
       m.mapping_method, m.confidence, m.notes
FROM spec_mapping m
WHERE m.canonical_item IS NOT NULL
  AND m.mapping_method IN ('inferred', 'unit_based')
  AND m.confidence > 0 AND m.confidence < 0.6
ORDER BY m.confidence, m.company;

-- AUDIT: risky_semantic_mappings
-- 重点確認: 意味の違う項目を同じ canonical_item に統合している疑いの候補
-- （exact 以外で、混同しやすい語を含む項目のマッピングを全件列挙する）
WITH risk(rule_name, item_pattern, concern) AS (
    VALUES
        ('weight_variants', '(重量|質量|weight|mass)',
         '重量・質量・本体重量・梱包重量（キャブ付き/なし等）の混同'),
        ('rated_vs_max', '(最大|定格|標準|平均|max|rated|nominal|average)',
         '最大値・定格値・標準値・平均値の混同'),
        ('power_consumption', '(消費電力|待機電力|power\s*consumption|standby)',
         '消費電力・最大消費電力・待機電力の混同'),
        ('dimensions', '(全長|全幅|全高|奥行|外形寸法|dimension)',
         '幅・高さ・奥行・外形寸法の分解ミス'),
        ('standards_certs', '(規格|認証|準拠|適合|standard|certifi|complian)',
         '対応規格・取得認証・準拠規格の混同'),
        ('optional_vs_standard', '(オプション|option)',
         'オプション対応と標準対応の混同'),
        ('temperature_range', '(温度|temperature)',
         '使用温度と保管温度の混同')
)
SELECT k.rule_name, k.concern, m.company, p.product_name, m.raw_item_name,
       m.canonical_item, m.mapping_method, m.confidence, m.notes
FROM spec_mapping m
JOIN risk k ON regexp_matches(m.raw_item_name, k.item_pattern, 'i')
LEFT JOIN products p USING (product_id)
WHERE m.canonical_item IS NOT NULL
  AND m.mapping_method <> 'exact'
ORDER BY k.rule_name, m.canonical_item, m.confidence DESC;

-- AUDIT: risky_group_merges
-- 重点確認: 同じリスク語群の「異なる raw_item_name」が同一 canonical_item に統合されている
-- （例: 「本体重量」と「梱包重量」が両方 operating_weight → 混同の強い疑い）
WITH risk(rule_name, item_pattern, concern) AS (
    VALUES
        ('weight_variants', '(重量|質量|weight|mass)',
         '重量・質量・本体重量・梱包重量（キャブ付き/なし等）の混同'),
        ('rated_vs_max', '(最大|定格|標準|平均|max|rated|nominal|average)',
         '最大値・定格値・標準値・平均値の混同'),
        ('power_consumption', '(消費電力|待機電力|power\s*consumption|standby)',
         '消費電力・最大消費電力・待機電力の混同'),
        ('dimensions', '(全長|全幅|全高|奥行|外形寸法|dimension)',
         '幅・高さ・奥行・外形寸法の分解ミス'),
        ('standards_certs', '(規格|認証|準拠|適合|standard|certifi|complian)',
         '対応規格・取得認証・準拠規格の混同'),
        ('optional_vs_standard', '(オプション|option)',
         'オプション対応と標準対応の混同'),
        ('temperature_range', '(温度|temperature)',
         '使用温度と保管温度の混同')
)
SELECT k.rule_name, k.concern, m.canonical_item,
       COUNT(DISTINCT m.raw_item_name) AS distinct_raw_items,
       string_agg(DISTINCT m.raw_item_name, ' | ') AS raw_item_names,
       string_agg(DISTINCT m.company, ' | ') AS companies,
       MIN(m.confidence) AS min_confidence
FROM spec_mapping m
JOIN risk k ON regexp_matches(m.raw_item_name, k.item_pattern, 'i')
WHERE m.canonical_item IS NOT NULL
GROUP BY k.rule_name, k.concern, m.canonical_item
HAVING COUNT(DISTINCT m.raw_item_name) > 1
ORDER BY distinct_raw_items DESC, k.rule_name;

-- AUDIT: mapping_success_by_company
-- company 別のマッピング成功率
SELECT company,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND mapping_method <> 'manual_required') AS mapped,
       COUNT(*) FILTER (WHERE canonical_item IS NULL OR mapping_method = 'manual_required') AS unmapped,
       ROUND(100.0 * COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND mapping_method <> 'manual_required')
             / NULLIF(COUNT(*), 0), 1) AS mapped_pct,
       ROUND(AVG(confidence) FILTER (WHERE canonical_item IS NOT NULL), 3) AS avg_confidence
FROM spec_mapping
GROUP BY company
ORDER BY company;
