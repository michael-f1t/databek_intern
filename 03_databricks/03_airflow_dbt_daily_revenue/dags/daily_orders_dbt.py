from __future__ import annotations

import pendulum
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="daily_orders_to_dbt",
    description="Idempotently stage yesterday's orders, then build/test daily revenue.",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "data-engineering", "retries": 2},
    tags=["postgres", "dbt", "daily-revenue"],
)
def daily_orders_to_dbt():

    @task
    def stage_yesterdays_orders(**context):
        start = context["data_interval_start"].in_timezone("UTC")
        end = context["data_interval_end"].in_timezone("UTC")
        hook = PostgresHook(postgres_conn_id="shop_postgres")
        conn = hook.get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE SCHEMA IF NOT EXISTS staging;
                        CREATE TABLE IF NOT EXISTS staging.orders (
                            id BIGINT PRIMARY KEY,
                            customer_id BIGINT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL
                        );
                    """)
                    cur.execute("""
                        INSERT INTO staging.orders (id, customer_id, created_at)
                        SELECT id, customer_id, created_at
                        FROM public.orders
                        WHERE created_at >= %s AND created_at < %s
                        ON CONFLICT (id) DO UPDATE
                        SET customer_id = EXCLUDED.customer_id,
                            created_at = EXCLUDED.created_at;
                    """, (start, end))
                    count = cur.rowcount
            return {
                "interval_start": start.to_iso8601_string(),
                "interval_end": end.to_iso8601_string(),
                "rows_inserted_or_updated": count,
            }
        finally:
            conn.close()

    stage = stage_yesterdays_orders()
    dbt_build = BashOperator(
        task_id="dbt_build_and_test",
        bash_command="cd /opt/airflow/dbt/shop_analytics && dbt build --profiles-dir . --target dev",
    )
    stage >> dbt_build


daily_orders_to_dbt()
