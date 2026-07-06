-- 04_canonical_specs_audit.sql
-- 目的: canonical_specs 品質の監査。比較軸としての妥当性・定義の欠落・未使用項目を確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。
-- 注意: 「比較軸として妥当か」「抽象的すぎないか」の最終判断は人間/エージェントのレビュー。
--       ここでは判断材料（全定義・機械的に検出できる候補）を出す。

-- AUDIT: canonical_definitions
SELECT canonical_item, display_name_ja, display_name_en, category, canonical_unit,
       value_type, priority, comparison_flag, description
FROM canonical_specs
ORDER BY category, priority, canonical_item;

-- AUDIT: canonical_field_gaps
-- 定義の欠落・想定外値（numeric なのに単位なし等。単位を持たない数値項目もあるため REVIEW 扱い）
SELECT canonical_item, category, canonical_unit, value_type, priority, issue
FROM (
    SELECT *,
        CASE
            WHEN category IS NULL OR category = '' THEN 'NG: category が未定義'
            WHEN priority IS NULL THEN 'NG: priority が未定義'
            WHEN value_type IS NULL OR value_type = '' THEN 'NG: value_type が未定義'
            WHEN value_type NOT IN ('numeric', 'integer', 'text', 'boolean') THEN 'REVIEW: value_type が想定外'
            WHEN value_type IN ('numeric') AND (canonical_unit IS NULL OR canonical_unit = '')
                THEN 'REVIEW: numeric なのに canonical_unit が未定義（無次元数なら OK）'
        END AS issue
    FROM canonical_specs)
WHERE issue IS NOT NULL
ORDER BY issue, canonical_item;

-- AUDIT: canonical_duplicate_display_names
-- 表示名の重複（同じ意味の項目を二重定義している疑い）
SELECT display_name_ja, COUNT(*) AS n,
       string_agg(canonical_item, ' | ') AS canonical_items
FROM canonical_specs
GROUP BY display_name_ja
HAVING COUNT(*) > 1
ORDER BY n DESC;

-- AUDIT: canonical_unused_items
-- マッピングにも normalized にも一度も使われていない標準項目（定義過剰の疑い）
SELECT c.canonical_item, c.display_name_ja, c.category, c.priority
FROM canonical_specs c
WHERE NOT EXISTS (SELECT 1 FROM spec_mapping m WHERE m.canonical_item = c.canonical_item)
  AND NOT EXISTS (SELECT 1 FROM normalized_specs n WHERE n.canonical_item = c.canonical_item)
ORDER BY c.priority, c.canonical_item;

-- AUDIT: canonical_abstract_name_candidates
-- 抽象的すぎる項目名の候補（人間レビュー用）
SELECT canonical_item, display_name_ja, category, priority
FROM canonical_specs
WHERE regexp_matches(canonical_item, '(other|misc|general|spec|value|info|data)s?$', 'i')
   OR regexp_matches(display_name_ja, '(その他|一般|情報|データ|各種)')
ORDER BY canonical_item;

-- AUDIT: canonical_product_coverage
-- canonical_item 別の製品カバー率（priority が高いのにカバー率が低い項目は比較軸として機能していない）
SELECT c.canonical_item, c.display_name_ja, c.category, c.priority,
       COUNT(DISTINCT b.product_id) AS products_covered,
       (SELECT COUNT(*) FROM products) AS products_total,
       ROUND(100.0 * COUNT(DISTINCT b.product_id)
             / NULLIF((SELECT COUNT(*) FROM products), 0), 1) AS coverage_pct
FROM canonical_specs c
LEFT JOIN best_normalized_specs b USING (canonical_item)
GROUP BY c.canonical_item, c.display_name_ja, c.category, c.priority
ORDER BY c.priority, coverage_pct, c.canonical_item;

-- AUDIT: canonical_company_specific_candidates
-- 1社の項目しかマッピングされていない canonical 項目（会社固有項目を標準化してしまった疑い）
SELECT m.canonical_item, c.priority,
       COUNT(DISTINCT m.company) AS n_companies,
       string_agg(DISTINCT m.company, ' | ') AS companies,
       COUNT(DISTINCT m.raw_item_name) AS distinct_raw_items
FROM spec_mapping m
JOIN canonical_specs c ON c.canonical_item = m.canonical_item
GROUP BY m.canonical_item, c.priority
HAVING COUNT(DISTINCT m.company) <= 1
ORDER BY c.priority, m.canonical_item;
