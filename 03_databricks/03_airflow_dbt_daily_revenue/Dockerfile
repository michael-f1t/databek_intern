FROM apache/airflow:2.10.5-python3.11
USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.14.0 \
    dbt-core==1.9.4 \
    dbt-postgres==1.9.0
