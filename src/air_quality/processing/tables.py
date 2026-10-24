"""Iceberg writes có thể retry; ranh giới transaction là từng bảng, không cả pipeline.

Nếu process chết sau Silver trước Gold, Kafka checkpoint chưa tiến nên cùng
micro-batch chạy lại; MERGE không nhân đôi rồi Gold được tái tạo để phục hồi.
"""

import re

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from air_quality.processing.transforms import SILVER_KEYS, daily_gold, hourly_gold, latest_per_key, normalize


def namespace_name(value: str) -> str:
    """Chỉ cho identifier đơn, không đưa user text chưa kiểm tra vào Spark SQL."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", value):
        raise ValueError("Namespace phải là identifier chữ thường/số/underscore")
    return value


def ensure_table(frame: DataFrame, name: str, partition: str | None = None) -> None:
    """Tạo bảng Iceberg v2; chỉ bổ sung cột nullable mới, giữ dữ liệu/schema cũ.

    Ví dụ original_ingested_at của replay được thêm sau checkpoint ban đầu.
    Không tự đổi type/drop cột: thay đổi đó cần migration có chủ đích.
    """
    spark = frame.sparkSession
    if spark.catalog.tableExists(name):
        existing = set(spark.table(name).columns)
        missing = [field for field in frame.schema if field.name not in existing]
        if any(not field.nullable for field in missing):
            raise ValueError("Cột mới không nullable cần migration tường minh")
        if missing:
            definitions = ", ".join(f"`{field.name.replace('`', '``')}` {field.dataType.simpleString()}" for field in missing)
            spark.sql(f"ALTER TABLE {name} ADD COLUMNS ({definitions})")
        return
    writer = (frame.limit(0).writeTo(name).using("iceberg").tableProperty("format-version", "2")
              .tableProperty("write.target-file-size-bytes", "67108864"))
    if partition == "month":
        writer = writer.partitionedBy(F.months("period_end"))
    elif partition == "day":
        writer = writer.partitionedBy(F.days("ingested_at"))
    writer.create()


def merge_bronze(frame: DataFrame, namespace: str) -> None:
    """Giữ một lần quan sát event_id; Kafka retry có offset mới không nhân raw logic."""
    table = f"lake.{namespace}.bronze"
    source = latest_per_key(frame, ["event_id"])
    ensure_table(source, table, "day")
    source.createOrReplaceTempView("incoming_bronze")
    frame.sparkSession.sql(f"""MERGE INTO {table} t USING incoming_bronze s ON t.event_id=s.event_id
        WHEN NOT MATCHED THEN INSERT *""")


def merge_silver(frame: DataFrame, namespace: str) -> None:
    """Upsert theo business key; chỉ observation mới hơn được sửa số đo hiện tại."""
    table = f"lake.{namespace}.silver"
    source = latest_per_key(frame, SILVER_KEYS)
    ensure_table(source, table, "month")
    source.createOrReplaceTempView("incoming_silver")
    condition = " AND ".join(f"t.{key}=s.{key}" for key in SILVER_KEYS)
    frame.sparkSession.sql(f"""MERGE INTO {table} t USING incoming_silver s ON {condition}
        WHEN MATCHED AND ((s.ingested_at IS NOT NULL AND t.ingested_at IS NULL)
            OR s.ingested_at > t.ingested_at OR
            ((s.ingested_at <=> t.ingested_at) AND s.event_id>t.event_id)) THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *""")


def overwrite_table(frame: DataFrame, table: str, partition: str | None = None) -> None:
    """Một snapshot atomic thay toàn nội dung; không truncate rồi append để lộ bảng rỗng."""
    ensure_table(frame, table, partition)
    frame.writeTo(table).overwrite(F.lit(True))


def refresh_gold(spark: SparkSession, namespace: str) -> None:
    """Tái tính từ Silver hiện tại để late/correction xóa cả kết quả cũ sai.

    Phạm vi hai trạm nhỏ: full refresh dễ giải thích và kiểm chứng. Không giả
    đây là chiến lược tối ưu cho hàng tỷ dòng; benchmark sẽ ghi quy mô thực tế.
    """
    silver = spark.table(f"lake.{namespace}.silver")
    hourly = hourly_gold(silver).cache()
    try:
        overwrite_table(hourly, f"lake.{namespace}.hourly", "month")
        overwrite_table(daily_gold(hourly), f"lake.{namespace}.daily")
        freshness = (silver.groupBy("sensor_id", "location_id", "station_name", "parameter_name", "series_kind")
                     .agg(F.max("period_end").alias("last_measurement_at"), F.max("ingested_at").alias("last_ingested_at"),
                          F.count("*").alias("records"), F.sum((F.size("quality_flags") == 0).cast("int")).alias("valid_records")))
        overwrite_table(freshness, f"lake.{namespace}.freshness")
    finally:
        hourly.unpersist()


def process_events(frame: DataFrame, namespace: str, refresh: bool = True) -> dict[str, int]:
    """Bronze → Silver → Gold dùng chung cho batch hoặc foreachBatch.

    Thiếu period không thể tạo business key: giữ ở Bronze/rejected thay vì
    MERGE null-key sinh trùng. Invalid value có key vẫn ở Silver với flags.
    """
    namespace = namespace_name(namespace)
    spark = frame.sparkSession
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS lake.{namespace}")
    frame = frame.cache()
    try:
        count = frame.count()
        if not count:
            return {"events": 0, "rejected": 0}
        merge_bronze(frame, namespace)
        cleaned = normalize(frame).cache()
        try:
            # Mọi thành phần MERGE key phải non-null; SQL '=' không match null,
            # nếu chỉ kiểm sensor/period thì thiếu series_kind sẽ nhân Silver.
            valid_key = F.lit(True)
            for key in SILVER_KEYS:
                valid_key = valid_key & F.col(key).isNotNull()
            # MERGE vào bảng rỗng sẽ insert cả hai source rows cùng event_id;
            # dedup source trước, giống Bronze, để quarantine cũng retry an toàn.
            rejected = latest_per_key(cleaned.filter(~valid_key), ["event_id"])
            rejected_count = rejected.count()
            if rejected_count:
                table = f"lake.{namespace}.rejected"
                ensure_table(rejected, table)
                rejected.createOrReplaceTempView("incoming_rejected")
                spark.sql(f"MERGE INTO {table} t USING incoming_rejected s ON t.event_id=s.event_id WHEN NOT MATCHED THEN INSERT *")
            accepted = cleaned.filter(valid_key)
            if accepted.limit(1).count():
                merge_silver(accepted, namespace)
                if refresh:
                    refresh_gold(spark, namespace)
            return {"events": count, "rejected": rejected_count}
        finally:
            cleaned.unpersist()
    finally:
        frame.unpersist()
