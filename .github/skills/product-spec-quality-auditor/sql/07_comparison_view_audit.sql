-- 07_comparison_view_audit.sql
-- 目的: 比較ビュー品質の監査。1行1製品・重複・欠損率・主要項目のカバーを確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。
-- 注意: 列名の分かりやすさ・数値/テキスト混在の最終判断は missing_rates の column_type と
--       サンプル出力を見て人間/エージェントが行う。

-- AUDIT: comparison_core_counts
-- 製品数の整合（products と core ビューの行数・製品数が一致するはず）
SELECT
    (SELECT COUNT(*) FROM products) AS products_total,
    (SELECT COUNT(*) FROM product_comparison_core_view) AS core_rows,
    (SELECT COUNT(DISTINCT product_id) FROM product_comparison_core_view) AS core_distinct_products;

-- AUDIT: comparison_full_counts
SELECT
    (SELECT COUNT(*) FROM products) AS products_total,
    (SELECT COUNT(*) FROM product_comparison_full_view) AS full_rows,
    (SELECT COUNT(DISTINCT product_id) FROM product_comparison_full_view) AS full_distinct_products;

-- AUDIT: comparison_core_duplicates
-- 同一製品の重複（0行が正常）
SELECT product_id, COUNT(*) AS n
FROM product_comparison_core_view
GROUP BY product_id
HAVING COUNT(*) > 1;

-- AUDIT: comparison_full_duplicates
SELECT product_id, COUNT(*) AS n
FROM product_comparison_full_view
GROUP BY product_id
HAVING COUNT(*) > 1;

-- AUDIT: comparison_core_missing_rates
-- core ビューの列ごとの欠損率と型（列名の妥当性・数値/テキスト混在の確認材料）
SELECT column_name, column_type, count AS total_rows, null_percentage
FROM (SUMMARIZE product_comparison_core_view)
ORDER BY null_percentage DESC, column_name;

-- AUDIT: comparison_full_missing_rates
SELECT column_name, column_type, count AS total_rows, null_percentage
FROM (SUMMARIZE product_comparison_full_view)
ORDER BY null_percentage DESC, column_name;

-- AUDIT: comparison_core_sample
-- 目視レビュー用サンプル（比較表として読めるか）
SELECT *
FROM product_comparison_core_view
ORDER BY company, product_name
LIMIT 30;

-- AUDIT: priority1_coverage_in_views
-- priority=1（最重要比較項目）の製品カバー状況。カバーの低い項目はビューでも欠損だらけになる
SELECT c.canonical_item, c.display_name_ja, c.priority,
       COUNT(DISTINCT b.product_id) AS products_covered,
       (SELECT COUNT(*) FROM products) AS products_total,
       ROUND(100.0 * COUNT(DISTINCT b.product_id)
             / NULLIF((SELECT COUNT(*) FROM products), 0), 1) AS coverage_pct
FROM canonical_specs c
LEFT JOIN best_normalized_specs b USING (canonical_item)
WHERE c.priority = 1
GROUP BY c.canonical_item, c.display_name_ja, c.priority
ORDER BY coverage_pct, c.canonical_item;

-- AUDIT: important_items_not_in_views
-- normalized には値があるのに比較ビュー（core/full の対象 priority）から漏れている可能性のある項目
-- （priority <= 2 でカバー率が高いのにビュー定義に含まれていない項目は列追加漏れの疑い。
--   ビューの列は information_schema からは canonical_item 名に戻せないため、レビュー材料として
--   「priority<=2 かつ製品カバーが2社以上」の項目一覧を出す）
SELECT c.canonical_item, c.display_name_ja, c.priority, c.value_type,
       COUNT(DISTINCT b.product_id) AS products_covered,
       COUNT(DISTINCT b.company) AS companies_covered
FROM canonical_specs c
JOIN best_normalized_specs b USING (canonical_item)
WHERE c.priority <= 2
GROUP BY c.canonical_item, c.display_name_ja, c.priority, c.value_type
ORDER BY c.priority, products_covered DESC;
