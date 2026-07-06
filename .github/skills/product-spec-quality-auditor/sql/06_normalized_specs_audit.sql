-- 06_normalized_specs_audit.sql
-- 目的: normalized_specs 品質の監査。単位変換の正しさ・数値化の妥当性・重複・追跡可能性を確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。

-- AUDIT: unit_mismatches
-- normalized_unit が canonical_specs.canonical_unit と一致しない行
SELECT n.company, n.product_id, n.product_name, n.canonical_item,
       c.canonical_unit, n.normalized_unit, n.original_value, n.original_unit,
       n.confidence, n.notes
FROM normalized_specs n
JOIN canonical_specs c USING (canonical_item)
WHERE n.value_status = 'present'
  AND c.canonical_unit IS NOT NULL AND c.canonical_unit <> ''
  AND n.normalized_unit IS DISTINCT FROM c.canonical_unit
ORDER BY n.canonical_item, n.company, n.product_id;

-- AUDIT: unit_mismatch_count
SELECT COUNT(*) AS unit_mismatch_rows
FROM normalized_specs n
JOIN canonical_specs c USING (canonical_item)
WHERE n.value_status = 'present'
  AND c.canonical_unit IS NOT NULL AND c.canonical_unit <> ''
  AND n.normalized_unit IS DISTINCT FROM c.canonical_unit;

-- AUDIT: numeric_parse_failures
-- numeric 扱いなのに数値化できていない行
SELECT n.company, n.product_id, n.canonical_item, n.original_value, n.original_unit,
       n.normalized_value_text, n.value_status, n.confidence, n.notes
FROM normalized_specs n
JOIN canonical_specs c USING (canonical_item)
WHERE c.value_type = 'numeric'
  AND n.value_status = 'present'
  AND n.normalized_value_numeric IS NULL
ORDER BY n.canonical_item, n.company, n.product_id;

-- AUDIT: numeric_parse_failure_count
SELECT COUNT(*) AS numeric_parse_failure_rows
FROM normalized_specs n
JOIN canonical_specs c USING (canonical_item)
WHERE c.value_type = 'numeric'
  AND n.value_status = 'present'
  AND n.normalized_value_numeric IS NULL;

-- AUDIT: forced_numeric_candidates
-- 数値化すべきでないものを無理に数値化した疑いの候補（範囲・約・複合値を含む original_value）
SELECT n.company, n.product_id, n.canonical_item, n.original_value,
       n.normalized_value_numeric, n.normalized_unit, n.confidence, n.notes
FROM normalized_specs n
WHERE n.value_status = 'present'
  AND n.normalized_value_numeric IS NOT NULL
  AND n.original_value IS NOT NULL
  AND regexp_matches(n.original_value, '(約|approx|circa|〜|~|±|以上|以下|超|未満|/|または| or )', 'i')
ORDER BY n.canonical_item, n.company
LIMIT 200;

-- AUDIT: normalized_zero_or_negative
-- 物理量なのに 0 以下の値（変換ミス・パースミスの疑い）
SELECT company, product_id, canonical_item, normalized_value_numeric,
       original_value, original_unit, notes
FROM normalized_specs
WHERE value_status = 'present'
  AND normalized_value_numeric IS NOT NULL
  AND normalized_value_numeric <= 0
ORDER BY canonical_item, company;

-- AUDIT: conversion_factor_review
-- 単位ペアごとに実際に使われた変換係数を集計（同じ単位ペアで係数がばらつく＝変換バグの疑い）
SELECT original_unit, normalized_unit,
       ROUND(normalized_value_numeric
             / NULLIF(TRY_CAST(replace(original_value, ',', '') AS DOUBLE), 0), 6) AS factor,
       COUNT(*) AS n_rows
FROM normalized_specs
WHERE value_status = 'present'
  AND normalized_value_numeric IS NOT NULL
  AND TRY_CAST(replace(original_value, ',', '') AS DOUBLE) IS NOT NULL
  AND original_unit IS DISTINCT FROM normalized_unit
GROUP BY original_unit, normalized_unit, factor
ORDER BY original_unit, normalized_unit, n_rows DESC;

-- AUDIT: duplicate_canonical_items
-- 同一 product_id × canonical_item の重複（値が食い違うものほど危険）
SELECT n.product_id, n.company, n.canonical_item,
       COUNT(*) AS n_rows,
       COUNT(DISTINCT COALESCE(CAST(n.normalized_value_numeric AS VARCHAR), n.normalized_value_text)) AS n_distinct_values,
       string_agg(DISTINCT COALESCE(CAST(n.normalized_value_numeric AS VARCHAR), n.normalized_value_text), ' | ') AS values_seen
FROM normalized_specs n
WHERE n.value_status IN ('present', 'optional')
GROUP BY n.product_id, n.company, n.canonical_item
HAVING COUNT(*) > 1
ORDER BY n_distinct_values DESC, n_rows DESC;

-- AUDIT: duplicate_conflicting_values_count
-- 重複のうち「異なる値」を持つペア数（採用値の確認が必要）
SELECT COUNT(*) AS conflicting_pairs
FROM (
    SELECT n.product_id, n.canonical_item
    FROM normalized_specs n
    WHERE n.value_status IN ('present', 'optional')
    GROUP BY n.product_id, n.canonical_item
    HAVING COUNT(*) > 1
       AND COUNT(DISTINCT COALESCE(CAST(n.normalized_value_numeric AS VARCHAR), n.normalized_value_text)) > 1
);

-- AUDIT: best_view_uniqueness
-- best_normalized_specs は product_id × canonical_item で一意のはず（0行が正常）
SELECT product_id, canonical_item, COUNT(*) AS n
FROM best_normalized_specs
GROUP BY product_id, canonical_item
HAVING COUNT(*) > 1;

-- AUDIT: low_confidence_normalized
SELECT company, product_id, canonical_item, normalized_value_numeric, normalized_value_text,
       original_value, confidence, notes
FROM normalized_specs
WHERE value_status = 'present'
  AND confidence IS NOT NULL AND confidence < 0.7
ORDER BY confidence, company, canonical_item;

-- AUDIT: notes_missing_low_confidence
-- 推定を含む（confidence < 0.8）のに判断理由 notes が残っていない行
SELECT company, product_id, canonical_item, confidence, original_value
FROM normalized_specs
WHERE value_status = 'present'
  AND confidence IS NOT NULL AND confidence < 0.8
  AND (notes IS NULL OR notes = '')
ORDER BY confidence, company, canonical_item;

-- AUDIT: original_value_traceability
-- original_value / original_unit が残っていて normalized との対応が追えるか
SELECT
    COUNT(*) FILTER (WHERE value_status = 'present') AS present_rows,
    COUNT(*) FILTER (WHERE value_status = 'present'
                     AND (original_value IS NULL OR original_value = '')) AS present_missing_original_value,
    COUNT(*) FILTER (WHERE value_status = 'present'
                     AND normalized_value_numeric IS NOT NULL
                     AND normalized_unit IS DISTINCT FROM original_unit
                     AND (original_unit IS NULL OR original_unit = '')) AS converted_missing_original_unit
FROM normalized_specs;
