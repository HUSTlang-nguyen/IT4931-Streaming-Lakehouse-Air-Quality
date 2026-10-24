"""Lab Spark/Iceberg thật: duplicate, correction, late data, gap và quarantine.

Chạy trong container runtime với --run-integration, không trên Python3.13 host.
Mỗi kịch bản có namespace replay_test_* mới, tách hoàn toàn dữ liệu live. Giữ
bảng/snapshot để có thể đối chiếu thay vì xóa volume sau test.
"""

import json
from datetime import timedelta
from uuid import uuid4

import pytest

pytest.importorskip("pyspark")
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType

from air_quality.config.settings import SENSORS
from air_quality.contracts.events import iso_utc, make_event, utc_datetime
from air_quality.processing.session import ensure_bucket, spark_session
from air_quality.processing.tables import process_events
from air_quality.processing.transforms import ENVELOPE_SCHEMA, normalize, parse_kafka


pytestmark = pytest.mark.integration
START = utc_datetime("2026-01-01T00:00:00Z")


@pytest.fixture(scope="module")
def spark():
    """Một SparkContext cho module để không nhân JVM/RAM trên laptop."""
    ensure_bucket()
    session = spark_session("air-quality-integration-tests")
    yield session
    session.stop()


def event(hour: int, value: float | None, observation: int = 0) -> dict:
    """Synthetic giờ nguồn với provenance replay; không phải phép đo live."""
    end = START + timedelta(hours=hour)
    raw = {"value": value, "parameter": {"name": "pm25", "units": "µg/m³"},
           "period": {"interval": "01:00:00", "datetimeFrom": {"utc": iso_utc(end - timedelta(hours=1))},
                      "datetimeTo": {"utc": iso_utc(end)}}, "flagInfo": {"hasFlags": False},
           "coverage": {"observedCount": 12}}
    return make_event(SENSORS[0], "hours", raw, {"provider": {"name": "synthetic fixture"}},
                      f"fixture-{hour}-{observation}", 1, 0, START + timedelta(days=1, minutes=observation),
                      "replay", START - timedelta(hours=1), START + timedelta(days=1))


def frame(spark, events):
    """Tạo cùng schema mà parse_kafka trả về, gồm audit Kafka synthetic rõ ràng."""
    # Offset phải là dữ liệu xác định, giống Kafka thật. Không sinh bằng
    # monotonically_increasing_id vì Catalyst cấm lineage nondeterministic trong MERGE.
    schema = StructType([*ENVELOPE_SCHEMA.fields, StructField("kafka_topic", StringType()),
                         StructField("kafka_partition", IntegerType()), StructField("kafka_offset", LongType())])
    rows = [{**row, "kafka_topic": "air-quality.replay.test", "kafka_partition": 0, "kafka_offset": index}
            for index, row in enumerate(events)]
    return spark.createDataFrame(rows, schema).withColumn("ingested_at", F.to_timestamp("ingested_at"))


def test_duplicate_correction_and_old_observation(spark):
    namespace = "replay_test_" + uuid4().hex[:10]
    original = event(1, 10)
    process_events(frame(spark, [original, original]), namespace)
    assert spark.table(f"lake.{namespace}.bronze").count() == 1
    assert spark.table(f"lake.{namespace}.silver").count() == 1
    correction = event(1, 25, observation=2)
    process_events(frame(spark, [correction]), namespace)
    process_events(frame(spark, [original]), namespace)
    silver = spark.table(f"lake.{namespace}.silver").collect()
    assert len(silver) == 1 and silver[0].value == 25
    assert spark.table(f"lake.{namespace}.hourly").filter("sensor_id=13502154").first().value == 25


def test_late_data_fills_gap_and_refreshes_daily(spark):
    namespace = "replay_test_" + uuid4().hex[:10]
    process_events(frame(spark, [event(1, 10), event(3, 30)]), namespace)
    before = spark.table(f"lake.{namespace}.hourly").filter("sensor_id=13502154").orderBy("period_end").collect()
    assert len(before) == 3 and before[1].value is None and not before[1].has_data
    process_events(frame(spark, [event(2, 50, observation=10)]), namespace)
    after = spark.table(f"lake.{namespace}.hourly").filter("sensor_id=13502154").orderBy("period_end").collect()
    assert [row.value for row in after] == [10, 50, 30]
    daily = spark.table(f"lake.{namespace}.daily").filter("sensor_id=13502154").first()
    assert daily.valid_hours == 3 and daily.mean_value == 30


def test_invalid_correction_removes_previous_gold_value(spark):
    namespace = "replay_test_" + uuid4().hex[:10]
    process_events(frame(spark, [event(1, 20)]), namespace)
    process_events(frame(spark, [event(1, -1, observation=1)]), namespace)
    silver = spark.table(f"lake.{namespace}.silver").first()
    assert silver.value == -1 and "invalid_value" in silver.quality_flags
    gold = spark.table(f"lake.{namespace}.hourly").filter("sensor_id=13502154").first()
    assert gold.value is None and not gold.has_data


def test_missing_period_retained_bronze_and_rejected(spark):
    namespace = "replay_test_" + uuid4().hex[:10]
    bad = event(1, 20)
    raw = json.loads(bad["raw_payload"])
    raw["period"]["datetimeFrom"] = None
    bad["raw_payload"] = json.dumps(raw)
    result = process_events(frame(spark, [bad]), namespace)
    assert result == {"events": 1, "rejected": 1}
    assert spark.table(f"lake.{namespace}.bronze").count() == 1
    assert spark.table(f"lake.{namespace}.rejected").count() == 1


def test_normalize_retains_invalid_and_handles_timezone(spark):
    bad = event(1, None)
    raw = json.loads(bad["raw_payload"])
    raw["parameter"]["units"] = "mg/m³"
    raw["period"]["datetimeTo"]["utc"] = "2026-01-01T08:00:00+07:00"
    bad["raw_payload"] = json.dumps(raw)
    row = normalize(frame(spark, [bad])).first()
    assert set(row.quality_flags) == {"invalid_value", "unexpected_unit"}
    assert row.period_end.hour == 1


def test_replay_message_on_live_topic_is_dead_letter(spark):
    replay = event(1, 20)
    replay["original_ingested_at"] = "2026-01-01T00:00:00Z"
    message = json.dumps(replay)
    source = spark.createDataFrame([(message, "air-quality.live", 0, 12)], "value STRING, topic STRING, partition INT, offset LONG")
    good, dead = parse_kafka(source, ("live", "backfill"))
    assert good.count() == 0
    assert dead.first().message == message
    allowed, _ = parse_kafka(source, ("replay",))
    assert allowed.first().original_ingested_at == replay["original_ingested_at"]


def test_nullable_schema_evolution_preserves_old_bronze(spark):
    from air_quality.processing.tables import ensure_table, merge_bronze
    namespace = "replay_test_" + uuid4().hex[:10]
    spark.sql(f"CREATE NAMESPACE lake.{namespace}")
    table = f"lake.{namespace}.bronze"
    original = frame(spark, [event(1, 10)])
    ensure_table(original.drop("original_ingested_at"), table)
    original.drop("original_ingested_at").writeTo(table).append()
    correction = frame(spark, [event(2, 20)]).withColumn("original_ingested_at", F.lit("2026-01-01T00:00:00Z"))
    # Fixture withColumn(lit) mặc định non-nullable; schema replay thực là nullable.
    correction = spark.createDataFrame(correction.collect(), original.schema)
    merge_bronze(correction, namespace)
    assert spark.table(table).count() == 2
    assert spark.table(table).filter("original_ingested_at IS NULL").count() == 1
