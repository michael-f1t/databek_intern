{{ config(materialized='table') }}

SELECT
    (o.created_at AT TIME ZONE 'UTC')::date AS order_date,
    SUM(oi.quantity * oi.unit_price)::numeric(18, 2) AS daily_revenue,
    COUNT(DISTINCT o.id) AS order_count,
    COUNT(*) AS order_line_count
FROM {{ source('staged_shop', 'orders') }} AS o
JOIN {{ source('raw_shop', 'order_items') }} AS oi
  ON oi.order_id = o.id
GROUP BY 1
