import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StringType, DoubleType, LongType

KAFKA_BOOTSTRAP_SERVERS = "course-kafka:9092"
KAFKA_TOPIC = "crypto_price_data"

POSTGRES_URL = "jdbc:postgresql://postgres:5432/airflow"
POSTGRES_TABLE = "crypto_market_data"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

S3_PATH = "s3a://archive-data-final-project/crypto_market_data/"

schema = StructType() \
    .add("id", StringType()) \
    .add("symbol", StringType()) \
    .add("name", StringType()) \
    .add("current_price", DoubleType()) \
    .add("market_cap", LongType()) \
    .add("total_volume", LongType())

spark = SparkSession.builder \
    .appName("StreamCryptoPriceToPostgresAndS3") \
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
    .selectExpr(
        "data.id as coin_id",
        "data.symbol",
        "data.name",
        "data.current_price",
        "data.market_cap",
        "data.total_volume"
    ).withColumn("last_updated", current_timestamp())

def write_to_postgres_and_s3(batch_df, batch_id):
    if batch_df.count() == 0:
        return

    print(f"🚀 Writing batch {batch_id} to Postgres and S3")

    batch_df = batch_df.withColumnRenamed("coin_id", "id")

    try:
        conn = psycopg2.connect(
            dbname="airflow",
            user="postgres",
            password="postgres",
            host="postgres",
            port="5432"
        )
        cur = conn.cursor()
        cur.execute(f"TRUNCATE TABLE {POSTGRES_TABLE};")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to truncate table: {e}")
        return

    batch_df.write \
        .mode("append") \
        .jdbc(url=POSTGRES_URL, table=POSTGRES_TABLE, properties=POSTGRES_PROPERTIES)

    batch_df.write \
        .mode("append") \
        .parquet(S3_PATH)

query = df_parsed.writeStream \
    .foreachBatch(write_to_postgres_and_s3) \
    .outputMode("append") \
    .start()

query.awaitTermination()



# Run inside dev_env container:
# export PYSPARK_SUBMIT_ARGS="--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4 pyspark-shell"
# python3 /opt/airflow/stream_coin_price.py
# docker cp stream_coin_price.py dev_env:/opt/airflow/stream_coin_price.py