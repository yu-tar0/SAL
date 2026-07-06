-- 01_profile_existing_tables.sql
-- knowledge.duckdb 内の既存テーブルを調査する読み取り専用クエリ集。
-- 実行: scripts/inspect_duckdb.py が read_only 接続で実行する。手動実行も read_only で行うこと。
-- ここでは DB を一切変更しない。

-- 1. テーブル一覧と行数
SELECT t.table_name,
       (SELECT row_count FROM excel_imports e WHERE e.table_name = t.table_name LIMIT 1) AS excel_rows,
       (SELECT raw_path  FROM excel_imports e WHERE e.table_name = t.table_name LIMIT 1) AS raw_path
FROM information_schema.tables t
WHERE t.table_type = 'BASE TABLE'
ORDER BY t.table_name;

-- 2. 各テーブルの列名と型
SELECT table_name, ordinal_position, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'main'
ORDER BY table_name, ordinal_position;

-- 3. 列シグネチャ（メタ列を除く列構成）でテーブルをグループ化 → 縦持ち/横持ちの型分類に使う
WITH cols AS (
    SELECT table_name,
           string_agg(column_name, ', ' ORDER BY ordinal_position) AS signature
    FROM information_schema.columns
    WHERE table_schema = 'main'
      AND column_name NOT IN ('raw_path', 'sheet_name', 'row_no')
    GROUP BY table_name
)
SELECT signature, count(*) AS n_tables, string_agg(table_name, '; ' ORDER BY table_name) AS tables
FROM cols
GROUP BY signature
ORDER BY n_tables DESC;

-- 4. 製品名・会社名・型番・仕様項目・値・単位に相当する列の候補
SELECT table_name, column_name,
       CASE
         WHEN column_name IN ('メーカー', 'メーカー名') THEN 'company'
         WHEN column_name IN ('型式', 'SAL型式', 'Model') THEN 'model'
         WHEN column_name IN ('仕様項目', '項目') THEN 'spec_item'
         WHEN column_name IN ('仕様値', '内容', '数値', 'US値', 'メートル値', '仕様_US値',
                              'メートル数値', 'US数値') THEN 'value'
         WHEN column_name LIKE '%単位%' THEN 'unit'
         WHEN column_name IN ('仕様カテゴリ', '大分類', '中分類', '区分', 'セクション', '大項目', '分類') THEN 'category'
         ELSE NULL
       END AS role
FROM information_schema.columns
WHERE table_schema = 'main'
  AND role IS NOT NULL
ORDER BY table_name, role;

-- 5. 縦持ちテーブルの仕様項目一覧（会社ごとの表記ゆれ確認の入口。代表テーブルのみ）
--    追加調査は scripts/inspect_duckdb.py --items で全縦持ちテーブルに対して行う。
SELECT 'avant' AS family, "仕様カテゴリ" AS category, "仕様項目" AS item, count(*) AS n
FROM "avant_型式_仕様一覧_仕様一覧" GROUP BY 1, 2, 3
UNION ALL
SELECT 'giant', NULL, "仕様項目", count(*)
FROM "giant_g1200_仕様一覧_仕様比較" GROUP BY 1, 2, 3
UNION ALL
SELECT 'yanmar', NULL, "仕様項目", count(*)
FROM "yanmar_cl26_仕様一覧_仕様一覧" GROUP BY 1, 2, 3
ORDER BY family, category, item;

-- 6. 単位の分布（単位混在・表記ゆれの確認）
SELECT unit, count(*) AS n FROM (
    SELECT "単位" AS unit FROM "avant_型式_仕様一覧_仕様一覧"
    UNION ALL SELECT "単位" FROM "gianni_ferrari_turboloader_仕様一覧_仕様一覧"
    UNION ALL SELECT "単位" FROM "yanmar_cl26_仕様一覧_仕様一覧"
    UNION ALL SELECT "US単位" FROM "case_sl12_仕様項目一覧_仕様"
    UNION ALL SELECT "メートル単位" FROM "case_sl12_仕様項目一覧_仕様"
    UNION ALL SELECT "L23_US単位" FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
    UNION ALL SELECT "L23_メートル単位" FROM "bobcat_sal_仕様値_Bobcat_SAL仕様"
)
WHERE unit IS NOT NULL
GROUP BY unit ORDER BY n DESC;
