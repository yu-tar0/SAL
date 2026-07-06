-- 05_build_spec_mapping.sql
-- raw_specs の (会社, 製品, 元テーブル, 項目名, 単位) の組ごとに canonical_item を割り当てる。
-- 優先順: spec_synonyms（exact/synonym） > spec_patterns（pattern_id 昇順） > manual_required。
-- マッピングできなかったものは canonical_item=NULL / mapping_method='manual_required' として残し、
-- normalization_issues にも記録する。

DELETE FROM spec_mapping;
DELETE FROM normalization_issues WHERE issue_type IN ('unmapped_item', 'low_confidence');

INSERT INTO spec_mapping
WITH combos AS (
    SELECT DISTINCT company, product_id, source_table, raw_item_name, raw_category, raw_unit
    FROM raw_specs
),
keyed AS (
    SELECT *,
           psn_item_key(raw_item_name) AS item_key,
           psn_item_key(coalesce(raw_category, '')) AS category_key,
           psn_unit_key(coalesce(raw_unit, '')) AS unit_key
    FROM combos
),
syn AS (
    SELECT k.*, s.canonical_item AS syn_item, s.match_type AS syn_method, s.notes AS syn_notes
    FROM keyed k
    LEFT JOIN spec_synonyms s ON s.synonym_key = k.item_key
),
pat AS (
    SELECT s.*, p.canonical_item AS pat_item, p.mapping_method AS pat_method,
           p.confidence AS pat_conf, p.notes AS pat_notes
    FROM syn s
    LEFT JOIN spec_patterns p
      ON regexp_matches(s.item_key, p.item_regex)
     AND (p.company_regex IS NULL OR regexp_matches(s.company, p.company_regex))
     AND (p.category_regex IS NULL OR regexp_matches(s.category_key, p.category_regex))
     AND (p.unit_regex IS NULL OR regexp_matches(s.unit_key, p.unit_regex))
    QUALIFY row_number() OVER (
        PARTITION BY s.company, s.product_id, s.source_table, s.raw_item_name, s.raw_unit
        ORDER BY p.pattern_id NULLS LAST) = 1
)
SELECT company, product_id, source_table, raw_item_name,
       coalesce(syn_item, pat_item) AS canonical_item,
       raw_unit,
       (SELECT canonical_unit FROM canonical_specs c WHERE c.canonical_item = coalesce(syn_item, pat_item)) AS canonical_unit,
       CASE
         WHEN syn_item IS NOT NULL THEN syn_method          -- 'exact' | 'synonym'
         WHEN pat_item IS NOT NULL THEN pat_method          -- 'pattern' | 'unit_based' | 'inferred'
         ELSE 'manual_required'
       END AS mapping_method,
       CASE
         WHEN syn_item IS NOT NULL AND syn_method = 'exact' THEN 1.0
         WHEN syn_item IS NOT NULL THEN 0.9
         WHEN pat_item IS NOT NULL THEN pat_conf
         ELSE 0.0
       END AS confidence,
       coalesce(syn_notes, pat_notes) AS notes
FROM pat;

-- 未マッピング項目を issues に記録
INSERT INTO normalization_issues (issue_type, severity, company, product_id, source_table, raw_item_name, detail)
SELECT 'unmapped_item', 'review', company, product_id, source_table, raw_item_name,
       'canonical_item が未割当。同義語辞書またはパターンの追加、もしくは比較対象外の判断が必要'
FROM spec_mapping
WHERE mapping_method = 'manual_required';

-- 低confidence（<0.7）のマッピングを issues に記録
INSERT INTO normalization_issues (issue_type, severity, company, product_id, source_table, raw_item_name, detail)
SELECT 'low_confidence', 'review', company, product_id, source_table, raw_item_name,
       'confidence ' || confidence || ' で ' || canonical_item || ' に割当（method=' || mapping_method || '）。要確認'
FROM spec_mapping
WHERE canonical_item IS NOT NULL AND confidence < 0.7;
