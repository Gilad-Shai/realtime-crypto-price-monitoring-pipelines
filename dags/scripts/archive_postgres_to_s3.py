from pyspark.sql import SparkSession
from pyspark.sql.functions import current_date

spark = SparkSession.builder \
    .appName("ArchivePostgresToMinIO") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

pg_url = "jdbc:postgresql://postgres_db:5432/postgres"

pg_properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

df_crypto_alarts = spark.read.jdbc(url=pg_url, table="crypto_alarts", properties=pg_properties)
df_crypto_alarts = df_crypto_alarts.filter(df_crypto_alarts["inserted_at"].cast("date") == current_date())

df_crypto_market_data = spark.read.jdbc(url=pg_url, table="crypto_market_data", properties=pg_properties)
df_crypto_market_data = df_crypto_market_data.filter(df_crypto_market_data["last_updated"].cast("date") == current_date())

df_crypto_alarts.write \
    .mode("append") \
    .partitionBy("inserted_at") \
    .parquet("s3a://archive-postgres/crypto_alarts/")

df_crypto_market_data.write \
    .mode("append") \
    .partitionBy("last_updated") \
    .parquet("s3a://archive-postgres/crypto_market_data/")

spark.stop()
