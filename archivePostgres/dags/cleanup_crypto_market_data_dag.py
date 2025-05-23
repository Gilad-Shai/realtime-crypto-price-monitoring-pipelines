from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 5, 10),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='cleanup_crypto_market_data_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Delete old records from crypto_market_data daily',
) as dag:

    delete_old_crypto_market_data = PostgresOperator(
        task_id='delete_old_crypto_market_data',
        postgres_conn_id='postgres_default',
        sql="DELETE FROM public.crypto_market_data WHERE last_updated < NOW() - INTERVAL '1 day';"
    )


# docker cp "C:\Project\DataEngineer\BigDataEngineer\FinalProjectNaya\dags\cleanup_crypto_market_data_dag.py" dev_env:/opt/airflow/dags/