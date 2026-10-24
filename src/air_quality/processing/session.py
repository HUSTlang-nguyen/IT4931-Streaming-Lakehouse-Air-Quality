"""Spark session dùng chung REST catalog/S3 với Trino, không download jar runtime."""

import os

from pyspark.sql import SparkSession


def spark_session(name: str = "air-quality") -> SparkSession:
    """Tạo local[2] trên runtime đã pin; timezone và secret redaction tường minh.

    local[2] là Spark thật chạy trên laptop, không giả lập master/worker nhàn
    rỗi. Dữ liệu/bảng ở MinIO và catalog persist, không nằm trong RAM driver.
    """
    settings = {
        "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        "spark.sql.catalog.lake": "org.apache.iceberg.spark.SparkCatalog",
        "spark.sql.catalog.lake.type": "rest",
        "spark.sql.catalog.lake.uri": os.getenv("ICEBERG_CATALOG_URI", "http://catalog:8181"),
        "spark.sql.catalog.lake.warehouse": "s3://warehouse/",
        "spark.sql.catalog.lake.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
        "spark.sql.catalog.lake.s3.endpoint": os.getenv("S3_ENDPOINT", "http://minio:9000"),
        "spark.sql.catalog.lake.s3.path-style-access": "true",
        "spark.sql.catalog.lake.s3.access-key-id": os.environ["AWS_ACCESS_KEY_ID"],
        "spark.sql.catalog.lake.s3.secret-access-key": os.environ["AWS_SECRET_ACCESS_KEY"],
        "spark.sql.session.timeZone": "UTC",
        "spark.sql.shuffle.partitions": "2",
        "spark.sql.adaptive.enabled": "true",
        "spark.ui.enabled": "false",
        "spark.driver.memory": "1500m",
        "spark.redaction.regex": "(?i)secret|password|token|access[.]?key|api[_-]?key",
        "spark.sql.catalog.lake.client.region": os.getenv("AWS_REGION", "us-east-1"),
    }
    builder = SparkSession.builder.master("local[2]").appName(name)
    for key, value in settings.items():
        builder = builder.config(key, value)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def ensure_bucket() -> None:
    """Tạo warehouse nếu chưa có; AccessDenied/network errors không được nuốt."""
    import boto3
    from botocore.exceptions import ClientError
    from air_quality.operations import wait_for_http

    wait_for_http(os.getenv("ICEBERG_CATALOG_URI", "http://catalog:8181") + "/v1/config")

    s3 = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT", "http://minio:9000"),
                      region_name=os.getenv("AWS_REGION", "us-east-1"))
    try:
        s3.head_bucket(Bucket="warehouse")
    except ClientError as error:
        if error.response["Error"]["Code"] not in {"404", "NoSuchBucket"}:
            raise
        s3.create_bucket(Bucket="warehouse")
