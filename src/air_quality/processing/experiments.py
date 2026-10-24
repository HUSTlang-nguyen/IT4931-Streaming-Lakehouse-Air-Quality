"""Thực nghiệm Iceberg trên bản sao dữ liệu thật, không sửa/xóa bảng live.

Bốn lần append cố ý tạo small files để có thí nghiệm compaction tái lập.
Không nhân bản hàng, không giả tốc độ tăng; timing gồm warmup và ba lần đo.
"""

import time
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

from air_quality.collector.service import atomic_json
from air_quality.observability.evidence import evidence_context
from air_quality.processing.tables import ensure_table, namespace_name


def snapshot_id(spark: SparkSession, table: str) -> int:
    """ID snapshot mới nhất để dùng time travel độc lập với snapshot live khác."""
    return spark.sql(f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1").first()[0]


def measure(spark: SparkSession, table: str) -> dict:
    """Metadata file count/size, exact files chạm vào tháng7 và plan có filters."""
    files = spark.table(table + ".files").filter("content=0")
    totals = files.agg(F.count("*").alias("files"), F.sum("file_size_in_bytes").alias("bytes"),
                       F.sum("record_count").alias("records")).first().asDict()
    filtered = spark.table(table).filter("period_end >= TIMESTAMP '2026-07-01 00:00:00' AND period_end < TIMESTAMP '2026-08-01 00:00:00'")
    selected = filtered.select("_file").distinct().count()
    # SUM(double) phụ thuộc thứ tự cộng sau rewrite. Decimal ở bước kiểm tổng
    # cho kết quả xác định; kiểm exceptAll bên dưới còn đối chiếu nguyên hàng.
    query = filtered.groupBy("sensor_id").agg(F.count("*").alias("n"),
        F.sum(F.col("value").cast("decimal(25,8)")).cast("double").alias("total"))
    timings = []
    result = None
    for index in range(4):
        start = time.perf_counter()
        result = sorted([row.asDict() for row in query.collect()], key=lambda row: row["sensor_id"])
        if index:
            timings.append(time.perf_counter() - start)
    plan = query._jdf.queryExecution().executedPlan().toString()
    return {**totals, "selected_files_july": selected, "pruned_files": totals["files"] - selected,
            "filtered_result": result, "spark_seconds_3_runs_after_warmup": timings, "spark_plan": plan,
            "snapshot": snapshot_id(spark, table)}


def prepare(spark: SparkSession, namespace: str) -> dict:
    """Pin Silver snapshot rồi chép đúng mỗi hàng vào một trong bốn lần append.

    Namespace experiment_* obligatoire; chaque appel CLI utilise un nouveau nom.
    Refuse de recréer une table existante pour préserver la preuve précédente.
    """
    namespace = namespace_name(namespace)
    if not namespace.startswith("experiment_"):
        raise ValueError("Benchmark exige namespace experiment_*")
    table = f"lake.{namespace}.observations"
    if spark.catalog.tableExists(table):
        raise ValueError("Namespace benchmark déjà utilisé; choisir un nouveau nom")
    source_snapshot = snapshot_id(spark, "lake.live.silver")
    source = spark.read.option("snapshot-id", str(source_snapshot)).table("lake.live.silver").cache()
    try:
        spark.sql(f"CREATE NAMESPACE IF NOT EXISTS lake.{namespace}")
        ensure_table(source, table, "month")
        for chunk in range(4):
            # pmod hash stable: une ligne appartient exactement à un chunk.
            source.filter(F.pmod(F.xxhash64(*[F.col(c) for c in ["sensor_id", "series_kind", "period_start", "period_end"]]), F.lit(4)) == chunk).repartition(2).writeTo(table).append()
        before = measure(spark, table)
        count = source.count()
        assert before["records"] == count
        assert before["pruned_files"] > 0
        report = {"namespace": namespace, "table": table, "source_table": "lake.live.silver", "source_snapshot": source_snapshot,
                  "source_count": count, "dataset": "exact real-source copy, no row replication; four appends intentionally create small files",
                  "filter": "2026-07-01 <= period_end < 2026-08-01 UTC", "before": before, "provenance": evidence_context()}
        atomic_json(Path("artifacts/local/benchmark-prepare.json"), report)
        return report
    finally:
        source.unpersist()


def compact(spark: SparkSession, namespace: str) -> dict:
    """Gộp file nhỏ, giữ snapshots; đối chiếu số dòng/tổng hợp và time travel."""
    namespace = namespace_name(namespace)
    if not namespace.startswith("experiment_"):
        raise ValueError("Compaction lab chỉ dùng namespace experiment_*")
    table = f"lake.{namespace}.observations"
    before = measure(spark, table)
    output = spark.sql(f"""CALL lake.system.rewrite_data_files(table => '{namespace}.observations',
        options => map('rewrite-all','true','target-file-size-bytes','67108864'))""").collect()
    spark.catalog.refreshTable(table)
    after = measure(spark, table)
    historical = spark.read.option("snapshot-id", str(before["snapshot"])).table(table).count()
    old_rows = spark.read.option("snapshot-id", str(before["snapshot"])).table(table)
    current_rows = spark.table(table)
    exact_differences = old_rows.exceptAll(current_rows).count() + current_rows.exceptAll(old_rows).count()
    assert exact_differences == 0
    assert historical == before["records"] == after["records"]
    assert before["filtered_result"] == after["filtered_result"]
    report = {"namespace": namespace, "before": before, "after": after, "rewrite_result": [row.asDict() for row in output],
              "time_travel_count": historical, "exact_row_differences": exact_differences,
              "content_equal": True, "provenance": evidence_context()}
    atomic_json(Path("artifacts/local/benchmark-compact.json"), report)
    return report
