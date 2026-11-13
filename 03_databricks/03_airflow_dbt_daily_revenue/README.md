# Daily Orders Pipeline — Airflow + PostgreSQL + dbt

A Docker Compose demo that extracts yesterday's orders from PostgreSQL into a
staging table, then builds and tests a daily revenue dbt model.

## Pipeline

`public.orders` → Airflow DAG → `staging.orders` → dbt `daily_revenue`

The fact/model grain is **one row per UTC calendar date**. Revenue is
`SUM(order_items.quantity * order_items.unit_price)` for orders on that date.

## Idempotency

The staging load uses `INSERT ... ON CONFLICT (id) DO UPDATE`, with `id` as
the staging table primary key. Re-running the same interval updates existing
rows rather than creating duplicates. The DAG uses `max_active_runs=1`.

## Expected source schema

- `orders(id, customer_id, created_at)`
- `order_items(id, order_id, product_id, quantity, unit_price)`

The demo database is initialized from `sql/init.sql`. Adapt the staging
DDL and SELECT if your provided shop dataset uses different column names.

## Run

Requires Docker Desktop/Engine and Docker Compose.

```bash
docker compose up --build airflow-init
docker compose up -d
```

Open Airflow at http://localhost:8080 (admin / admin), unpause
`daily_orders_to_dbt`, then trigger it. PostgreSQL is available at
localhost:5433 (shop / shop).

The DAG uses the Airflow daily data interval in UTC and extracts the
half-open interval `[data_interval_start, data_interval_end)`.

## dbt

The DAG runs `dbt build`, which builds `analytics.daily_revenue` and executes
the declared tests: `unique` and `not_null` on `order_date`, and `not_null`
on `daily_revenue`.

To run manually:

```bash
docker compose exec airflow-scheduler bash
cd /opt/airflow/dbt/shop_analytics
dbt build --profiles-dir . --target dev
```

Stop with `docker compose down`. Reset the demo database with
`docker compose down -v`.

**Local-demo warning:** change the default passwords and secret key before
using this configuration outside a local learning environment.
