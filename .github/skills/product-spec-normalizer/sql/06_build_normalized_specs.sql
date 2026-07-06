-- 06_build_normalized_specs.sql
-- raw_specs × spec_mapping × canonical_specs から normalized_specs を構築する。
--
-- 方針:
--   * 単位変換は unit_conversions にある明示ルールのみ実施。ルールが無いものは数値化せず
--     テキストのまま保持し、notes にマーカーを付けて issues に記録する。
--   * カタログ併記形式（source_rank=3, 単位 'lb (kg)' 等）は括弧内のメートル系を採用する。
--   * 元テーブルに数値列が無い行は、値テキストが「数値+単位」の単純形のときだけ抽出する
--     （変換ではなく抽出。confidence を 0.95 倍に下げる）。
--   * 同一の元行から metric / us / テキストの複数 raw 行が出ている場合、変換に成功した行
--     → metric → us → その他 の優先で1行に絞る（同じ canonical_item 内のみ）。

DELETE FROM normalized_specs;
DELETE FROM normalization_issues WHERE issue_type IN ('unit_no_rule', 'unit_missing', 'numeric_parse_failed');

INSERT INTO normalized_specs (product_id, company, product_name, canonical_item,
                              normalized_value_numeric, normalized_value_text, normalized_unit,
                              original_value, original_unit, value_type, value_status, confidence,
                              source_table, source_column, source_row_id, unit_system, source_rank, notes)
WITH src AS (
    SELECT r.raw_spec_id, r.company, r.product_id, r.product_name, r.source_table, r.source_row_id,
           r.source_column, r.raw_item_name, r.raw_value_text, r.raw_value_numeric, r.raw_unit,
           r.unit_system, r.source_rank, r.raw_notes,
           m.canonical_item, m.confidence AS map_conf, m.mapping_method, m.notes AS map_notes,
           c.canonical_unit, c.value_type
    FROM raw_specs r
    JOIN spec_mapping m
      ON r.company = m.company AND r.product_id = m.product_id AND r.source_table = m.source_table
     AND r.raw_item_name = m.raw_item_name AND r.raw_unit IS NOT DISTINCT FROM m.raw_unit
    JOIN canonical_specs c ON c.canonical_item = m.canonical_item
    WHERE m.canonical_item IS NOT NULL
),
parsed1 AS (
    -- カタログ併記の分解は「値の末尾に括弧が1つだけ」の単純形に限定する
    -- （'Traction 9 (6.5); Implement 16 (12)' のような複合値は分解せずテキスト保持）
    SELECT *,
           (source_rank = 3 AND coalesce(raw_unit, '') LIKE '%(%'
            AND regexp_matches(coalesce(raw_value_text, ''), '^[^()]*\([^)]+\)\s*$')) AS is_combined,
           CASE WHEN source_rank = 3 AND coalesce(raw_unit, '') LIKE '%(%'
                 AND regexp_matches(coalesce(raw_value_text, ''), '^[^()]*\([^)]+\)\s*$')
                THEN coalesce(nullif(trim(regexp_extract(raw_value_text, '\(([^)]+)\)', 1)), ''), raw_value_text)
                ELSE raw_value_text END AS base_text,
           CASE WHEN source_rank = 3 AND coalesce(raw_unit, '') LIKE '%(%'
                 AND regexp_matches(coalesce(raw_value_text, ''), '^[^()]*\([^)]+\)\s*$')
                THEN psn_unit_key(regexp_extract(raw_unit, '\(([^)]+)\)', 1))
                ELSE psn_unit_key(coalesce(raw_unit, '')) END AS unit_key0
    FROM src
),
parsed2 AS (
    SELECT *,
           -- 末尾の括弧書き（'14.9 kW (20 hp)' の '(20 hp)'）を除去した作業用テキスト
           regexp_replace(coalesce(base_text, ''), '\s*\([^)]*\)\s*$', '') AS work_text
    FROM parsed1
),
parsed3 AS (
    SELECT *,
           CASE WHEN NOT is_combined THEN raw_value_numeric END AS num_direct,
           -- 「数値(+単位トークン)」の単純形のみ抽出対象にする
           CASE WHEN regexp_matches(work_text, '^\s*-?\d[\d,\. ]*\s*[A-Za-z°/%³²\.\-]*\s*$')
                THEN try_cast(replace(replace(regexp_extract(work_text, '^\s*(-?\d[\d,\. ]*)', 1), ',', ''), ' ', '') AS DOUBLE)
           END AS num_parsed,
           CASE WHEN regexp_matches(work_text, '^\s*-?\d[\d,\. ]*\s*[A-Za-z°/%³²\.\-]*\s*$')
                THEN psn_unit_key(regexp_extract(work_text, '^\s*-?\d[\d,\. ]*\s*([A-Za-z°/%³²\.\-]*)\s*$', 1))
           END AS unit_parsed
    FROM parsed2
),
prepared AS (
    SELECT *,
           coalesce(num_direct, num_parsed) AS eff_num,
           coalesce(nullif(unit_key0, ''),
                    CASE WHEN num_direct IS NULL THEN nullif(unit_parsed, '') END, '') AS eff_unit_key,
           CASE
             WHEN trim(coalesce(base_text, '')) = '' AND num_direct IS NULL THEN 'unknown'
             WHEN upper(trim(coalesce(base_text, ''))) IN ('N/A', 'NA', 'N.A.') THEN 'not_applicable'
             WHEN trim(coalesce(base_text, '')) IN ('—', '–', '-', '―') THEN 'not_disclosed'
             WHEN lower(trim(coalesce(base_text, ''))) IN ('optional', 'opt', 'option') THEN 'optional'
             ELSE 'present'
           END AS vstatus
    FROM parsed3
),
converted AS (
    -- 単位なし数値は、無次元の canonical 単位（cyl / rpm）に限り恒等変換を認める
    SELECT p.*,
           coalesce(uc.factor,
                    CASE WHEN p.eff_unit_key = '' AND p.canonical_unit IN ('cyl', 'rpm') THEN 1.0 END) AS factor,
           (coalesce(uc.factor,
                     CASE WHEN p.eff_unit_key = '' AND p.canonical_unit IN ('cyl', 'rpm') THEN 1.0 END) IS NOT NULL
            AND p.eff_num IS NOT NULL AND p.vstatus = 'present') AS conv_ok
    FROM prepared p
    LEFT JOIN unit_conversions uc
      ON uc.from_unit = p.eff_unit_key AND uc.to_unit = p.canonical_unit
)
SELECT product_id, company, product_name, canonical_item,
       CASE WHEN value_type = 'numeric' AND conv_ok THEN round(eff_num * factor, 4) END AS normalized_value_numeric,
       CASE WHEN value_type <> 'numeric' OR NOT conv_ok THEN nullif(trim(coalesce(base_text, cast(raw_value_numeric AS VARCHAR))), '') END AS normalized_value_text,
       CASE WHEN value_type = 'numeric' AND conv_ok THEN canonical_unit END AS normalized_unit,
       coalesce(raw_value_text, cast(raw_value_numeric AS VARCHAR)) AS original_value,
       raw_unit AS original_unit,
       value_type, vstatus,
       round(map_conf
             * (CASE WHEN num_direct IS NULL AND num_parsed IS NOT NULL AND value_type = 'numeric' THEN 0.95 ELSE 1 END)
             * (CASE WHEN is_combined THEN 0.95 ELSE 1 END), 3) AS confidence,
       source_table, source_column, source_row_id, unit_system, source_rank,
       concat_ws('; ',
           map_notes,
           raw_notes,
           CASE WHEN is_combined THEN 'カタログ併記からメートル側を抽出' END,
           CASE WHEN num_direct IS NULL AND num_parsed IS NOT NULL AND value_type = 'numeric'
                THEN 'テキストから数値抽出: ' || work_text END,
           CASE WHEN value_type = 'numeric' AND vstatus = 'present' AND eff_num IS NOT NULL
                 AND NOT conv_ok AND eff_unit_key <> ''
                THEN '[unit_no_rule] ' || eff_unit_key || ' → ' || coalesce(canonical_unit, '(なし)') || ' の変換ルールなし' END,
           CASE WHEN value_type = 'numeric' AND vstatus = 'present' AND eff_num IS NOT NULL
                 AND NOT conv_ok AND eff_unit_key = ''
                THEN '[unit_missing] 単位表記なしのため変換せず' END,
           CASE WHEN value_type = 'numeric' AND vstatus = 'present' AND eff_num IS NULL
                THEN '[numeric_parse_failed] 数値化できず（複合値・レンジ等）' END
       ) AS notes
FROM converted
-- 同一の元行×同一 canonical_item は1行に絞る（変換成功 > metric > us > その他）
QUALIFY row_number() OVER (
    PARTITION BY product_id, source_table, source_row_id, raw_item_name, canonical_item
    ORDER BY conv_ok DESC,
             CASE unit_system WHEN 'metric' THEN 1 WHEN 'us' THEN 2 ELSE 3 END,
             raw_spec_id) = 1;

-- notes のマーカーから issues を起こす
INSERT INTO normalization_issues (issue_type, severity, company, product_id, source_table, raw_item_name, raw_value, detail)
SELECT 'unit_no_rule', 'review', company, product_id, source_table, canonical_item,
       original_value || ' [' || coalesce(original_unit, '') || ']',
       regexp_extract(notes, '\[unit_no_rule\] ([^;]*)', 1)
FROM normalized_specs WHERE notes LIKE '%[unit_no_rule]%';

INSERT INTO normalization_issues (issue_type, severity, company, product_id, source_table, raw_item_name, raw_value, detail)
SELECT 'unit_missing', 'review', company, product_id, source_table, canonical_item,
       original_value, '数値はあるが単位表記が無く、変換の根拠がない'
FROM normalized_specs WHERE notes LIKE '%[unit_missing]%';

INSERT INTO normalization_issues (issue_type, severity, company, product_id, source_table, raw_item_name, raw_value, detail)
SELECT 'numeric_parse_failed', 'review', company, product_id, source_table, canonical_item,
       original_value, '数値型の標準項目だが数値化できなかった（複合値・レンジ・注記付き等）'
FROM normalized_specs WHERE notes LIKE '%[numeric_parse_failed]%';
