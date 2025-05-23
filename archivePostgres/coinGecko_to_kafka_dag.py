from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import requests
from kafka import KafkaProducer
import json

logging.basicConfig(level=logging.INFO)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def fetch_and_send_to_kafka():
    logging.info("🔄 Starting to fetch crypto data and send to Kafka")

    try:
        coinGecko_url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&per_page=10&page=1&sparkline=false"
        )
        response = requests.get(coinGecko_url)
        response.raise_for_status()
        data = response.json()
        logging.info(f"✅ Fetched {len(data)} records from CoinGecko")
        producer = KafkaProducer(
            bootstrap_servers='course-kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        for record in data:
            producer.send('crypto_price_data', value=record)
        producer.flush()

        logging.info("✅ All records sent to Kafka topic: crypto_price_data")

    except Exception as e:
        logging.error("❌ Failed to fetch or send data to Kafka", exc_info=True)
        raise

with DAG(
    dag_id='coinGecko_to_kafka_dag',
    default_args=default_args,
    description='Fetch crypto prices and send to Kafka',
    schedule_interval='*/5 * * * *',
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['crypto', 'kafka'],
) as dag:

    fetch_and_push = PythonOperator(
        task_id='fetch_and_send',
        python_callable=fetch_and_send_to_kafka
    )

    fetch_and_push

# docker cp "C:\Project\DataEngineer\BigDataEngineer\FinalProjectNaya\dags\coinGecko_to_kafka_dag.py" dev_env:/opt/airflow/dags/