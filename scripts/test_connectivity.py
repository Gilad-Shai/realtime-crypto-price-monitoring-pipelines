from kafka import KafkaConsumer
import psycopg2

# --- Kafka Test ---
try:
    consumer = KafkaConsumer(
        'telegram_message_data',
        bootstrap_servers='course-kafka:9092',
        group_id='test-group',
        auto_offset_reset='earliest'
    )
    print("✅ Kafka is reachable from dev_env!")
except Exception as e:
    print("❌ Kafka connection error:", e)

# --- PostgreSQL Test ---
try:
    conn = psycopg2.connect(
        dbname="airflow",
        user="postgres",
        password="postgres",
        host="postgres",
        port="5432"
    )
    print("✅ PostgreSQL is reachable from dev_env!")
    conn.close()
except Exception as e:
    print("❌ PostgreSQL connection error:", e)
