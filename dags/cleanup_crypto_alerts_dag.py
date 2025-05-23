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
    dag_id='cleanup_crypto_alerts_dag',
    default_args=default_args,
    schedule_interval='*/1 * * * *',
    catchup=False,
    description='Delete old records from crypto_alerts every 1 minute',
) as dag:

    delete_old_crypto_alerts = PostgresOperator(
        task_id='delete_old_crypto_alerts',
        postgres_conn_id='postgres_default',
        sql="DELETE FROM public.crypto_alerts WHERE is_alerted = true;"
    )

# docker cp "C:\Project\DataEngineer\BigDataEngineer\FinalProjectNaya\dags\cleanup_crypto_alerts_dag.py" dev_env:/opt/airflow/dags/