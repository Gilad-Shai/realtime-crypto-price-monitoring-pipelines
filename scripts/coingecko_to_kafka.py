from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
from kafka import KafkaProducer

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1&sparkline=false"
KAFKA_TOPIC = "crypto_market_data"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092" 


def fetch_and_publish_to_kafka():
    response = requests.get(COINGECKO_URL)
    response.raise_for_status()
    data = response.json()

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    for coin in data:
        producer.send(KAFKA_TOPIC, value=coin)

    producer.flush()

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id="coingecko_to_kafka",
    default_args=default_args,
    schedule="*/5 * * * *",  # every 5 minutes
    catchup=False,
    description="Fetch crypto data from Coingecko and send to Kafka every 5 minutes",
    tags=["crypto", "kafka", "coingecko"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_and_publish",
        python_callable=fetch_and_publish_to_kafka,
    )

    fetch_task
