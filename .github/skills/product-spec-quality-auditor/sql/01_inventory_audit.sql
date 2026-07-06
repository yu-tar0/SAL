-- 01_inventory_audit.sql
-- 目的: DB オブジェクトの棚卸し。期待するテーブル・ビューの存在、件数、列定義を確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。
-- 実行: scripts/run_audit.py が「-- AUDIT: <名前>」単位で分割して実行する。
--       対象オブジェクトが存在しない場合、そのブロックは失敗として記録される（不足の証跡になる）。

-- AUDIT: tables_list
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_type, table_name;

-- AUDIT: expected_objects_presence
WITH expected(object_name, expected_kind) AS (
    VALUES
        ('products', 'BASE TABLE'),
        ('raw_specs', 'BASE TABLE'),
        ('canonical_specs', 'BASE TABLE'),
        ('spec_mapping', 'BASE TABLE'),
        ('normalized_specs', 'BASE TABLE'),
        ('normalization_issues', 'BASE TABLE'),
        ('spec_synonyms', 'BASE TABLE'),
        ('spec_patterns', 'BASE TABLE'),
        ('unit_conversions', 'BASE TABLE'),
        ('best_normalized_specs', 'VIEW'),
        ('product_comparison_core_view', 'VIEW'),
        ('product_comparison_full_view', 'VIEW')
)
SELECT
    e.object_name,
    e.expected_kind,
    CASE WHEN t.table_name IS NULL THEN 'MISSING' ELSE 'OK' END AS presence,
    t.table_type AS actual_kind
FROM expected e
LEFT JOIN information_schema.tables t
    ON t.table_schema = 'main' AND t.table_name = e.object_name
ORDER BY presence DESC, e.object_name;

-- AUDIT: standard_object_columns
SELECT table_name, ordinal_position, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'main'
  AND table_name IN (
      'products', 'raw_specs', 'canonical_specs', 'spec_mapping',
      'normalized_specs', 'normalization_issues',
      'best_normalized_specs',
      'product_comparison_core_view', 'product_comparison_full_view')
ORDER BY table_name, ordinal_position;

-- AUDIT: row_count_products
SELECT 'products' AS table_name, COUNT(*) AS row_count FROM products;

-- AUDIT: row_count_raw_specs
SELECT 'raw_specs' AS table_name, COUNT(*) AS row_count FROM raw_specs;

-- AUDIT: row_count_canonical_specs
SELECT 'canonical_specs' AS table_name, COUNT(*) AS row_count FROM canonical_specs;

-- AUDIT: row_count_spec_mapping
SELECT 'spec_mapping' AS table_name, COUNT(*) AS row_count FROM spec_mapping;

-- AUDIT: row_count_normalized_specs
SELECT 'normalized_specs' AS table_name, COUNT(*) AS row_count FROM normalized_specs;

-- AUDIT: row_count_normalization_issues
SELECT 'normalization_issues' AS table_name, COUNT(*) AS row_count FROM normalization_issues;

-- AUDIT: row_count_best_normalized_specs
SELECT 'best_normalized_specs' AS table_name, COUNT(*) AS row_count FROM best_normalized_specs;

-- AUDIT: row_count_comparison_core_view
SELECT 'product_comparison_core_view' AS table_name, COUNT(*) AS row_count FROM product_comparison_core_view;

-- AUDIT: row_count_comparison_full_view
SELECT 'product_comparison_full_view' AS table_name, COUNT(*) AS row_count FROM product_comparison_full_view;
