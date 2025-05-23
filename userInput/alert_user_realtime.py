import time
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window
import requests
import psycopg2

TELEGRAM_BOT_TOKEN = "ENTER YOUR TOKEN"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

POSTGRES_URL = "jdbc:postgresql://postgres:5432/airflow"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

NATIVE_PG_CONN = {
    "host": "postgres",
    "port": 5432,
    "database": "airflow",
    "user": "postgres",
    "password": "postgres"
}

spark = SparkSession.builder \
    .appName("CryptoAlertBot") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

def send_telegram_message(chat_id, message):
    if not chat_id:
        print("⚠️ Skipping alert with no chat_id")
        return
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(TELEGRAM_API_URL, json=payload)
        if response.status_code == 200:
            print(f"✅ Sent alert to {chat_id}")
        else:
            print(f"❌ Failed to send alert: {response.text}")
    except Exception as e:
        print(f"❌ Telegram Error: {str(e)}")

def mark_as_alerted(chat_id, crypto_type, purchase_price):
    try:
        conn = psycopg2.connect(**NATIVE_PG_CONN)
        cur = conn.cursor()
        cur.execute("""
            UPDATE public.crypto_alerts
            SET is_alerted = TRUE
            WHERE chat_id = %s AND crypto_type = %s AND purchase_price = %s
        """, (chat_id, crypto_type, purchase_price))
        conn.commit()
        cur.close()
        conn.close()
        print(f"☑️ Marked alert as sent for {crypto_type} - {chat_id}")
    except Exception as e:
        print(f"❌ Failed to update alert status: {str(e)}")

def process_batch():
    print("🔁 Checking alerts...")

    alerts_df = spark.read \
        .format("jdbc") \
        .option("url", POSTGRES_URL) \
        .option("dbtable", "public.crypto_alerts") \
        .option("user", POSTGRES_PROPERTIES["user"]) \
        .option("password", POSTGRES_PROPERTIES["password"]) \
        .option("driver", POSTGRES_PROPERTIES["driver"]) \
        .load() \
        .filter("is_alerted = false")

    market_df = spark.read \
        .format("jdbc") \
        .option("url", POSTGRES_URL) \
        .option("dbtable", "public.crypto_market_data") \
        .option("user", POSTGRES_PROPERTIES["user"]) \
        .option("password", POSTGRES_PROPERTIES["password"]) \
        .option("driver", POSTGRES_PROPERTIES["driver"]) \
        .load()

    window_spec = Window.partitionBy("id").orderBy(col("last_updated").desc())
    market_latest = market_df.withColumn("rn", row_number().over(window_spec)).filter("rn = 1").drop("rn")

    joined_df = alerts_df.join(
        market_latest,
        alerts_df["crypto_type"] == market_latest["name"],
        "inner"
    ).select(
        alerts_df["chat_id"],
        alerts_df["crypto_type"],
        alerts_df["purchase_price"].cast("double"),
        alerts_df["desired_profit_percentage"].cast("double"),
        alerts_df["desired_loss_percentage"].cast("double"),
        market_latest["current_price"].cast("double")
    )

    rows = joined_df.collect()
    for row in rows:
        chat_id = row["chat_id"]
        crypto = row["crypto_type"]
        purchase_price = row["purchase_price"]
        profit_percent = row["desired_profit_percentage"]
        loss_percent = row["desired_loss_percentage"]
        current_price = row["current_price"]

        target_profit_price = purchase_price * (1 + profit_percent / 100)
        stop_loss_price = purchase_price * (1 - loss_percent / 100)

        if current_price >= target_profit_price:
            message = (
                f"📈 {crypto} hit your profit target!\n"
                f"Current price: ${current_price:.2f}\n"
                f"(target: ${target_profit_price:.2f} = {purchase_price} * (1 + {profit_percent}/100))"
            )
            send_telegram_message(chat_id, message)
            mark_as_alerted(chat_id, crypto, purchase_price)

        elif current_price <= stop_loss_price:
            message = (
                f"📉 {crypto} dropped below your stop-loss!\n"
                f"Current price: ${current_price:.2f}\n"
                f"(limit: ${stop_loss_price:.2f} = {purchase_price} * (1 - {loss_percent}/100))"
            )
            send_telegram_message(chat_id, message)
            mark_as_alerted(chat_id, crypto, purchase_price)

if __name__ == "__main__":
    while True:
        process_batch()
        time.sleep(30)




# Run inside dev_env container:
# export PYSPARK_SUBMIT_ARGS="--packages org.postgresql:postgresql:42.6.0 pyspark-shell"
# python3 /opt/airflow/alert_user_realtime.py 
# docker cp alert_user_realtime.py dev_env:/opt/airflow/alert_user_realtime.py
