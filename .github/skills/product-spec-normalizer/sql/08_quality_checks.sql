-- 08_quality_checks.sql
-- 品質チェック用クエリ集。scripts/export_review_files.py が各クエリを CSV に書き出す。
-- クエリの区切りは「-- CHECK: <名前>」コメント。手動実行する場合は個別に流してよい。

-- CHECK: unmapped_items
-- 1. マッピングされていない raw_item_name（会社×項目で集約し、サンプル値を添える）
SELECT m.company, m.raw_item_name, count(*) AS n_products,
       any_value(m.source_table) AS sample_table,
       (SELECT any_value(r.raw_value_text) FROM raw_specs r
         WHERE r.company = m.company AND r.raw_item_name = m.raw_item_name) AS sample_value
FROM spec_mapping m
WHERE m.mapping_method = 'manual_required'
GROUP BY m.company, m.raw_item_name
ORDER BY m.company, n_products DESC, m.raw_item_name;

-- CHECK: low_confidence_mappings
-- 2. confidence が低い（<0.7）マッピング
SELECT company, raw_item_name, canonical_item, mapping_method, confidence, notes,
       count(*) AS n_products
FROM spec_mapping
WHERE canonical_item IS NOT NULL AND confidence < 0.7
GROUP BY ALL
ORDER BY confidence, company, raw_item_name;

-- CHECK: unit_mismatches
-- 3. canonical_unit と original_unit が不整合（変換ルールが無く数値化できなかったもの）
SELECT company, product_id, canonical_item, original_unit,
       (SELECT canonical_unit FROM canonical_specs c WHERE c.canonical_item = n.canonical_item) AS canonical_unit,
       original_value, source_table
FROM normalized_specs n
WHERE notes LIKE '%[unit_no_rule]%' OR notes LIKE '%[unit_missing]%'
ORDER BY canonical_item, company;

-- CHECK: duplicate_values
-- 4. 同一製品×同一 canonical_item に異なる正規化値が複数あるもの（採用値の妥当性確認用）
SELECT product_id, canonical_item,
       count(*) AS n_rows,
       count(DISTINCT coalesce(cast(normalized_value_numeric AS VARCHAR), normalized_value_text)) AS n_distinct_values,
       min(normalized_value_numeric) AS min_value,
       max(normalized_value_numeric) AS max_value,
       string_agg(DISTINCT source_table, ' | ') AS sources
FROM normalized_specs
WHERE value_status = 'present'
GROUP BY product_id, canonical_item
HAVING count(DISTINCT coalesce(cast(normalized_value_numeric AS VARCHAR), normalized_value_text)) > 1
ORDER BY n_distinct_values DESC, product_id, canonical_item;

-- CHECK: numeric_parse_failures
-- 5. 数値型として扱うべきだが数値化できなかったもの
SELECT company, product_id, canonical_item, original_value, original_unit, source_table, notes
FROM normalized_specs
WHERE value_type = 'numeric' AND value_status = 'present' AND normalized_value_numeric IS NULL
ORDER BY canonical_item, company, product_id;

-- CHECK: high_missing_rate_items
-- 6. 比較ビューで欠損率が高い項目（priority<=2 の数値項目について製品カバレッジを見る）
WITH target_products AS (
    SELECT product_id FROM products
    WHERE coalesce(market_segment, '') NOT IN ('SAL外の近接機種')
),
coverage AS (
    SELECT c.canonical_item, c.priority, c.category,
           count(DISTINCT b.product_id) AS n_products_with_value
    FROM canonical_specs c
    LEFT JOIN best_normalized_specs b
      ON b.canonical_item = c.canonical_item
     AND b.product_id IN (SELECT product_id FROM target_products)
     AND (b.normalized_value_numeric IS NOT NULL OR b.normalized_value_text IS NOT NULL)
    WHERE c.priority <= 2 AND c.comparison_flag
    GROUP BY ALL
)
SELECT canonical_item, priority, category, n_products_with_value,
       (SELECT count(*) FROM target_products) AS n_products_total,
       round(1.0 - n_products_with_value * 1.0 / (SELECT count(*) FROM target_products), 2) AS missing_rate
FROM coverage
ORDER BY missing_rate DESC, priority, canonical_item;

-- CHECK: company_skewed_items
-- 7. 会社ごとに項目の出どころが大きく偏っているもの（1社にしか無い canonical_item など）
SELECT b.canonical_item,
       count(DISTINCT b.company) AS n_companies,
       count(DISTINCT b.product_id) AS n_products,
       string_agg(DISTINCT b.company, ' | ') AS companies
FROM best_normalized_specs b
GROUP BY b.canonical_item
HAVING count(DISTINCT b.company) <= 2
ORDER BY n_companies, b.canonical_item;

-- CHECK: open_issues
-- 8. 未解決の normalization_issues のサマリー
SELECT issue_type, severity, count(*) AS n, string_agg(DISTINCT company, ' | ') AS companies
FROM normalization_issues
WHERE status = 'open'
GROUP BY issue_type, severity
ORDER BY n DESC;

-- CHECK: uncovered_source_tables
-- 9. raw_specs に取り込まれていない元テーブル（スコープ判断の再確認用）
SELECT e.table_name, e.sheet_name, e.row_count,
       CASE WHEN i.source_table IS NOT NULL THEN 'scope_excluded として記録済み' ELSE '未判断' END AS scope_status
FROM excel_imports e
LEFT JOIN (SELECT DISTINCT source_table FROM normalization_issues WHERE issue_type = 'scope_excluded') i
       ON i.source_table = e.table_name
WHERE e.table_name NOT IN (SELECT DISTINCT source_table FROM raw_specs)
QUALIFY row_number() OVER (PARTITION BY e.table_name ORDER BY e.loaded_at DESC) = 1
ORDER BY e.table_name;
