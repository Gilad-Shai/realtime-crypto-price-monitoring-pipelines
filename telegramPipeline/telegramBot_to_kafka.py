from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime
import json

TELEGRAM_TOKEN = "ENTER YOUR TOKEN"
KAFKA_TOPIC = "telegram_message_data"
KAFKA_BOOTSTRAP_SERVERS = "course-kafka:9092"

def parse_input(text, chat_id):
    try:
        fields = text.split(',')
        result = {"chat_id": str(chat_id)}
        for field in fields:
            key, value = field.strip().split('=')
            result[key.strip().lower()] = value.strip()
        result["created_at"] = datetime.utcnow().isoformat()
        return result
    except Exception:
        return {"error": "❌ Invalid format. Please use:\ncrypto_type=..., purchase_price=..., profit=..., loss=..."}

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to Crypto Alert Bot 🤑!\n\n"
        "Please enter your crypto tracking info in the format:\n\n"
        "crypto_type=Bitcoin, purchase_price=30000, desired_profit_percentage=10, desired_loss_percentage=5"
    )

def handle_message(update: Update, context: CallbackContext):
    user_input = update.message.text
    chat_id = update.message.chat_id
    parsed = parse_input(user_input, chat_id)

    if "error" in parsed:
        update.message.reply_text(parsed["error"])
    else:
        update.message.reply_text(f"✅ Tracking added: {parsed}")
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            future = producer.send(KAFKA_TOPIC, value=parsed)
            result = future.get(timeout=10)
            print(f"✅ Sent to Kafka: {parsed}")
        except KafkaError as e:
            print(f"❌ Kafka error: {e}")

def main():
    updater_instance = Updater(TELEGRAM_TOKEN)
    dp = updater_instance.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater_instance.start_polling()
    updater_instance.idle()

if __name__ == '__main__':
    main()

# Run inside dev_env container:
# python3 /opt/airflow/telegramBot_to_kafka.py
# docker cp telegramBot_to_kafka.py dev_env:/opt/airflow/telegramBot_to_kafka.py
