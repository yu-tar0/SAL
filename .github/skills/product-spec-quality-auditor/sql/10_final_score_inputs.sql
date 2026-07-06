-- 10_final_score_inputs.sql
-- 目的: スコアリングに使う数値指標を metric / value の縦持ちで出力する。
--       scripts/generate_audit_report.py がこの結果（score_inputs_*.csv）を読んで点数化する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。
-- 注意: 依存テーブルが無いブロックは失敗として記録され、該当カテゴリは 0 点評価になる。

-- AUDIT: score_inputs_inventory
WITH expected(object_name) AS (
    VALUES ('products'), ('raw_specs'), ('canonical_specs'), ('spec_mapping'),
           ('normalized_specs'), ('normalization_issues'),
           ('product_comparison_core_view'), ('product_comparison_full_view')
)
SELECT 'expected_objects_missing' AS metric, CAST(COUNT(*) AS DOUBLE) AS value
FROM expected e
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables t
    WHERE t.table_schema = 'main' AND t.table_name = e.object_name);

-- AUDIT: score_inputs_products
SELECT 'products_total' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM products;

-- AUDIT: score_inputs_raw
SELECT 'raw_rows_total' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM raw_specs
UNION ALL
SELECT 'raw_missing_source', CAST(COUNT(*) AS DOUBLE) FROM raw_specs
 WHERE source_table IS NULL OR source_table = '' OR source_row_id IS NULL
UNION ALL
SELECT 'raw_missing_product_link', CAST(COUNT(*) AS DOUBLE) FROM raw_specs
 WHERE company IS NULL OR company = '' OR product_id IS NULL OR product_id = ''
UNION ALL
SELECT 'raw_duplicate_groups', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT 1 FROM raw_specs
    GROUP BY company, product_id, source_table, source_row_id, source_column, raw_item_name
    HAVING COUNT(*) > 1)
UNION ALL
SELECT 'raw_unit_not_separated', CAST(COUNT(*) AS DOUBLE) FROM raw_specs
 WHERE (raw_unit IS NULL OR raw_unit = '')
   AND raw_value_text IS NOT NULL
   AND regexp_matches(raw_value_text,
       '^[0-9][0-9,\.]*\s*(kg|t|mm|cm|m|km/h|mph|kw|ps|hp|l|min-1|rpm|mpa|kpa|psi|lb|lbs|in|ft|gpm|kn|n|cc|ah|kwh|v|a|db)\s*$', 'i')
UNION ALL
SELECT 'products_without_raw', CAST(COUNT(*) AS DOUBLE) FROM products p
 WHERE NOT EXISTS (SELECT 1 FROM raw_specs r WHERE r.product_id = p.product_id)
UNION ALL
SELECT 'raw_products_not_in_master', CAST(COUNT(DISTINCT r.product_id) AS DOUBLE) FROM raw_specs r
 WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = r.product_id);

-- AUDIT: score_inputs_canonical
SELECT 'canonical_items_total' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM canonical_specs
UNION ALL
SELECT 'canonical_field_gaps', CAST(COUNT(*) AS DOUBLE) FROM canonical_specs
 WHERE category IS NULL OR category = '' OR priority IS NULL
    OR value_type IS NULL OR value_type = ''
UNION ALL
SELECT 'canonical_dup_display_names', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT display_name_ja FROM canonical_specs GROUP BY display_name_ja HAVING COUNT(*) > 1)
UNION ALL
SELECT 'canonical_unused', CAST(COUNT(*) AS DOUBLE) FROM canonical_specs c
 WHERE NOT EXISTS (SELECT 1 FROM spec_mapping m WHERE m.canonical_item = c.canonical_item)
   AND NOT EXISTS (SELECT 1 FROM normalized_specs n WHERE n.canonical_item = c.canonical_item)
UNION ALL
SELECT 'priority1_avg_coverage_pct', COALESCE(AVG(cov), 0) FROM (
    SELECT 100.0 * COUNT(DISTINCT b.product_id)
           / NULLIF((SELECT COUNT(*) FROM products), 0) AS cov
    FROM canonical_specs c
    LEFT JOIN best_normalized_specs b USING (canonical_item)
    WHERE c.priority = 1
    GROUP BY c.canonical_item);

-- AUDIT: score_inputs_mapping
SELECT 'mapping_rows_total' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM spec_mapping
UNION ALL
SELECT 'mapping_unmapped', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping
 WHERE canonical_item IS NULL OR mapping_method = 'manual_required'
UNION ALL
SELECT 'mapping_conf_lt_070', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping
 WHERE canonical_item IS NOT NULL AND confidence > 0 AND confidence < 0.7
UNION ALL
SELECT 'mapping_conf_lt_050', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping
 WHERE canonical_item IS NOT NULL AND confidence > 0 AND confidence < 0.5
UNION ALL
SELECT 'mapping_multi_canonical_groups', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT company, raw_item_name FROM spec_mapping
    WHERE canonical_item IS NOT NULL
    GROUP BY company, raw_item_name
    HAVING COUNT(DISTINCT canonical_item) > 1)
UNION ALL
SELECT 'mapping_manual_required', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping
 WHERE mapping_method = 'manual_required'
UNION ALL
SELECT 'mapping_overrated_confidence', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping m
 WHERE (m.mapping_method = 'inferred' AND m.confidence > 0.8)
    OR (m.mapping_method IN ('pattern', 'unit_based') AND m.confidence > 0.9)
    OR (m.mapping_method NOT IN ('exact', 'synonym') AND m.confidence >= 0.9
        AND (m.notes IS NULL OR m.notes = ''))
UNION ALL
SELECT 'risky_group_merges', CAST(COUNT(*) AS DOUBLE) FROM (
    WITH risk(rule_name, item_pattern) AS (
        VALUES
            ('weight_variants', '(重量|質量|weight|mass)'),
            ('rated_vs_max', '(最大|定格|標準|平均|max|rated|nominal|average)'),
            ('power_consumption', '(消費電力|待機電力|power\s*consumption|standby)'),
            ('dimensions', '(全長|全幅|全高|奥行|外形寸法|dimension)'),
            ('standards_certs', '(規格|認証|準拠|適合|standard|certifi|complian)'),
            ('optional_vs_standard', '(オプション|option)'),
            ('temperature_range', '(温度|temperature)')
    )
    SELECT k.rule_name, m.canonical_item
    FROM spec_mapping m
    JOIN risk k ON regexp_matches(m.raw_item_name, k.item_pattern, 'i')
    WHERE m.canonical_item IS NOT NULL
    GROUP BY k.rule_name, m.canonical_item
    HAVING COUNT(DISTINCT m.raw_item_name) > 1);

-- AUDIT: score_inputs_normalized
SELECT 'normalized_present_rows' AS metric, CAST(COUNT(*) AS DOUBLE) AS value
FROM normalized_specs WHERE value_status = 'present'
UNION ALL
SELECT 'unit_mismatch_rows', CAST(COUNT(*) AS DOUBLE)
FROM normalized_specs n JOIN canonical_specs c USING (canonical_item)
 WHERE n.value_status = 'present'
   AND c.canonical_unit IS NOT NULL AND c.canonical_unit <> ''
   AND n.normalized_unit IS DISTINCT FROM c.canonical_unit
UNION ALL
SELECT 'numeric_parse_failures', CAST(COUNT(*) AS DOUBLE)
FROM normalized_specs n JOIN canonical_specs c USING (canonical_item)
 WHERE c.value_type = 'numeric' AND n.value_status = 'present'
   AND n.normalized_value_numeric IS NULL
UNION ALL
SELECT 'duplicate_conflicting_pairs', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT n.product_id, n.canonical_item
    FROM normalized_specs n
    WHERE n.value_status IN ('present', 'optional')
    GROUP BY n.product_id, n.canonical_item
    HAVING COUNT(*) > 1
       AND COUNT(DISTINCT COALESCE(CAST(n.normalized_value_numeric AS VARCHAR), n.normalized_value_text)) > 1)
UNION ALL
SELECT 'normalized_conf_lt_070', CAST(COUNT(*) AS DOUBLE) FROM normalized_specs
 WHERE value_status = 'present' AND confidence IS NOT NULL AND confidence < 0.7
UNION ALL
SELECT 'notes_missing_low_conf', CAST(COUNT(*) AS DOUBLE) FROM normalized_specs
 WHERE value_status = 'present' AND confidence IS NOT NULL AND confidence < 0.8
   AND (notes IS NULL OR notes = '')
UNION ALL
SELECT 'normalized_missing_original', CAST(COUNT(*) AS DOUBLE) FROM normalized_specs
 WHERE value_status = 'present' AND (original_value IS NULL OR original_value = '')
UNION ALL
SELECT 'normalized_zero_or_negative', CAST(COUNT(*) AS DOUBLE) FROM normalized_specs
 WHERE value_status = 'present' AND normalized_value_numeric IS NOT NULL
   AND normalized_value_numeric <= 0;

-- AUDIT: score_inputs_traceability
SELECT 'normalized_not_traceable' AS metric, CAST(COUNT(*) AS DOUBLE) AS value
FROM normalized_specs n
WHERE NOT EXISTS (
    SELECT 1 FROM raw_specs r
    WHERE r.product_id = n.product_id
      AND r.source_table IS NOT DISTINCT FROM n.source_table
      AND r.source_row_id IS NOT DISTINCT FROM n.source_row_id
      AND r.source_column IS NOT DISTINCT FROM n.source_column)
UNION ALL
SELECT 'uncovered_source_tables', CAST(COUNT(*) AS DOUBLE)
FROM information_schema.tables t
WHERE t.table_schema = 'main'
  AND t.table_type = 'BASE TABLE'
  AND t.table_name NOT IN (
      'products', 'raw_specs', 'canonical_specs', 'spec_mapping', 'normalized_specs',
      'normalization_issues', 'spec_synonyms', 'spec_patterns', 'unit_conversions')
  AND t.table_name NOT IN (
      SELECT DISTINCT source_table FROM raw_specs WHERE source_table IS NOT NULL);

-- AUDIT: score_inputs_comparison
SELECT 'core_rows' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM product_comparison_core_view
UNION ALL
SELECT 'core_dup_products', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT product_id FROM product_comparison_core_view GROUP BY product_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'full_rows', CAST(COUNT(*) AS DOUBLE) FROM product_comparison_full_view
UNION ALL
SELECT 'core_columns_missing_ge80', CAST(COUNT(*) AS DOUBLE) FROM (
    SELECT column_name FROM (SUMMARIZE product_comparison_core_view)
    WHERE TRY_CAST(replace(CAST(null_percentage AS VARCHAR), '%', '') AS DOUBLE) >= 80.0);

-- AUDIT: score_inputs_issues
SELECT 'issues_total' AS metric, CAST(COUNT(*) AS DOUBLE) AS value FROM normalization_issues
UNION ALL
SELECT 'issues_open', CAST(COUNT(*) AS DOUBLE) FROM normalization_issues WHERE status = 'open'
UNION ALL
SELECT 'issues_missing_reference', CAST(COUNT(*) AS DOUBLE) FROM normalization_issues
 WHERE (product_id IS NULL OR product_id = '') AND (raw_item_name IS NULL OR raw_item_name = '')
UNION ALL
SELECT 'low_conf_not_issued', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping m
 WHERE m.canonical_item IS NOT NULL AND m.confidence > 0 AND m.confidence < 0.7
   AND NOT EXISTS (
       SELECT 1 FROM normalization_issues i
       WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
         AND (i.product_id IS NULL OR i.product_id = m.product_id))
UNION ALL
SELECT 'unmapped_not_issued', CAST(COUNT(*) AS DOUBLE) FROM spec_mapping m
 WHERE (m.canonical_item IS NULL OR m.mapping_method = 'manual_required')
   AND NOT EXISTS (
       SELECT 1 FROM normalization_issues i
       WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
         AND (i.product_id IS NULL OR i.product_id = m.product_id));
