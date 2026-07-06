-- 09_company_coverage_audit.sql
-- 目的: 会社別カバレッジの監査。特定の会社だけ取り込み・マッピング・正規化が薄くないかを確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。

-- AUDIT: company_summary
-- 会社別サマリー（製品数・raw行数・raw項目数・マッピング成功率・normalized行数・平均confidence）
WITH prod AS (
    SELECT company, COUNT(*) AS products FROM products GROUP BY company),
raw AS (
    SELECT company, COUNT(*) AS raw_rows, COUNT(DISTINCT raw_item_name) AS raw_items
    FROM raw_specs GROUP BY company),
map AS (
    SELECT company,
           COUNT(*) AS mapping_rows,
           COUNT(*) FILTER (WHERE canonical_item IS NOT NULL AND mapping_method <> 'manual_required') AS mapped_rows
    FROM spec_mapping GROUP BY company),
norm AS (
    SELECT company, COUNT(*) AS normalized_rows,
           ROUND(AVG(confidence), 3) AS avg_confidence
    FROM normalized_specs WHERE value_status = 'present' GROUP BY company)
SELECT p.company,
       p.products,
       COALESCE(r.raw_rows, 0) AS raw_rows,
       COALESCE(r.raw_items, 0) AS raw_items,
       COALESCE(m.mapping_rows, 0) AS mapping_rows,
       COALESCE(m.mapped_rows, 0) AS mapped_rows,
       ROUND(100.0 * COALESCE(m.mapped_rows, 0) / NULLIF(m.mapping_rows, 0), 1) AS mapped_pct,
       COALESCE(n.normalized_rows, 0) AS normalized_rows,
       n.avg_confidence
FROM prod p
LEFT JOIN raw r USING (company)
LEFT JOIN map m USING (company)
LEFT JOIN norm n USING (company)
ORDER BY p.company;

-- AUDIT: canonical_coverage_matrix
-- canonical_item（priority<=2）× 会社ごとのカバー製品数
SELECT c.canonical_item, c.priority, b.company,
       COUNT(DISTINCT b.product_id) AS products_covered
FROM canonical_specs c
LEFT JOIN best_normalized_specs b USING (canonical_item)
WHERE c.priority <= 2
GROUP BY c.canonical_item, c.priority, b.company
ORDER BY c.priority, c.canonical_item, b.company;

-- AUDIT: company_skewed_canonical_items
-- 1社しか値を持たない canonical 項目（比較軸として機能していない／会社固有項目の疑い）
SELECT b.canonical_item,
       COUNT(DISTINCT b.company) AS n_companies,
       string_agg(DISTINCT b.company, ' | ') AS companies,
       COUNT(DISTINCT b.product_id) AS n_products
FROM best_normalized_specs b
GROUP BY b.canonical_item
HAVING COUNT(DISTINCT b.company) <= 1
ORDER BY b.canonical_item;

-- AUDIT: company_missing_priority1
-- 会社ごとに、priority=1 の最重要項目で値が1件もないもの（取り込み/マッピング漏れの疑い）
SELECT comp.company, c.canonical_item, c.display_name_ja
FROM (SELECT DISTINCT company FROM products) comp
CROSS JOIN canonical_specs c
WHERE c.priority = 1
  AND NOT EXISTS (
      SELECT 1 FROM best_normalized_specs b
      WHERE b.company = comp.company AND b.canonical_item = c.canonical_item)
ORDER BY comp.company, c.canonical_item;
