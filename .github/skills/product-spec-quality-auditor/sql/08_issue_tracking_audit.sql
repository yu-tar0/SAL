-- 08_issue_tracking_audit.sql
-- 目的: issue 管理の監査。要レビュー事項が記録され、追跡・レビュー可能な粒度かを確認する。
-- 制約: すべて SELECT のみ。DB を一切変更しない。

-- AUDIT: issues_by_type
SELECT issue_type, severity, status, COUNT(*) AS n
FROM normalization_issues
GROUP BY issue_type, severity, status
ORDER BY issue_type, severity, status;

-- AUDIT: issues_missing_reference
-- 対象（product_id / raw_item_name）を追えない issue（レビュー粒度として不十分）
SELECT issue_id, issue_type, severity, company, product_id, raw_item_name, detail
FROM normalization_issues
WHERE (product_id IS NULL OR product_id = '')
  AND (raw_item_name IS NULL OR raw_item_name = '')
ORDER BY issue_type, issue_id;

-- AUDIT: issues_missing_reference_count
SELECT COUNT(*) AS missing_reference_rows
FROM normalization_issues
WHERE (product_id IS NULL OR product_id = '')
  AND (raw_item_name IS NULL OR raw_item_name = '');

-- AUDIT: low_confidence_not_issued
-- confidence < 0.7 のマッピングなのに issue に記録されていないもの（見逃し）
SELECT m.company, m.product_id, m.raw_item_name, m.canonical_item,
       m.mapping_method, m.confidence
FROM spec_mapping m
WHERE m.canonical_item IS NOT NULL
  AND m.confidence > 0 AND m.confidence < 0.7
  AND NOT EXISTS (
      SELECT 1 FROM normalization_issues i
      WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
        AND (i.product_id IS NULL OR i.product_id = m.product_id))
ORDER BY m.confidence, m.company, m.raw_item_name;

-- AUDIT: low_confidence_not_issued_count
SELECT COUNT(*) AS low_confidence_not_issued_rows
FROM spec_mapping m
WHERE m.canonical_item IS NOT NULL
  AND m.confidence > 0 AND m.confidence < 0.7
  AND NOT EXISTS (
      SELECT 1 FROM normalization_issues i
      WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
        AND (i.product_id IS NULL OR i.product_id = m.product_id));

-- AUDIT: unmapped_not_issued
-- 未マッピング（manual_required）なのに issue に記録されていないもの（見逃し）
SELECT m.company, m.product_id, m.raw_item_name
FROM spec_mapping m
WHERE (m.canonical_item IS NULL OR m.mapping_method = 'manual_required')
  AND NOT EXISTS (
      SELECT 1 FROM normalization_issues i
      WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
        AND (i.product_id IS NULL OR i.product_id = m.product_id))
ORDER BY m.company, m.raw_item_name;

-- AUDIT: unmapped_not_issued_count
SELECT COUNT(*) AS unmapped_not_issued_rows
FROM spec_mapping m
WHERE (m.canonical_item IS NULL OR m.mapping_method = 'manual_required')
  AND NOT EXISTS (
      SELECT 1 FROM normalization_issues i
      WHERE i.raw_item_name IS NOT DISTINCT FROM m.raw_item_name
        AND (i.product_id IS NULL OR i.product_id = m.product_id));

-- AUDIT: open_issues_list
-- 人間レビュー待ちの open issue 全件
SELECT issue_id, issue_type, severity, company, product_id, raw_item_name,
       raw_value, detail, created_at
FROM normalization_issues
WHERE status = 'open'
ORDER BY issue_type, company, product_id, issue_id;
