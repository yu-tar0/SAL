-- 02_data_preservation_audit.sql
-- 目的: データ保全の監査。raw データが保持され、normalized 側から raw 側・元テーブルへ遡れるかを確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。

-- AUDIT: uncovered_source_tables
-- raw_specs に取り込まれていない元テーブル（標準化オブジェクトを除く BASE TABLE）
SELECT t.table_name
FROM information_schema.tables t
WHERE t.table_schema = 'main'
  AND t.table_type = 'BASE TABLE'
  AND t.table_name NOT IN (
      'products', 'raw_specs', 'canonical_specs', 'spec_mapping', 'normalized_specs',
      'normalization_issues', 'spec_synonyms', 'spec_patterns', 'unit_conversions')
  AND t.table_name NOT IN (
      SELECT DISTINCT source_table FROM raw_specs WHERE source_table IS NOT NULL)
ORDER BY t.table_name;

-- AUDIT: raw_specs_source_gaps
-- raw_specs の source 情報（元テーブル・元行・元列）の欠落件数
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE source_table IS NULL OR source_table = '') AS missing_source_table,
    COUNT(*) FILTER (WHERE source_row_id IS NULL) AS missing_source_row_id,
    COUNT(*) FILTER (WHERE source_column IS NULL OR source_column = '') AS missing_source_column
FROM raw_specs;

-- AUDIT: normalized_specs_source_gaps
-- normalized_specs の source 情報と original_value（元値）の欠落件数
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE source_table IS NULL OR source_table = '') AS missing_source_table,
    COUNT(*) FILTER (WHERE source_row_id IS NULL) AS missing_source_row_id,
    COUNT(*) FILTER (WHERE value_status = 'present'
                     AND (original_value IS NULL OR original_value = '')) AS present_missing_original_value,
    COUNT(*) FILTER (WHERE value_status = 'present'
                     AND normalized_value_numeric IS NOT NULL
                     AND (original_unit IS NULL OR original_unit = '')
                     AND (normalized_unit IS NOT NULL AND normalized_unit <> '')) AS numeric_missing_original_unit
FROM normalized_specs;

-- AUDIT: normalized_to_raw_traceability
-- normalized 側の行が raw_specs の行（product_id + source_table + source_row_id + source_column）へ戻れるか
SELECT
    (SELECT COUNT(*) FROM normalized_specs) AS normalized_rows,
    (SELECT COUNT(*) FROM normalized_specs n
      WHERE NOT EXISTS (
          SELECT 1 FROM raw_specs r
          WHERE r.product_id = n.product_id
            AND r.source_table IS NOT DISTINCT FROM n.source_table
            AND r.source_row_id IS NOT DISTINCT FROM n.source_row_id
            AND r.source_column IS NOT DISTINCT FROM n.source_column)
    ) AS not_traceable_rows;

-- AUDIT: normalized_not_traceable_examples
SELECT n.normalized_id, n.product_id, n.company, n.canonical_item,
       n.source_table, n.source_row_id, n.source_column, n.original_value
FROM normalized_specs n
WHERE NOT EXISTS (
    SELECT 1 FROM raw_specs r
    WHERE r.product_id = n.product_id
      AND r.source_table IS NOT DISTINCT FROM n.source_table
      AND r.source_row_id IS NOT DISTINCT FROM n.source_row_id
      AND r.source_column IS NOT DISTINCT FROM n.source_column)
ORDER BY n.product_id, n.canonical_item
LIMIT 100;

-- AUDIT: mapping_source_gaps
-- spec_mapping の source 情報の欠落件数
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE source_table IS NULL OR source_table = '') AS missing_source_table,
    COUNT(*) FILTER (WHERE raw_item_name IS NULL OR raw_item_name = '') AS missing_raw_item_name,
    COUNT(*) FILTER (WHERE product_id IS NULL OR product_id = '') AS missing_product_id
FROM spec_mapping;

-- AUDIT: raw_source_row_reachability
-- raw_specs が指す元テーブルが実在するか（DROP されていないか）
SELECT r.source_table, COUNT(*) AS raw_rows,
       CASE WHEN t.table_name IS NULL THEN 'NG: 元テーブルが存在しない' ELSE 'OK' END AS check_result
FROM raw_specs r
LEFT JOIN information_schema.tables t
    ON t.table_schema = 'main' AND t.table_name = r.source_table
GROUP BY r.source_table, t.table_name
ORDER BY check_result DESC, r.source_table;
