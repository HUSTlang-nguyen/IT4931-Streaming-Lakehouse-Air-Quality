"""Biến đổi DataFrame dùng chung batch/stream; không gọi API/Kafka/storage.

Một envelope giữ nguyên raw payload trong Bronze; normalize tạo period/value/
flags và metadata cần truy vấn. Invalid value vẫn được giữ, không biến thành 0.
"""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

from air_quality.config.settings import SENSORS


ENVELOPE_SCHEMA = StructType([
    StructField("schema_version", IntegerType()),
    *[StructField(name, StringType()) for name in (
        "event_id", "job_id", "station_name", "parameter_name", "series_kind", "ingest_mode",
        "ingested_at", "original_ingested_at", "request_from", "request_to", "raw_payload", "location_metadata")],
    StructField("location_id", IntegerType()), StructField("sensor_id", IntegerType()),
])

RAW_SCHEMA = """value DOUBLE, parameter STRUCT<name:STRING,units:STRING>,
 period STRUCT<label:STRING,interval:STRING,datetimeFrom:STRUCT<utc:STRING>,datetimeTo:STRUCT<utc:STRING>>,
 flagInfo STRUCT<hasFlags:BOOLEAN>, coverage STRUCT<observedCount:DOUBLE,percentCoverage:DOUBLE>"""

SILVER_KEYS = ["sensor_id", "series_kind", "period_start", "period_end"]


def parse_kafka(frame: DataFrame, allowed_modes: tuple[str, ...] = ("live", "backfill", "replay")) -> tuple[DataFrame, DataFrame]:
    """Tách envelope hợp lệ và dead-letter; giữ raw Kafka message khi sai schema.

    Dead-letter có key topic/partition/offset để retry không nhân đôi. Không
    drop event_id null một cách âm thầm rồi vẫn báo ingest thành công.
    """
    parsed = frame.select(F.col("value").cast("string").alias("message"),
                          F.col("topic").alias("kafka_topic"), F.col("partition").alias("kafka_partition"),
                          F.col("offset").alias("kafka_offset"))
    parsed = parsed.withColumn("event", F.from_json("message", ENVELOPE_SCHEMA))
    valid = F.coalesce((F.col("event.schema_version") == 1) & F.col("event.event_id").isNotNull()
                       & F.col("event.raw_payload").isNotNull()
                       & F.col("event.ingest_mode").isin(*allowed_modes), F.lit(False))
    dead = parsed.filter(~valid).drop("event").withColumn("reason", F.lit("invalid_envelope_or_mode"))
    good = parsed.filter(valid).select("event.*", "kafka_topic", "kafka_partition", "kafka_offset")
    good = good.withColumn("ingested_at", F.to_timestamp("ingested_at"))
    return good, dead


def normalize(frame: DataFrame) -> DataFrame:
    """Chuẩn hóa theo field nguồn, đánh cờ riêng value/unit/period/flags/metadata.

    Chỉ chuẩn hóa hai Unicode glyph micro; không tự đổi mg/m³ sang µg/m³.
    series_kind giữ raw và hours riêng dù có cùng sensor/khoảng đo.
    """
    df = frame.withColumn("raw", F.from_json("raw_payload", RAW_SCHEMA))
    df = (df.withColumn("period_start", F.to_timestamp("raw.period.datetimeFrom.utc"))
          .withColumn("period_end", F.to_timestamp("raw.period.datetimeTo.utc"))
          .withColumn("value", F.col("raw.value"))
          .withColumn("unit", F.regexp_replace("raw.parameter.units", "μ", "µ"))
          .withColumn("reported_interval", F.col("raw.period.interval"))
          .withColumn("observed_count", F.col("raw.coverage.observedCount").cast("int"))
          .withColumn("provider", F.get_json_object("location_metadata", "$.provider.name"))
          .withColumn("latitude", F.get_json_object("location_metadata", "$.coordinates.latitude").cast("double"))
          .withColumn("longitude", F.get_json_object("location_metadata", "$.coordinates.longitude").cast("double")))
    known = F.lit(False)
    for sensor in SENSORS:
        known = known | ((F.col("sensor_id") == sensor.sensor_id) & (F.col("location_id") == sensor.location_id)
                         & (F.col("parameter_name") == sensor.parameter))
    invalid_value = F.col("value").isNull() | F.isnan("value") | (F.abs(F.col("value")) == float("inf")) | (F.col("value") < 0)
    invalid_period = (F.col("period_start").isNull() | F.col("period_end").isNull()
                      | (F.col("period_end") <= F.col("period_start")))
    invalid_hour = (F.col("series_kind") == "hours") & (
        ((F.col("period_end").cast("long") - F.col("period_start").cast("long")) != 3600)
        | (F.minute("period_end") != 0) | (F.second("period_end") != 0))
    flags = F.array(
        F.when(invalid_value, F.lit("invalid_value")),
        F.when(~F.coalesce(F.col("unit") == "µg/m³", F.lit(False)), F.lit("unexpected_unit")),
        F.when(invalid_period | invalid_hour, F.lit("invalid_period")),
        F.when(F.col("raw.flagInfo.hasFlags") == True, F.lit("source_flagged")),
        F.when(~F.coalesce(known & (F.col("raw.parameter.name") == F.col("parameter_name")), F.lit(False)), F.lit("metadata_mismatch")),
        F.when(~F.coalesce(F.col("series_kind").isin("measurements", "hours"), F.lit(False)), F.lit("unknown_series")),
        F.when(F.col("ingested_at").isNull(), F.lit("invalid_ingested_at")),
    )
    return df.withColumn("quality_flags", F.filter(flags, lambda item: item.isNotNull())).select(
        "location_id", "sensor_id", "station_name", "parameter_name", "series_kind", "period_start", "period_end",
        "value", "unit", "reported_interval", "ingested_at", "event_id", "job_id", "ingest_mode",
        "quality_flags", "observed_count", "provider", "latitude", "longitude")


def latest_per_key(frame: DataFrame, keys: list[str]) -> DataFrame:
    """Chọn correction mới nhất xác định được; retry/thứ tự partition không đổi kết quả."""
    window = Window.partitionBy(*keys).orderBy(F.col("ingested_at").desc_nulls_last(), F.col("event_id").desc())
    return frame.withColumn("_rank", F.row_number().over(window)).filter("_rank = 1").drop("_rank")


def hourly_gold(silver: DataFrame) -> DataFrame:
    """Tạo grid giờ đầy đủ và left join, giữ null cho gap/invalid thay vì nối liền.

    Target là mean nguồn /hours. Không tính trung bình từ raw intervals chồng
    nhau. Grid giúp dashboard/ML có khái niệm một giờ thực kể cả khi không có hàng.
    """
    hours = silver.filter("series_kind = 'hours'")
    bounds = hours.agg(F.min("period_end").alias("first_hour"), F.max("period_end").alias("last_hour"))
    registry = silver.sparkSession.createDataFrame(
        [(s.sensor_id, s.location_id, s.station_name, s.parameter) for s in SENSORS],
        "sensor_id INT, location_id INT, station_name STRING, parameter_name STRING")
    grid = registry.crossJoin(bounds).withColumn("period_end", F.explode(F.sequence("first_hour", "last_hour", F.expr("INTERVAL 1 HOUR")))).drop("first_hour", "last_hour")
    source = hours.select("sensor_id", "period_end", F.col("value").alias("source_value"), "quality_flags", "observed_count", "ingested_at")
    joined = grid.join(source, ["sensor_id", "period_end"], "left")
    valid = F.coalesce((F.size("quality_flags") == 0) & F.col("source_value").isNotNull(), F.lit(False))
    return (joined.withColumn("has_data", valid)
            .withColumn("value", F.when(valid, F.col("source_value")))
            .withColumn("period_start", F.col("period_end") - F.expr("INTERVAL 1 HOUR"))
            .withColumn("quality_flags", F.coalesce("quality_flags", F.array(F.lit("missing"))))
            .withColumn("unit", F.lit("µg/m³")).drop("source_value"))


def daily_gold(hourly: DataFrame) -> DataFrame:
    """Mean các giờ hợp lệ theo ngày Việt Nam; luôn báo count và expected24.

    Trừ một giây khỏi end để giờ kết thúc 00:00 thuộc ngày vừa kết thúc, không
    bị đẩy sang ngày sau. Ngày ở biên dataset có window_bins<24 được thể hiện rõ.
    """
    local_date = F.to_date(F.from_utc_timestamp(F.col("period_end") - F.expr("INTERVAL 1 SECOND"), "Asia/Ho_Chi_Minh"))
    return (hourly.withColumn("local_date", local_date)
            .groupBy("sensor_id", "location_id", "station_name", "parameter_name", "local_date")
            .agg(F.avg("value").alias("mean_value"), F.count("value").alias("valid_hours"), F.count("*").alias("window_bins"))
            .withColumn("expected_hours", F.lit(24)).withColumn("coverage_percent", F.col("valid_hours") / 24 * 100)
            .withColumn("unit", F.lit("µg/m³")))
