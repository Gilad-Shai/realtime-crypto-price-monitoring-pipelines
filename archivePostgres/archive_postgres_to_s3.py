from pyspark.sql import SparkSession
from datetime import datetime

spark = SparkSession.builder \
    .appName("ArchivePostgresToMinIO") \
    .getOrCreate()

# ✅ Print the loaded JARs in the current Spark context
print("JARS in Spark context:", spark.sparkContext._conf.get("spark.jars"))

# ✅ JDBC connection settings
pg_url = "jdbc:postgresql://postgres:5432/airflow"
pg_properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# ✅ Read data from PostgreSQL
df_crypto_alarts = spark.read.jdbc(
    url=pg_url,
    table="crypto_alarts",
    properties=pg_properties
)

# ✅ Define the S3 (MinIO) output path
today_str = datetime.today().strftime('%Y-%m-%d')
output_path = f"s3a://archive-bucket/crypto_alarts/date={today_str}/"

# ✅ Write to S3 as Parquet
df_crypto_alarts.write.mode("overwrite").parquet(output_path)

print(f"✅ Successfully archived to: {output_path}")
