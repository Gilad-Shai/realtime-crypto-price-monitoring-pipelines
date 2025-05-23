from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, lit
from pyspark.sql.types import StructType, StringType

KAFKA_BOOTSTRAP_SERVERS = "course-kafka:9092"
KAFKA_TOPIC = "telegram_message_data"

POSTGRES_URL = "jdbc:postgresql://postgres:5432/airflow"
POSTGRES_TABLE = "crypto_alerts"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

S3_PATH = "s3a://archive-data-final-project/crypto_alerts/"

schema = StructType() \
    .add("chat_id", StringType()) \
    .add("crypto_type", StringType()) \
    .add("purchase_price", StringType()) \
    .add("desired_profit_percentage", StringType()) \
    .add("desired_loss_percentage", StringType()) \
    .add("created_at", StringType())

spark = SparkSession.builder \
    .appName("StreamTelegramAlertsToPostgresAndS3") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

df_parsed = df_kafka.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

def write_to_postgres_and_s3(batch_df, batch_id):
    if batch_df.count() == 0:
        return

    print(f"💾 Writing batch {batch_id}")

    df_casted = batch_df \
        .withColumn("chat_id", col("chat_id").cast("long")) \
        .withColumn("purchase_price", col("purchase_price").cast("double")) \
        .withColumn("desired_profit_percentage", col("desired_profit_percentage").cast("double")) \
        .withColumn("desired_loss_percentage", col("desired_loss_percentage").cast("double")) \
        .withColumn("created_at", to_timestamp(col("created_at"))) \
        .withColumn("is_alerted", lit(False))

    df_casted.write \
        .mode("append") \
        .jdbc(url=POSTGRES_URL, table=POSTGRES_TABLE, properties=POSTGRES_PROPERTIES)

    df_casted.write \
        .mode("append") \
        .parquet(S3_PATH)

query = df_parsed.writeStream \
    .foreachBatch(write_to_postgres_and_s3) \
    .outputMode("append") \
    .start()

query.awaitTermination()


# Run inside dev_env container:
# export PYSPARK_SUBMIT_ARGS="--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4 pyspark-shell"
# python3 /opt/airflow/stream_crypto_alerts.py
# docker cp stream_crypto_alerts.py dev_env:/opt/airflow/stream_crypto_alerts.py












# from pyspark.sql import SparkSession
# from pyspark.sql.functions import from_json, col, to_timestamp, lit
# from pyspark.sql.types import StructType, StringType

# KAFKA_BOOTSTRAP_SERVERS = "course-kafka:9092"
# KAFKA_TOPIC = "telegram_message_data"

# POSTGRES_URL = "jdbc:postgresql://postgres:5432/airflow"
# POSTGRES_TABLE = "crypto_alerts"
# POSTGRES_PROPERTIES = {
#     "user": "postgres",
#     "password": "postgres",
#     "driver": "org.postgresql.Driver"
# }

# S3_PATH = "s3a://archive-data-final-project/crypto_alerts/"

# schema = StructType() \
#     .add("chat_id", StringType()) \
#     .add("crypto_type", StringType()) \
#     .add("purchase_price", StringType()) \
#     .add("desired_profit_percentage", StringType()) \
#     .add("desired_loss_percentage", StringType()) \
#     .add("created_at", StringType())

# spark = SparkSession.builder \
#     .appName("StreamTelegramAlertsToPostgresAndS3") \
#     .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4") \
#     .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
#     .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
#     .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
#     .config("spark.hadoop.fs.s3a.path.style.access", "true") \
#     .getOrCreate()

# spark.sparkContext.setLogLevel("WARN")

# df_kafka = spark.readStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
#     .option("subscribe", KAFKA_TOPIC) \
#     .option("startingOffsets", "latest") \
#     .load()

# df_parsed = df_kafka.selectExpr("CAST(value AS STRING)") \
#     .select(from_json(col("value"), schema).alias("data")) \
#     .select("data.*")

# def write_to_postgres_and_s3(batch_df, batch_id):
#     if batch_df.count() == 0:
#         return

#     print(f"💾 Writing batch {batch_id}")

#     df_casted = batch_df \
#         .withColumn("purchase_price", col("purchase_price").cast("double")) \
#         .withColumn("desired_profit_percentage", col("desired_profit_percentage").cast("double")) \
#         .withColumn("desired_loss_percentage", col("desired_loss_percentage").cast("double")) \
#         .withColumn("created_at", to_timestamp(col("created_at"))) \
#         .withColumn("is_alerted", lit(False))

#     df_casted.write \
#         .mode("append") \
#         .jdbc(url=POSTGRES_URL, table=POSTGRES_TABLE, properties=POSTGRES_PROPERTIES)

#     df_casted.write \
#         .mode("append") \
#         .parquet(S3_PATH)

# query = df_parsed.writeStream \
#     .foreachBatch(write_to_postgres_and_s3) \
#     .outputMode("append") \
#     .start()

# query.awaitTermination()