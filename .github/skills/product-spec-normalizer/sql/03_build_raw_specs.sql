-- 03_build_raw_specs.sql
-- 既存テーブルから products と raw_specs を構築する。既存テーブルは読み取りのみ。
-- 再実行可能にするため、冒頭で標準化テーブル側だけを空にする。
--
-- 対象範囲（v1）:
--   仕様値を持つシート（仕様一覧 / 仕様 / 寸法 / 転倒荷重 / 仕様比較 / SAL仕様 / SALカタログ SPECIFICATIONS+DIMENSIONS）
-- 対象外（v1、docs/assumptions.md 参照）:
--   装備 / オプション・特徴 / 注記 / 原文 / 概要(定性) / アタッチメント / タイヤ互換表 / 油圧システム(型式一覧と重複) /
--   タイヤサイズ別寸法 / サマリー表示・カード表示（カタログの丸め値でノイズになるため）

DELETE FROM raw_specs;
DELETE FROM products;

-- ================================================================
-- 1. products
-- ================================================================

-- --- Avant（型式一覧 + 旧型モデル。旧型モデルは型式一覧に無いものだけ追加） ---
INSERT INTO products
SELECT psn_product_id('avant', "型式"), 'Avant', "型式", "型式", "シリーズ", "SAL分類",
       "動力区分", "テレスコ搭載", "販売状況", "製品URL",
       'avant_型式_仕様一覧_型式一覧', 1.0, NULL
FROM "avant_型式_仕様一覧_型式一覧";

INSERT INTO products
SELECT psn_product_id('avant', t."型式"), 'Avant', t."型式", t."型式", t."シリーズ", t."SAL分類",
       t."動力区分", t."テレスコ搭載", t."販売状況", t."製品URL",
       'avant_型式_仕様一覧_旧型モデル', 1.0, '旧型モデルシート由来'
FROM "avant_型式_仕様一覧_旧型モデル" t
WHERE psn_product_id('avant', t."型式") NOT IN (SELECT product_id FROM products);

-- --- Bobcat（横持ち列 L23/L28/L35 から定義） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, source_table, confidence, notes) VALUES
    ('bobcat:l23', 'Bobcat', 'L23', 'L23', 'SAL', 'bobcat_sal_仕様値_Bobcat_SAL仕様', 0.9, '横持ち列名から推定'),
    ('bobcat:l28', 'Bobcat', 'L28', 'L28', 'SAL', 'bobcat_sal_仕様値_Bobcat_SAL仕様', 0.9, '横持ち列名から推定'),
    ('bobcat:l35', 'Bobcat', 'L35', 'L35', 'SAL', 'bobcat_sal_仕様値_Bobcat_SAL仕様', 0.9, '横持ち列名から推定');

-- --- Case（型式別シート群 + カタログ列から定義。TR = テレスコピックリーチ仕様） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, power_type, telescopic, source_table, confidence, notes) VALUES
    ('case:sl12',    'Case', 'SL12',    'SL12',    'SAL', 'Diesel',   'なし', 'case_sl12_仕様項目一覧_仕様',    0.9, NULL),
    ('case:sl12_tr', 'Case', 'SL12 TR', 'SL12 TR', 'テレスコありのSAL', 'Diesel', 'あり', 'case_sl12tr_仕様項目一覧_仕様', 0.9, 'TR=Telescopic Reach と推定'),
    ('case:sl15',    'Case', 'SL15',    'SL15',    'SAL', 'Diesel',   'なし', 'case_sl15_仕様項目一覧_仕様',    0.9, NULL),
    ('case:sl22ev',  'Case', 'SL22EV',  'SL22EV',  '電動SAL', 'Electric', 'なし', 'case_sl22ev_仕様項目一覧_仕様', 0.9, NULL),
    ('case:sl23',    'Case', 'SL23',    'SL23',    'SAL', 'Diesel',   'なし', 'case_sl23_仕様項目一覧_仕様',    0.9, NULL),
    ('case:sl27',    'Case', 'SL27',    'SL27',    'SAL', 'Diesel',   'なし', 'case_sl27_仕様項目一覧_仕様',    0.9, NULL),
    ('case:sl27_tr', 'Case', 'SL27 TR', 'SL27 TR', 'テレスコありのSAL', 'Diesel', 'あり', 'case_sl27tr_仕様項目一覧_仕様', 0.9, 'TR=Telescopic Reach と推定'),
    ('case:sl35_tr', 'Case', 'SL35 TR', 'SL35 TR', 'テレスコありのSAL', 'Diesel', 'あり', 'case_sl35tr_仕様項目一覧_仕様', 0.9, 'TR=Telescopic Reach と推定'),
    ('case:sl50_tr', 'Case', 'SL50 TR', 'SL50 TR', 'テレスコありのSAL', 'Diesel', 'あり', 'case_sl50tr_仕様項目一覧_仕様', 0.9, 'TR=Telescopic Reach と推定');

-- --- Gianni Ferrari（仕様一覧の型式列から） ---
INSERT INTO products (product_id, company, product_name, model_code, series, market_segment, telescopic, source_table, confidence, notes)
SELECT psn_product_id('gianni', "型式"), 'Gianni Ferrari', "型式", "型式", 'Turboloader',
       'テレスコありのSAL', NULL, 'gianni_ferrari_turboloader_仕様一覧_仕様一覧', 0.8,
       '概要シートで Telescopic articulated loader と記載。セグメントは推定'
FROM (SELECT DISTINCT "型式" FROM "gianni_ferrari_turboloader_仕様一覧_仕様一覧" WHERE "型式" IS NOT NULL);

-- --- GIANT（型式分類一覧を正とし、仕様比較にしか出ない型式を補完） ---
INSERT INTO products (product_id, company, product_name, model_code, series, market_segment, power_type, telescopic, source_table, confidence, notes)
SELECT psn_product_id('giant', "型式"), 'GIANT', "型式", "型式", "シリーズ", "調査用分類",
       "動力", "テレスコ有無", 'giant_型式分類一覧_GIANT型式分類', 1.0, "判定メモ"
FROM "giant_型式分類一覧_GIANT型式分類";

INSERT INTO products (product_id, company, product_name, model_code, market_segment, source_table, confidence, notes)
SELECT DISTINCT psn_product_id('giant', regexp_replace("型式", '\s*\([^)]*\)\s*$', '')),
       'GIANT', regexp_replace("型式", '\s*\([^)]*\)\s*$', ''),
       regexp_replace("型式", '\s*\([^)]*\)\s*$', ''), NULL,
       s.source_table, 0.6, '仕様比較シートのみから検出。型式分類一覧に未掲載'
FROM (
    SELECT "型式", 'giant_g1200_仕様一覧_仕様比較' AS source_table FROM "giant_g1200_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g1200_tele_仕様一覧_仕様比較' FROM "giant_g1200_tele_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g1500_series_仕様一覧_仕様比較' FROM "giant_g1500_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g2200e_series_仕様一覧_仕様比較' FROM "giant_g2200e_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g2300_hd_仕様一覧_仕様比較' FROM "giant_g2300_hd_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g2500_series_仕様一覧_仕様比較' FROM "giant_g2500_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g2700_series_仕様一覧_仕様比較' FROM "giant_g2700_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g3500_series_仕様一覧_仕様比較' FROM "giant_g3500_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g5000_series_仕様一覧_仕様比較' FROM "giant_g5000_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_g5000_tele_series_仕様一覧_仕様比較' FROM "giant_g5000_tele_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_gs_series_仕様一覧_仕様比較' FROM "giant_gs_series_仕様一覧_仕様比較"
    UNION ALL SELECT "型式", 'giant_gt5048_series_仕様一覧_仕様比較' FROM "giant_gt5048_series_仕様一覧_仕様比較"
) s
WHERE psn_product_id('giant', regexp_replace("型式", '\s*\([^)]*\)\s*$', '')) NOT IN (SELECT product_id FROM products)
QUALIFY row_number() OVER (PARTITION BY psn_product_id('giant', regexp_replace("型式", '\s*\([^)]*\)\s*$', '')) ORDER BY s.source_table) = 1;

-- --- MultiOne 標準9機種（各テーブルの Model 行から製品名を取得） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, source_table, confidence, notes)
SELECT psn_product_id('multione', mn), 'MultiOne', mn, mn, 'SAL', src, 0.9, 'Model 行から取得'
FROM (
    SELECT (SELECT any_value("仕様値") FROM "multione_1_1_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model') AS mn, 'multione_1_1_仕様一覧_仕様一覧' AS src
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_2_3_efi_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_2_3_efi_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_5_2_k_id_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_5_2_k_id_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_5_3_k_id_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_5_3_k_id_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_6_3_ids_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_6_3_ids_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_7_2_k_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_7_2_k_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_8_4_turbos_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_8_4_turbos_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_8_5_y_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_8_5_y_仕様一覧_仕様一覧'
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_8_5s_k_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_8_5s_k_仕様一覧_仕様一覧'
) WHERE mn IS NOT NULL;

-- --- MultiOne 11.x（列構成が異なる2テーブル） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, source_table, confidence, notes)
SELECT psn_product_id('multione', mn), 'MultiOne', mn, mn, 'SAL', src, 0.9, 'Model 行から取得'
FROM (
    SELECT (SELECT any_value("仕様値") FROM "multione_11_5_y_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model') AS mn, 'multione_11_5_y_仕様一覧_仕様一覧' AS src
    UNION ALL SELECT (SELECT any_value("仕様値") FROM "multione_11_6_k_turbos_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model'), 'multione_11_6_k_turbos_仕様一覧_仕様一覧'
) WHERE mn IS NOT NULL;

-- --- MultiOne EZ（SAL型式列から。'EZ 8 / EZ 8 Long Range' の共通行は製品にしない） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, power_type, source_table, confidence, notes)
SELECT psn_product_id('multione', m), 'MultiOne', m, m, '電動SAL', 'Electric', src, 0.9, NULL
FROM (
    SELECT DISTINCT "SAL型式" AS m, 'multione_ez7_仕様一覧_仕様一覧' AS src
    FROM "multione_ez7_仕様一覧_仕様一覧" WHERE "SAL型式" NOT LIKE '%/%'
    UNION
    SELECT DISTINCT "SAL型式", 'multione_ez8_ez8_long_range_仕様一覧_仕様一覧'
    FROM "multione_ez8_ez8_long_range_仕様一覧_仕様一覧" WHERE "SAL型式" NOT LIKE '%/%'
) WHERE m IS NOT NULL
  AND psn_product_id('multione', m) NOT IN (SELECT product_id FROM products);

-- --- Yanmar（概要シートの内容に基づく。プロトタイプ） ---
INSERT INTO products (product_id, company, product_name, model_code, market_segment, telescopic, sales_status, source_table, confidence, notes) VALUES
    ('yanmar:cl26', 'Yanmar', 'CL26', 'CL26', 'SAL', 'なし', 'Prototype',
     'yanmar_cl26_仕様一覧_概要', 0.9, '記事ベースのプロトタイプ仕様。量産時に変更の可能性あり（概要シート記載）');

-- ================================================================
-- 2. raw_specs
-- ================================================================

-- ----------------------------------------------------------------
-- 2.1 Avant 縦持ち（仕様一覧）: source_rank=1
--     「備考」行は仕様値ではないため除外。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
SELECT 'Avant', psn_product_id('avant', "型式"), "型式",
       'avant_型式_仕様一覧_仕様一覧', sheet_name, row_no,
       '仕様値/数値/単位', "仕様カテゴリ", "仕様項目",
       "仕様値", try_cast(replace("数値", ',', '') AS DOUBLE),
       "単位", 'unspecified', 1, nullif("備考", '')
FROM "avant_型式_仕様一覧_仕様一覧"
WHERE "仕様項目" IS NOT NULL AND "仕様項目" <> '備考'
  AND (coalesce("仕様値", '') <> '' OR coalesce("数値", '') <> '');

-- ----------------------------------------------------------------
-- 2.2 Avant 横持ち（型式一覧 + 旧型モデル）: source_rank=2
--     列名に単位が埋め込まれているため raw_unit を列名サフィックスから補う。
--     同一製品×同一項目は 型式一覧 を優先して重複排除。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
SELECT 'Avant', psn_product_id('avant', "型式"), "型式",
       src, sheet_name, row_no, raw_item_name, '横持ち列', raw_item_name,
       raw_value_text, try_cast(replace(raw_value_text, ',', '') AS DOUBLE),
       CASE
         WHEN raw_item_name LIKE '%_kg'  THEN 'kg'
         WHEN raw_item_name LIKE '%_mm'  THEN 'mm'
         WHEN raw_item_name LIKE '%_kmh' THEN 'km/h'
         WHEN raw_item_name LIKE '%_Lmin' THEN 'L/min'
         WHEN raw_item_name LIKE '%_bar' THEN 'bar'
         WHEN raw_item_name LIKE '%_MPa' THEN 'MPa'
         WHEN raw_item_name LIKE '%_kgf' THEN 'kgf'
         ELSE NULL
       END,
       'metric', 2, NULL
FROM (
    SELECT *, 'avant_型式_仕様一覧_型式一覧' AS src FROM (
        SELECT "型式", sheet_name, row_no,
               cast("馬力_出力" AS VARCHAR) AS "馬力_出力", cast("エンジン型式" AS VARCHAR) AS "エンジン型式",
               cast("出力規格" AS VARCHAR) AS "出力規格", cast("最大トルク" AS VARCHAR) AS "最大トルク",
               cast("燃料_バッテリー" AS VARCHAR) AS "燃料_バッテリー", cast("バッテリー容量" AS VARCHAR) AS "バッテリー容量",
               cast("充電時間" AS VARCHAR) AS "充電時間", cast("リフト容量_kg" AS VARCHAR) AS "リフト容量_kg",
               cast("リフト高_mm" AS VARCHAR) AS "リフト高_mm", cast("テレスコ搭載" AS VARCHAR) AS "テレスコ搭載",
               cast("テレスコ長_mm" AS VARCHAR) AS "テレスコ長_mm", cast("補助油圧流量_Lmin" AS VARCHAR) AS "補助油圧流量_Lmin",
               cast("補助油圧圧力_bar" AS VARCHAR) AS "補助油圧圧力_bar", cast("補助油圧圧力_MPa" AS VARCHAR) AS "補助油圧圧力_MPa",
               cast("最大ブレークアウト力_kgf" AS VARCHAR) AS "最大ブレークアウト力_kgf", cast("最大牽引力_kgf" AS VARCHAR) AS "最大牽引力_kgf",
               cast("最高速度_kmh" AS VARCHAR) AS "最高速度_kmh", cast("運転質量_kg" AS VARCHAR) AS "運転質量_kg",
               cast("全幅_mm" AS VARCHAR) AS "全幅_mm", cast("全長_mm" AS VARCHAR) AS "全長_mm",
               cast("全高_mm" AS VARCHAR) AS "全高_mm", cast("旋回半径内側_mm" AS VARCHAR) AS "旋回半径内側_mm",
               cast("旋回半径外側_mm" AS VARCHAR) AS "旋回半径外側_mm", cast("標準タイヤ" AS VARCHAR) AS "標準タイヤ",
               cast("タイヤトレッド" AS VARCHAR) AS "タイヤトレッド", cast("ホイールサイズ" AS VARCHAR) AS "ホイールサイズ",
               cast("トランスミッション" AS VARCHAR) AS "トランスミッション"
        FROM "avant_型式_仕様一覧_型式一覧"
    ) UNPIVOT (raw_value_text FOR raw_item_name IN (
        "馬力_出力", "エンジン型式", "出力規格", "最大トルク", "燃料_バッテリー", "バッテリー容量", "充電時間",
        "リフト容量_kg", "リフト高_mm", "テレスコ搭載", "テレスコ長_mm", "補助油圧流量_Lmin",
        "補助油圧圧力_bar", "補助油圧圧力_MPa", "最大ブレークアウト力_kgf", "最大牽引力_kgf", "最高速度_kmh",
        "運転質量_kg", "全幅_mm", "全長_mm", "全高_mm", "旋回半径内側_mm", "旋回半径外側_mm",
        "標準タイヤ", "タイヤトレッド", "ホイールサイズ", "トランスミッション"))
    UNION ALL
    SELECT *, 'avant_型式_仕様一覧_旧型モデル' AS src FROM (
        SELECT "型式", sheet_name, row_no,
               cast("馬力_出力" AS VARCHAR) AS "馬力_出力", cast("エンジン型式" AS VARCHAR) AS "エンジン型式",
               cast("出力規格" AS VARCHAR) AS "出力規格", cast("最大トルク" AS VARCHAR) AS "最大トルク",
               cast("燃料_バッテリー" AS VARCHAR) AS "燃料_バッテリー", cast("バッテリー容量" AS VARCHAR) AS "バッテリー容量",
               cast("充電時間" AS VARCHAR) AS "充電時間", cast("リフト容量_kg" AS VARCHAR) AS "リフト容量_kg",
               cast("リフト高_mm" AS VARCHAR) AS "リフト高_mm", cast("テレスコ搭載" AS VARCHAR) AS "テレスコ搭載",
               cast("テレスコ長_mm" AS VARCHAR) AS "テレスコ長_mm", cast("補助油圧流量_Lmin" AS VARCHAR) AS "補助油圧流量_Lmin",
               cast("補助油圧圧力_bar" AS VARCHAR) AS "補助油圧圧力_bar", cast("補助油圧圧力_MPa" AS VARCHAR) AS "補助油圧圧力_MPa",
               cast("最大ブレークアウト力_kgf" AS VARCHAR) AS "最大ブレークアウト力_kgf", cast("最大牽引力_kgf" AS VARCHAR) AS "最大牽引力_kgf",
               cast("最高速度_kmh" AS VARCHAR) AS "最高速度_kmh", cast("運転質量_kg" AS VARCHAR) AS "運転質量_kg",
               cast("全幅_mm" AS VARCHAR) AS "全幅_mm", cast("全長_mm" AS VARCHAR) AS "全長_mm",
               cast("全高_mm" AS VARCHAR) AS "全高_mm", cast("旋回半径内側_mm" AS VARCHAR) AS "旋回半径内側_mm",
               cast("旋回半径外側_mm" AS VARCHAR) AS "旋回半径外側_mm", cast("標準タイヤ" AS VARCHAR) AS "標準タイヤ",
               cast("タイヤトレッド" AS VARCHAR) AS "タイヤトレッド", cast("ホイールサイズ" AS VARCHAR) AS "ホイールサイズ",
               cast("トランスミッション" AS VARCHAR) AS "トランスミッション"
        FROM "avant_型式_仕様一覧_旧型モデル"
    ) UNPIVOT (raw_value_text FOR raw_item_name IN (
        "馬力_出力", "エンジン型式", "出力規格", "最大トルク", "燃料_バッテリー", "バッテリー容量", "充電時間",
        "リフト容量_kg", "リフト高_mm", "テレスコ搭載", "テレスコ長_mm", "補助油圧流量_Lmin",
        "補助油圧圧力_bar", "補助油圧圧力_MPa", "最大ブレークアウト力_kgf", "最大牽引力_kgf", "最高速度_kmh",
        "運転質量_kg", "全幅_mm", "全長_mm", "全高_mm", "旋回半径内側_mm", "旋回半径外側_mm",
        "標準タイヤ", "タイヤトレッド", "ホイールサイズ", "トランスミッション"))
)
QUALIFY row_number() OVER (PARTITION BY psn_product_id('avant', "型式"), raw_item_name ORDER BY src) = 1;

-- ----------------------------------------------------------------
-- 2.3 Bobcat（製品×単位系の横持ちを縦に展開）: source_rank=1
--     機能・装備・注記セクションは v1 対象外。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank)
SELECT 'Bobcat', pid, pname, 'bobcat_sal_仕様値_Bobcat_SAL仕様', sheet_name, row_no,
       col, "セクション", "仕様項目", v, try_cast(replace(v, ',', '') AS DOUBLE), u, usys, 1
FROM (
    SELECT *, 'bobcat:l23' AS pid, 'L23' AS pname, 'L23_メートル数値' AS col, "L23_メートル数値" AS v, "L23_メートル単位" AS u, 'metric' AS usys FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT *, 'bobcat:l23', 'L23', 'L23_US数値', "L23_US数値", "L23_US単位", 'us' FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT *, 'bobcat:l28', 'L28', 'L28_メートル数値', "L28_メートル数値", "L28_メートル単位", 'metric' FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT *, 'bobcat:l28', 'L28', 'L28_US数値', "L28_US数値", "L28_US単位", 'us' FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT *, 'bobcat:l35', 'L35', 'L35_メートル数値', "L35_メートル数値", "L35_メートル単位", 'metric' FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT *, 'bobcat:l35', 'L35', 'L35_US数値', "L35_US数値", "L35_US単位", 'us' FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
)
WHERE coalesce(v, '') <> ''
  AND "セクション" NOT IN ('注記', 'MACHINE FEATURES', 'SAFETY EQUIPMENT', 'FEATURES FOR ATTACHMENTS');

-- ----------------------------------------------------------------
-- 2.4 Case SALカタログ（横持ち・US(メートル)併記）: source_rank=3
--     FEATURES 行（装備の standard/optional）は v1 対象外。値の分解は 06 で行う。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_unit,
                       unit_system, source_rank, raw_notes)
SELECT 'Case', psn_product_id('case', replace(model_col, '_', ' ')), replace(model_col, '_', ' '),
       'case_sal_catalog_specs_with_features_revised_Case_SALカタログ', sheet_name, row_no,
       model_col, "区分", "項目", raw_value_text, "単位", 'unspecified', 3,
       'US(メートル)併記のカタログ値'
FROM (
    SELECT sheet_name, row_no, "区分", "項目", "単位",
           SL12, SL12_TR, SL15, SL23, SL27, SL27_TR, SL35_TR, SL50_TR, SL22EV
    FROM "case_sal_catalog_specs_with_features_revised_Case_SALカタログ"
    WHERE "区分" <> 'FEATURES'
) UNPIVOT (raw_value_text FOR model_col IN (SL12, SL12_TR, SL15, SL23, SL27, SL27_TR, SL35_TR, SL50_TR, SL22EV))
WHERE coalesce(raw_value_text, '') <> '';

-- ----------------------------------------------------------------
-- 2.5 Case 型式別シート（仕様 / 寸法 / 転倒荷重）: source_rank=1
--     US系とメートル系を別行として保持する（重複整理は 06/07 で実施）。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
WITH case_spec AS (
    SELECT 'case:sl12' AS pid, 'SL12' AS pname, 'case_sl12_仕様項目一覧_仕様' AS tbl, sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR) AS usv, "US単位" AS usu, cast("メートル値" AS VARCHAR) AS mv, "メートル単位" AS mu FROM "case_sl12_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl12_tr', 'SL12 TR', 'case_sl12tr_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl12tr_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl15', 'SL15', 'case_sl15_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl15_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl22ev', 'SL22EV', 'case_sl22ev_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl22ev_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl23', 'SL23', 'case_sl23_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl23_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl27', 'SL27', 'case_sl27_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl27_tr', 'SL27 TR', 'case_sl27tr_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27tr_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl35_tr', 'SL35 TR', 'case_sl35tr_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl35tr_仕様項目一覧_仕様"
    UNION ALL SELECT 'case:sl50_tr', 'SL50 TR', 'case_sl50tr_仕様項目一覧_仕様', sheet_name, row_no, "大分類", "中分類", "項目", cast("仕様_US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl50tr_仕様項目一覧_仕様"
)
SELECT 'Case', pid, pname, tbl, sheet_name, row_no, col,
       "大分類",
       concat_ws(' / ', nullif(trim("大分類"), ''), nullif(trim(coalesce("中分類", '')), ''), nullif(trim("項目"), '')),
       v, try_cast(replace(v, ',', '') AS DOUBLE), u, usys, 1, NULL
FROM (
    SELECT *, 'メートル値' AS col, mv AS v, mu AS u, 'metric' AS usys FROM case_spec
    UNION ALL
    SELECT *, '仕様_US値', usv, usu, 'us' FROM case_spec
)
WHERE coalesce(v, '') <> '';

INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
WITH case_dim AS (
    SELECT 'case:sl12' AS pid, 'SL12' AS pname, 'case_sl12_仕様項目一覧_寸法' AS tbl, '寸法' AS cat, sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR) AS usv, "US単位" AS usu, cast("メートル値" AS VARCHAR) AS mv, "メートル単位" AS mu FROM "case_sl12_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl12_tr', 'SL12 TR', 'case_sl12tr_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl12tr_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl15', 'SL15', 'case_sl15_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl15_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl22ev', 'SL22EV', 'case_sl22ev_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl22ev_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl23', 'SL23', 'case_sl23_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl23_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl27', 'SL27', 'case_sl27_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl27_tr', 'SL27 TR', 'case_sl27tr_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27tr_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl35_tr', 'SL35 TR', 'case_sl35tr_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl35tr_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl50_tr', 'SL50 TR', 'case_sl50tr_仕様項目一覧_寸法', '寸法', sheet_name, row_no, "記号", "項目", cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl50tr_仕様項目一覧_寸法"
    UNION ALL SELECT 'case:sl12', 'SL12', 'case_sl12_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl12_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl12_tr', 'SL12 TR', 'case_sl12tr_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl12tr_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl15', 'SL15', 'case_sl15_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl15_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl22ev', 'SL22EV', 'case_sl22ev_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl22ev_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl23', 'SL23', 'case_sl23_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl23_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl27', 'SL27', 'case_sl27_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl27_tr', 'SL27 TR', 'case_sl27tr_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl27tr_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl35_tr', 'SL35 TR', 'case_sl35tr_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl35tr_仕様項目一覧_転倒荷重"
    UNION ALL SELECT 'case:sl50_tr', 'SL50 TR', 'case_sl50tr_仕様項目一覧_転倒荷重', '転倒荷重', sheet_name, row_no, "記号", "項目" || ' / ' || coalesce("記号", ''), cast("US値" AS VARCHAR), "US単位", cast("メートル値" AS VARCHAR), "メートル単位" FROM "case_sl50tr_仕様項目一覧_転倒荷重"
)
SELECT 'Case', pid, pname, tbl, sheet_name, row_no, col, cat, "項目",
       v, try_cast(replace(v, ',', '') AS DOUBLE), u, usys, 1,
       CASE WHEN cat = '寸法' THEN '記号 ' || coalesce("記号", '') ELSE NULL END
FROM (
    SELECT *, 'メートル値' AS col, mv AS v, mu AS u, 'metric' AS usys FROM case_dim
    UNION ALL
    SELECT *, 'US値', usv, usu, 'us' FROM case_dim
)
WHERE coalesce(v, '') <> '';

-- ----------------------------------------------------------------
-- 2.6 Gianni Ferrari（縦持ち）: source_rank=1
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
SELECT 'Gianni Ferrari', psn_product_id('gianni', "型式"), "型式",
       'gianni_ferrari_turboloader_仕様一覧_仕様一覧', sheet_name, row_no,
       '仕様値/数値/単位', "大項目", "仕様項目",
       "仕様値", try_cast(replace(cast("数値" AS VARCHAR), ',', '') AS DOUBLE),
       "単位", 'unspecified', 1, nullif("備考", '')
FROM "gianni_ferrari_turboloader_仕様一覧_仕様一覧"
WHERE "仕様項目" IS NOT NULL
  AND (coalesce("仕様値", '') <> '' OR "数値" IS NOT NULL);

-- ----------------------------------------------------------------
-- 2.7 GIANT（12ファイルの仕様比較を統合。ファイル間の完全重複行は排除）: source_rank=1
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
SELECT 'GIANT', psn_product_id('giant', regexp_replace("型式", '\s*\([^)]*\)\s*$', '')), "型式",
       tbl, sheet_name, row_no, '仕様値/数値/単位', NULL, "仕様項目",
       "仕様値", try_cast(replace(cast("数値" AS VARCHAR), ',', '') AS DOUBLE),
       "単位", 'us', 1, nullif("備考", '')
FROM (
    SELECT *, 'giant_g1200_仕様一覧_仕様比較' AS tbl FROM "giant_g1200_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g1200_tele_仕様一覧_仕様比較' FROM "giant_g1200_tele_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g1500_series_仕様一覧_仕様比較' FROM "giant_g1500_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g2200e_series_仕様一覧_仕様比較' FROM "giant_g2200e_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g2300_hd_仕様一覧_仕様比較' FROM "giant_g2300_hd_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g2500_series_仕様一覧_仕様比較' FROM "giant_g2500_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g2700_series_仕様一覧_仕様比較' FROM "giant_g2700_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g3500_series_仕様一覧_仕様比較' FROM "giant_g3500_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g5000_series_仕様一覧_仕様比較' FROM "giant_g5000_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_g5000_tele_series_仕様一覧_仕様比較' FROM "giant_g5000_tele_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_gs_series_仕様一覧_仕様比較' FROM "giant_gs_series_仕様一覧_仕様比較"
    UNION ALL SELECT *, 'giant_gt5048_series_仕様一覧_仕様比較' FROM "giant_gt5048_series_仕様一覧_仕様比較"
)
WHERE coalesce("仕様値", '') <> '' OR "数値" IS NOT NULL
QUALIFY row_number() OVER (
    PARTITION BY psn_product_id('giant', regexp_replace("型式", '\s*\([^)]*\)\s*$', '')),
                 "仕様項目", coalesce("仕様値", ''), coalesce("単位", '')
    ORDER BY tbl) = 1;

-- ----------------------------------------------------------------
-- 2.8 MultiOne 標準9機種: source_rank=1
--     マーケ用サマリー・寸法図・製品情報・タイヤ別寸法等は v1 対象外。
--     1行から metric行 / us行 / テキスト行 を生成（テキスト行は数値が無い場合と Engine 行のみ）。
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
WITH mo AS (
    SELECT * FROM (
        SELECT t.*, 'multione_1_1_仕様一覧_仕様一覧' AS tbl,
               (SELECT any_value("仕様値") FROM "multione_1_1_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model') AS mn
        FROM "multione_1_1_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_2_3_efi_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_2_3_efi_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_2_3_efi_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_5_2_k_id_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_5_2_k_id_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_5_2_k_id_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_5_3_k_id_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_5_3_k_id_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_5_3_k_id_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_6_3_ids_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_6_3_ids_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_6_3_ids_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_7_2_k_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_7_2_k_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_7_2_k_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_8_4_turbos_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_8_4_turbos_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_8_4_turbos_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_8_5_y_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_8_5_y_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_8_5_y_仕様一覧_仕様一覧" t
        UNION ALL SELECT t.*, 'multione_8_5s_k_仕様一覧_仕様一覧',
               (SELECT any_value("仕様値") FROM "multione_8_5s_k_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
        FROM "multione_8_5s_k_仕様一覧_仕様一覧" t
    )
    WHERE "区分" NOT IN ('サマリー表示', 'カード表示', '寸法図', '製品情報', 'シリーズ', 'タイヤサイズ別寸法')
)
SELECT 'MultiOne', psn_product_id('multione', mn), mn, tbl, sheet_name, row_no,
       col, "区分", "仕様項目", v, n, u, usys, 1, note
FROM (
    SELECT *, 'メートル数値' AS col, coalesce("仕様値", cast("メートル数値" AS VARCHAR)) AS v,
           "メートル数値" AS n, "メートル単位" AS u, 'metric' AS usys, NULL AS note
    FROM mo WHERE "メートル数値" IS NOT NULL
    UNION ALL
    SELECT *, 'US数値', coalesce("仕様値", cast("US数値" AS VARCHAR)), "US数値", "US単位", 'us', NULL
    FROM mo WHERE "US数値" IS NOT NULL
    UNION ALL
    SELECT *, '仕様値', "仕様値", NULL, NULL, 'unspecified',
           CASE WHEN "仕様項目" = 'Engine' THEN '数値行(排気量)とは別のテキスト行' ELSE NULL END
    FROM mo WHERE coalesce("仕様値", '') <> ''
              AND (("メートル数値" IS NULL AND "US数値" IS NULL) OR "仕様項目" = 'Engine')
);

-- ----------------------------------------------------------------
-- 2.9 MultiOne 11.x（サブ項目付き）: source_rank=1
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
WITH mo11 AS (
    SELECT t.*, t._tbl AS tbl,
           (CASE t._tbl
              WHEN 'multione_11_5_y_仕様一覧_仕様一覧' THEN (SELECT any_value("仕様値") FROM "multione_11_5_y_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
              ELSE (SELECT any_value("仕様値") FROM "multione_11_6_k_turbos_仕様一覧_仕様一覧" WHERE "仕様項目" = 'Model')
            END) AS mn,
           "仕様項目" || CASE WHEN coalesce(trim("サブ項目"), '') <> '' THEN ' [' || trim("サブ項目") || ']' ELSE '' END AS item
    FROM (
        SELECT *, 'multione_11_5_y_仕様一覧_仕様一覧' AS _tbl FROM "multione_11_5_y_仕様一覧_仕様一覧"
        UNION ALL SELECT *, 'multione_11_6_k_turbos_仕様一覧_仕様一覧' FROM "multione_11_6_k_turbos_仕様一覧_仕様一覧"
    ) t
    WHERE t."区分" NOT IN ('カード表示', 'タイヤ別寸法')
)
SELECT 'MultiOne', psn_product_id('multione', mn), mn, tbl, sheet_name, row_no,
       col, "区分", item, v, n, u, usys, 1, nullif("メモ", '')
FROM (
    SELECT *, 'メートル数値' AS col, coalesce("仕様値", cast("メートル数値" AS VARCHAR)) AS v,
           "メートル数値" AS n, "メートル単位" AS u, 'metric' AS usys
    FROM mo11 WHERE "メートル数値" IS NOT NULL
    UNION ALL
    SELECT *, 'US数値', coalesce("仕様値", cast("US数値" AS VARCHAR)), "US数値", "US単位", 'us'
    FROM mo11 WHERE "US数値" IS NOT NULL
    UNION ALL
    SELECT *, '仕様値', "仕様値", NULL, NULL, 'unspecified'
    FROM mo11 WHERE coalesce("仕様値", '') <> ''
                AND (("メートル数値" IS NULL AND "US数値" IS NULL) OR "仕様項目" = 'Engine')
);

-- ----------------------------------------------------------------
-- 2.10 MultiOne EZ（電動。SAL型式列を持つ。共通行 'EZ 8 / EZ 8 Long Range' は両製品に複製）: source_rank=1
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
WITH ez AS (
    SELECT t.*, t._tbl AS tbl,
           "仕様項目" || CASE WHEN coalesce(trim("条件"), '') <> '' THEN ' [' || trim("条件") || ']' ELSE '' END AS item
    FROM (
        SELECT *, 'multione_ez7_仕様一覧_仕様一覧' AS _tbl FROM "multione_ez7_仕様一覧_仕様一覧"
        UNION ALL SELECT *, 'multione_ez8_ez8_long_range_仕様一覧_仕様一覧' FROM "multione_ez8_ez8_long_range_仕様一覧_仕様一覧"
    ) t
    WHERE t."分類" NOT IN ('カタログ概要', 'タイヤ寸法', '製品コード')
),
ez_fanout AS (
    -- 単一型式の行はそのまま、'A / B' 共通行は両型式へ複製
    SELECT *, trim("SAL型式") AS model, NULL AS fan_note FROM ez WHERE "SAL型式" NOT LIKE '%/%'
    UNION ALL
    SELECT *, trim(str_split("SAL型式", '/')[1]), '複数型式の共通行を複製: ' || "SAL型式" FROM ez WHERE "SAL型式" LIKE '%/%'
    UNION ALL
    SELECT *, trim(str_split("SAL型式", '/')[2]), '複数型式の共通行を複製: ' || "SAL型式" FROM ez WHERE "SAL型式" LIKE '%/%'
)
SELECT 'MultiOne', psn_product_id('multione', model), model, tbl, sheet_name, row_no,
       col, "分類", item, v, n, u, usys, 1,
       concat_ws('; ', fan_note, nullif("メモ", ''))
FROM (
    SELECT *, 'メートル数値' AS col, coalesce("仕様値", cast("メートル数値" AS VARCHAR)) AS v,
           "メートル数値" AS n, "メートル単位" AS u, 'metric' AS usys
    FROM ez_fanout WHERE "メートル数値" IS NOT NULL
    UNION ALL
    SELECT *, 'US数値', coalesce("仕様値", cast("US数値" AS VARCHAR)), "US数値", "US単位", 'us'
    FROM ez_fanout WHERE "US数値" IS NOT NULL
    UNION ALL
    SELECT *, '仕様値', "仕様値", NULL, NULL, 'unspecified'
    FROM ez_fanout WHERE coalesce("仕様値", '') <> ''
                     AND "メートル数値" IS NULL AND "US数値" IS NULL
);

-- ----------------------------------------------------------------
-- 2.11 Yanmar（縦持ち）: source_rank=1
-- ----------------------------------------------------------------
INSERT INTO raw_specs (company, product_id, product_name, source_table, source_sheet, source_row_id,
                       source_column, raw_category, raw_item_name, raw_value_text, raw_value_numeric,
                       raw_unit, unit_system, source_rank, raw_notes)
SELECT 'Yanmar', psn_product_id('yanmar', "型式"), "型式",
       'yanmar_cl26_仕様一覧_仕様一覧', sheet_name, row_no,
       '仕様値/数値/単位', NULL, "仕様項目",
       "仕様値", try_cast(replace(cast("数値" AS VARCHAR), ',', '') AS DOUBLE),
       "単位", 'us', 1, nullif("備考", '')
FROM "yanmar_cl26_仕様一覧_仕様一覧"
WHERE "仕様項目" IS NOT NULL
  AND (coalesce("仕様値", '') <> '' OR "数値" IS NOT NULL);

-- ----------------------------------------------------------------
-- 2.12 v1 対象外テーブルの記録（スコープ判断を issues に残す）
-- ----------------------------------------------------------------
INSERT INTO normalization_issues (issue_type, severity, source_table, detail)
SELECT 'scope_excluded', 'info', e.table_name,
       'v1 の raw_specs 取り込み対象外（装備/オプション/注記/原文/概要/アタッチメント/タイヤ互換/重複シート等）'
FROM excel_imports e
WHERE e.table_name NOT IN (SELECT DISTINCT source_table FROM raw_specs)
  AND e.table_name NOT IN ('avant_型式_仕様一覧_型式一覧', 'avant_型式_仕様一覧_旧型モデル',
                           'giant_型式分類一覧_GIANT型式分類')  -- products の出所は対象扱い
QUALIFY row_number() OVER (PARTITION BY e.table_name ORDER BY e.loaded_at DESC) = 1;
