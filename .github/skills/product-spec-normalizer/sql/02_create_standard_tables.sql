-- 02_create_standard_tables.sql
-- 標準化用テーブルの DDL。既存の raw テーブルには一切触れない。
-- CREATE OR REPLACE は「このスキルが所有する標準化テーブル」に対してのみ使う。

-- ---------------------------------------------------------------
-- 共通マクロ
-- ---------------------------------------------------------------

-- product_id 生成: '{company_key}:{正規化した型式}'。'+' は plus に変換してから記号を _ に寄せる。
CREATE OR REPLACE MACRO psn_product_id(company_key, model) AS
    company_key || ':' ||
    trim(regexp_replace(regexp_replace(lower(trim(model)), '\+', 'plus', 'g'), '[^a-z0-9]+', '_', 'g'), '_');

-- 仕様項目名の照合キー: 小文字化、脚注記号(*, ※, (1)等)除去、ダッシュ統一、空白圧縮。
CREATE OR REPLACE MACRO psn_item_key(s) AS
    trim(regexp_replace(
        regexp_replace(
            regexp_replace(
                replace(replace(lower(trim(coalesce(s, ''))), '–', '-'), '—', '-'),
                '[*※]+', '', 'g'),
            '\((\d+)\)|（(\d+)）', '', 'g'),
        '\s+', ' ', 'g'));

-- 単位の照合キー: 小文字化して空白・ピリオド・中黒を除去（'lb.'→'lb', 'L/min.'→'l/min', 'N·m'→'nm'）。
CREATE OR REPLACE MACRO psn_unit_key(u) AS
    regexp_replace(lower(trim(coalesce(u, ''))), '[\s\.·]+', '', 'g');

-- ---------------------------------------------------------------
-- 標準化テーブル
-- ---------------------------------------------------------------

-- 製品マスタ
CREATE OR REPLACE TABLE products (
    product_id     VARCHAR PRIMARY KEY,   -- 例 'case:sl12_tr'
    company        VARCHAR NOT NULL,      -- 表示用の会社名
    product_name   VARCHAR NOT NULL,      -- 表示用の製品名（原文の型式表記）
    model_code     VARCHAR,               -- 型式コード
    series         VARCHAR,
    market_segment VARCHAR,               -- SAL / テレスコありのSAL / SAL外の近接機種 など
    power_type     VARCHAR,               -- Diesel / Petrol / Electric など
    telescopic     VARCHAR,               -- あり / なし / NULL(不明)
    sales_status   VARCHAR,               -- 現行 / 旧型 / Prototype など
    product_url    VARCHAR,
    source_table   VARCHAR,               -- この行の主たる出所テーブル
    confidence     DOUBLE DEFAULT 1.0,
    notes          VARCHAR
);

-- raw層: 既存テーブルの仕様行を、元の名称・値・単位のまま縦持ちに集約する。
-- 元テーブルへの参照 (source_table / source_sheet / source_row_id / source_column) を必ず持つ。
CREATE OR REPLACE SEQUENCE raw_spec_seq;
CREATE OR REPLACE TABLE raw_specs (
    raw_spec_id       BIGINT DEFAULT nextval('raw_spec_seq'),
    company           VARCHAR NOT NULL,
    product_id        VARCHAR NOT NULL,
    product_name      VARCHAR,
    source_table      VARCHAR NOT NULL,   -- 元テーブル名
    source_sheet      VARCHAR,            -- 元シート名
    source_row_id     BIGINT,             -- 元テーブルの row_no（Excel 行番号）
    source_column     VARCHAR,            -- 値を取り出した元列名
    raw_category      VARCHAR,            -- 元の分類列（仕様カテゴリ / セクション / 大項目 等）
    raw_item_name     VARCHAR NOT NULL,   -- 元の仕様項目名（無加工。複合キーは ' / ' 連結）
    raw_value_text    VARCHAR,            -- 元の値（テキスト原文）
    raw_value_numeric DOUBLE,             -- 元の値（元テーブルに数値列がある場合のみ）
    raw_unit          VARCHAR,            -- 元の単位表記（無加工）
    unit_system       VARCHAR DEFAULT 'unspecified',  -- 'metric' | 'us' | 'unspecified'
    source_rank       INTEGER DEFAULT 1,  -- 1=一次仕様シート 2=横持ち一覧 3=カタログ集約(US(メートル)併記)
    raw_notes         VARCHAR
);

-- canonical層: 比較に使う標準仕様項目の定義
CREATE OR REPLACE TABLE canonical_specs (
    canonical_item  VARCHAR PRIMARY KEY,
    display_name_ja VARCHAR NOT NULL,
    display_name_en VARCHAR NOT NULL,
    category        VARCHAR NOT NULL,   -- basic_info/dimensions/weight/performance/engine/electrical/
                                        -- hydraulics/drivetrain/environment/interface/material/
                                        -- compliance/warranty/pricing/accessories/other
    canonical_unit  VARCHAR,            -- NULL = テキスト項目
    value_type      VARCHAR NOT NULL,   -- 'numeric' | 'text' | 'boolean'
    priority        INTEGER NOT NULL,   -- 1=コア比較項目 2=フル比較項目 3=参考
    description     VARCHAR,
    comparison_flag BOOLEAN DEFAULT TRUE
);

-- 同義語辞書（確度の高い1対1対応のみ。key は psn_item_key() 適用後の文字列）
CREATE OR REPLACE TABLE spec_synonyms (
    synonym_key    VARCHAR NOT NULL,
    canonical_item VARCHAR NOT NULL,
    match_type     VARCHAR DEFAULT 'synonym',  -- 'exact'(canonical名そのもの) | 'synonym'
    notes          VARCHAR
);

-- パターン規則（正規表現 + 会社/カテゴリ/単位の条件付き。判断を伴うマッピングはこちらに置き、confidence を下げる）
CREATE OR REPLACE TABLE spec_patterns (
    pattern_id     INTEGER NOT NULL,
    item_regex     VARCHAR NOT NULL,   -- psn_item_key 適用後の項目名に対する正規表現
    company_regex  VARCHAR,            -- NULL = 全社
    category_regex VARCHAR,            -- NULL = 全カテゴリ（psn_item_key 適用後の raw_category に対して）
    unit_regex     VARCHAR,            -- NULL = 単位を問わない（psn_unit_key 適用後の raw_unit に対して）
    canonical_item VARCHAR NOT NULL,
    mapping_method VARCHAR NOT NULL,   -- 'pattern' | 'unit_based' | 'inferred'
    confidence     DOUBLE NOT NULL,
    notes          VARCHAR
);

-- 単位変換ルール（明示的なもののみ。from_unit は psn_unit_key() 適用後のキー）
CREATE OR REPLACE TABLE unit_conversions (
    from_unit VARCHAR NOT NULL,   -- 正規化済み単位キー
    to_unit   VARCHAR NOT NULL,   -- canonical_specs.canonical_unit と一致させる
    factor    DOUBLE NOT NULL,
    notes     VARCHAR
);

-- mapping層: 会社×製品×元項目 → 標準項目
CREATE OR REPLACE TABLE spec_mapping (
    company        VARCHAR NOT NULL,
    product_id     VARCHAR NOT NULL,
    source_table   VARCHAR NOT NULL,
    raw_item_name  VARCHAR NOT NULL,
    canonical_item VARCHAR,             -- NULL = 未マッピング（mapping_method='manual_required'）
    raw_unit       VARCHAR,
    canonical_unit VARCHAR,
    mapping_method VARCHAR NOT NULL,    -- exact | synonym | unit_based | pattern | inferred | manual_required
    confidence     DOUBLE NOT NULL,
    notes          VARCHAR
);

-- normalized層: 値と単位を正規化した比較可能な仕様
CREATE OR REPLACE SEQUENCE normalized_spec_seq;
CREATE OR REPLACE TABLE normalized_specs (
    normalized_id            BIGINT DEFAULT nextval('normalized_spec_seq'),
    product_id               VARCHAR NOT NULL,
    company                  VARCHAR NOT NULL,
    product_name             VARCHAR,
    canonical_item           VARCHAR NOT NULL,
    normalized_value_numeric DOUBLE,
    normalized_value_text    VARCHAR,
    normalized_unit          VARCHAR,
    original_value           VARCHAR,
    original_unit            VARCHAR,
    value_type               VARCHAR,
    value_status             VARCHAR DEFAULT 'present',  -- present/missing/not_applicable/not_disclosed/unknown/optional
    confidence               DOUBLE,
    source_table             VARCHAR,
    source_column            VARCHAR,
    source_row_id            BIGINT,
    unit_system              VARCHAR,
    source_rank              INTEGER,
    notes                    VARCHAR
);

-- 判定に迷ったもの・要レビュー事項の記録
CREATE OR REPLACE SEQUENCE normalization_issue_seq;
CREATE OR REPLACE TABLE normalization_issues (
    issue_id      BIGINT DEFAULT nextval('normalization_issue_seq'),
    issue_type    VARCHAR NOT NULL,   -- unmapped_item / low_confidence / unit_no_rule / unit_missing /
                                      -- numeric_parse_failed / duplicate_value / scope_excluded / data_shape
    severity      VARCHAR DEFAULT 'review',   -- 'info' | 'review' | 'blocker'
    company       VARCHAR,
    product_id    VARCHAR,
    source_table  VARCHAR,
    raw_item_name VARCHAR,
    raw_value     VARCHAR,
    detail        VARCHAR,
    status        VARCHAR DEFAULT 'open',     -- 'open' | 'resolved' | 'wont_fix'
    created_at    TIMESTAMP DEFAULT current_timestamp
);
