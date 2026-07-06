-- 03_raw_specs_audit.sql
-- 目的: raw_specs 品質の監査。取り込み網羅性・製品整合・値/単位の分離・重複を確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。

-- AUDIT: products_raw_spec_counts
-- 製品ごとの raw 仕様行数。0行＝取り込み漏れ、極端に少ない＝要確認
SELECT p.product_id, p.company, p.product_name,
       COALESCE(r.n_rows, 0) AS raw_spec_rows,
       COALESCE(r.n_items, 0) AS raw_item_count,
       CASE WHEN COALESCE(r.n_rows, 0) = 0 THEN 'NG: raw_specs に行がない'
            WHEN r.n_items < 10 THEN 'REVIEW: 仕様項目が不自然に少ない'
            ELSE 'OK' END AS check_result
FROM products p
LEFT JOIN (
    SELECT product_id, COUNT(*) AS n_rows, COUNT(DISTINCT raw_item_name) AS n_items
    FROM raw_specs GROUP BY product_id) r USING (product_id)
ORDER BY raw_spec_rows, p.company, p.product_id;

-- AUDIT: raw_products_not_in_master
-- raw_specs にあるが products マスタに存在しない製品（紐づけ欠落）
SELECT DISTINCT r.company, r.product_id, r.product_name
FROM raw_specs r
LEFT JOIN products p USING (product_id)
WHERE p.product_id IS NULL
ORDER BY r.company, r.product_id;

-- AUDIT: raw_item_counts_by_company
-- company 別の raw_item_name 数（会社間で桁が違えば取り込み漏れの疑い）
SELECT company,
       COUNT(DISTINCT raw_item_name) AS distinct_raw_items,
       COUNT(*) AS raw_rows,
       COUNT(DISTINCT product_id) AS products,
       COUNT(DISTINCT source_table) AS source_tables
FROM raw_specs
GROUP BY company
ORDER BY company;

-- AUDIT: raw_value_unit_not_separated
-- raw_unit が空なのに raw_value_text が「数値+単位」に見える行（値と単位の分離漏れ候補）
SELECT company, product_id, source_table, raw_item_name, raw_value_text
FROM raw_specs
WHERE (raw_unit IS NULL OR raw_unit = '')
  AND raw_value_text IS NOT NULL
  AND regexp_matches(raw_value_text,
      '^[0-9][0-9,\.]*\s*(kg|t|mm|cm|m|km/h|mph|kw|ps|hp|l|min-1|rpm|mpa|kpa|psi|lb|lbs|in|ft|gpm|kn|n|cc|ah|kwh|v|a|db)\s*$', 'i')
ORDER BY company, product_id, raw_item_name
LIMIT 200;

-- AUDIT: raw_value_unit_not_separated_count
SELECT COUNT(*) AS candidate_rows
FROM raw_specs
WHERE (raw_unit IS NULL OR raw_unit = '')
  AND raw_value_text IS NOT NULL
  AND regexp_matches(raw_value_text,
      '^[0-9][0-9,\.]*\s*(kg|t|mm|cm|m|km/h|mph|kw|ps|hp|l|min-1|rpm|mpa|kpa|psi|lb|lbs|in|ft|gpm|kn|n|cc|ah|kwh|v|a|db)\s*$', 'i');

-- AUDIT: raw_duplicate_rows
-- 同一（製品×元テーブル×元行×元列×項目名）の重複（縦持ち化の二重取り込み疑い）
SELECT company, product_id, source_table, source_row_id, source_column, raw_item_name,
       COUNT(*) AS n_rows
FROM raw_specs
GROUP BY ALL
HAVING COUNT(*) > 1
ORDER BY n_rows DESC
LIMIT 200;

-- AUDIT: raw_missing_links
-- 会社名・製品との紐づけ、および値そのものの欠落件数
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE company IS NULL OR company = '') AS missing_company,
    COUNT(*) FILTER (WHERE product_id IS NULL OR product_id = '') AS missing_product_id,
    COUNT(*) FILTER (WHERE product_name IS NULL OR product_name = '') AS missing_product_name,
    COUNT(*) FILTER (WHERE raw_value_text IS NULL AND raw_value_numeric IS NULL) AS missing_both_values
FROM raw_specs;

-- AUDIT: raw_items_per_source_table
-- 元テーブルごとの取り込み状況（横持ち→縦持ち化の網羅性確認の材料）
SELECT source_table,
       COUNT(*) AS raw_rows,
       COUNT(DISTINCT raw_item_name) AS distinct_items,
       COUNT(DISTINCT product_id) AS products,
       COUNT(DISTINCT source_column) AS source_columns
FROM raw_specs
GROUP BY source_table
ORDER BY source_table;
