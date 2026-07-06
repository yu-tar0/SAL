-- 07_create_comparison_views.sql
-- 比較用ビュー。
--   best_normalized_specs      : 製品×標準項目ごとに最良1行を選ぶ中間ビュー
--   product_comparison_core_view : priority=1 中心のコア比較（1行1製品）
--   product_comparison_full_view : priority<=2 のフル比較（1行1製品）
--   product_comparison_view      : core のエイリアス

-- 製品×項目ごとの採用行: confidence 降順 → 一次シート優先 → metric 優先
CREATE OR REPLACE VIEW best_normalized_specs AS
SELECT *
FROM normalized_specs
WHERE value_status IN ('present', 'optional')
QUALIFY row_number() OVER (
    PARTITION BY product_id, canonical_item
    ORDER BY confidence DESC,
             source_rank ASC,
             CASE unit_system WHEN 'metric' THEN 1 WHEN 'us' THEN 2 ELSE 3 END,
             normalized_id) = 1;

CREATE OR REPLACE VIEW product_comparison_core_view AS
SELECT p.product_id,
       p.company,
       p.product_name,
       p.model_code,
       p.market_segment,
       p.power_type,
       p.telescopic,
       p.sales_status,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'operating_weight')          AS operating_weight_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'engine_power')              AS engine_power_kw,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'lift_height')               AS lift_height_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'lift_capacity')             AS lift_capacity_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'tipping_load_straight')     AS tipping_load_straight_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'tipping_load')              AS tipping_load_unspec_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'rated_operating_capacity')  AS rated_operating_capacity_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'max_travel_speed')          AS max_travel_speed_kmh,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'aux_hydraulic_flow')        AS aux_hydraulic_flow_lmin,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'aux_hydraulic_pressure')    AS aux_hydraulic_pressure_mpa,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_length')            AS overall_length_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_width')             AS overall_width_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_height')            AS overall_height_mm
FROM products p
LEFT JOIN best_normalized_specs b USING (product_id)
GROUP BY ALL;

CREATE OR REPLACE VIEW product_comparison_full_view AS
SELECT p.product_id,
       p.company,
       p.product_name,
       p.model_code,
       p.series,
       p.market_segment,
       p.power_type,
       p.telescopic,
       p.sales_status,
       -- weight / performance
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'operating_weight')          AS operating_weight_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'lift_height')               AS lift_height_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'lift_capacity')             AS lift_capacity_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'tipping_load_straight')     AS tipping_load_straight_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'tipping_load_articulated')  AS tipping_load_articulated_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'tipping_load')              AS tipping_load_unspec_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'rated_operating_capacity')  AS rated_operating_capacity_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'rated_operating_capacity_articulated') AS roc_articulated_kg,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'breakout_force')            AS breakout_force_kn,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'traction_force')            AS traction_force_kn,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'pushing_force')             AS pushing_force_kn,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'max_travel_speed')          AS max_travel_speed_kmh,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'bucket_capacity')           AS bucket_capacity_m3,
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'telescopic_boom')           AS telescopic_boom,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'telescopic_length')         AS telescopic_length_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'ground_pressure')           AS ground_pressure_kgm2,
       -- engine
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'engine_model')              AS engine_model,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'engine_power')              AS engine_power_kw,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'engine_torque')             AS engine_torque_nm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'engine_displacement')       AS engine_displacement_cc,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'engine_cylinders')          AS engine_cylinders,
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'fuel_type')                 AS fuel_type,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'fuel_tank_capacity')        AS fuel_tank_capacity_l,
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'emissions_standard')        AS emissions_standard,
       -- electrical
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'battery_capacity')          AS battery_capacity_kwh,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'charge_time')               AS charge_time_h,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'motor_power_drive')         AS motor_power_drive_kw,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'motor_power_implement')     AS motor_power_implement_kw,
       -- hydraulics
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'aux_hydraulic_flow')        AS aux_hydraulic_flow_lmin,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'aux_hydraulic_pressure')    AS aux_hydraulic_pressure_mpa,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'aux_hydraulic_flow_high')   AS aux_hydraulic_flow_high_lmin,
       -- dimensions
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_length')            AS overall_length_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_length_with_bucket') AS length_with_bucket_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_width')             AS overall_width_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'overall_height')            AS overall_height_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'wheelbase')                 AS wheelbase_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'ground_clearance')          AS ground_clearance_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'turning_radius_inner')      AS turning_radius_inner_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'turning_radius_outer')      AS turning_radius_outer_mm,
       max(b.normalized_value_numeric) FILTER (b.canonical_item = 'dump_height')               AS dump_height_mm,
       -- drivetrain / accessories / warranty
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'transmission')              AS transmission,
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'standard_tires')            AS standard_tires,
       max(b.normalized_value_text)    FILTER (b.canonical_item = 'warranty')                  AS warranty
FROM products p
LEFT JOIN best_normalized_specs b USING (product_id)
GROUP BY ALL;

-- 標準名のビュー（core のエイリアス）
CREATE OR REPLACE VIEW product_comparison_view AS
SELECT * FROM product_comparison_core_view;
