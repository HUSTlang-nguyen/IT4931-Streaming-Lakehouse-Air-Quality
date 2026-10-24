"""Entrypoint Spark container: smoke và Kafka ingest, không cần Python Spark trên host.

Tất cả data transformations ở transforms.py, storage ở tables.py. Lệnh smoke
phải ghi/đọc được bảng thật S3/REST catalog, không chỉ kiểm import Spark.
"""

import argparse
import json
import os
import signal
from pathlib import Path

from filelock import FileLock
from pyspark.sql import functions as F

from air_quality.collector.service import atomic_json
from air_quality.observability.evidence import evidence_context
from air_quality.processing.session import ensure_bucket, spark_session
from air_quality.processing.tables import ensure_table, namespace_name, process_events, refresh_gold
from air_quality.processing.transforms import parse_kafka


def ingest(namespace: str, topic: str, checkpoint: Path, continuous: bool, max_offsets: int) -> None:
    """Đọc Kafka Structured Streaming; availableNow cho backfill và continuous cho live.

    foreachBatch có at-least-once; MERGE/Gold refresh idempotent tạo kết quả
    đúng dù retry sau crash giữa các bảng. FileLock giữ một writer/namespace.
    """
    namespace = namespace_name(namespace)
    if namespace == "live" and topic != "air-quality.live":
        raise ValueError("Namespace live chỉ nhận topic air-quality.live")
    if namespace.startswith("replay") and not topic.startswith("air-quality.replay."):
        raise ValueError("Namespace replay chỉ nhận topic replay")
    if namespace != "live" and not namespace.startswith("replay"):
        raise ValueError("Ingest namespace phải là live hoặc replay_*")
    checkpoint.mkdir(parents=True, exist_ok=True)
    with FileLock(checkpoint.parent / f"writer-{namespace}.lock", timeout=1):
        ensure_bucket()
        spark = spark_session("air-quality-ingest")
        try:
            stream = (spark.readStream.format("kafka")
                      .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
                      .option("subscribe", topic).option("startingOffsets", "earliest")
                      .option("failOnDataLoss", "true").option("maxOffsetsPerTrigger", max_offsets).load())

            def batch(frame, batch_id):
                modes = ("live", "backfill") if namespace == "live" else ("replay",)
                good, dead = parse_kafka(frame, modes)
                spark.sql(f"CREATE NAMESPACE IF NOT EXISTS lake.{namespace}")
                dead_count = dead.count()
                if dead_count:
                    table = f"lake.{namespace}.dead_letter"
                    ensure_table(dead, table)
                    dead.createOrReplaceTempView("incoming_dead")
                    spark.sql(f"""MERGE INTO {table} t USING incoming_dead s
                        ON t.kafka_topic=s.kafka_topic AND t.kafka_partition=s.kafka_partition AND t.kafka_offset=s.kafka_offset
                        WHEN NOT MATCHED THEN INSERT *""")
                result = process_events(good, namespace)
                report = {"batch_id": batch_id, "topic": topic, "namespace": namespace,
                          "dead_letter": dead_count, **result, "provenance": evidence_context()}
                atomic_json(Path(f"artifacts/local/ingest-{namespace}-{batch_id}.json"), report)
                print(json.dumps(report), flush=True)

            writer = stream.writeStream.foreachBatch(batch).option("checkpointLocation", str(checkpoint))
            query = (writer.trigger(processingTime="60 seconds") if continuous else writer.trigger(availableNow=True)).start()
            if continuous:
                signal.signal(signal.SIGTERM, lambda *_: query.stop())
                while query.isActive:
                    atomic_json(Path("artifacts/local/processor-heartbeat.json"), {
                        "query_active": query.isActive, "status": query.status,
                        "last_progress": query.lastProgress.get("timestamp") if query.lastProgress else None,
                    })
                    query.awaitTermination(30)
            else:
                query.awaitTermination()
        finally:
            spark.stop()


def smoke() -> None:
    """Viết bảng Iceberg thật rồi đọc lại; giữ bảng để Trino đối chiếu cùng catalog."""
    ensure_bucket()
    spark = spark_session("air-quality-smoke")
    try:
        spark.sql("CREATE NAMESPACE IF NOT EXISTS lake.validation")
        table = "lake.validation.smoke"
        frame = spark.createDataFrame([(1, "Spark / REST / MinIO")], "id INT, message STRING")
        ensure_table(frame, table)
        frame.writeTo(table).overwrite(F.lit(True))
        rows = [row.asDict() for row in spark.table(table).collect()]
        assert rows == [{"id": 1, "message": "Spark / REST / MinIO"}]
        report = {"spark_version": spark.version, "table": table, "rows": rows, "provenance": evidence_context()}
        atomic_json(Path("artifacts/reports/spark-smoke.json"), report)
        print(json.dumps(report), flush=True)
    finally:
        spark.stop()


def main() -> None:
    """Parse job arguments, không tự chuyển Kafka/live thành fixture khi nguồn lỗi."""
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("smoke")
    for action in ("train", "predict", "benchmark-prepare", "benchmark-compact"):
        ml = commands.add_parser(action)
        ml.add_argument("--namespace", default="live")
        ml.add_argument("--model-root", type=Path, default=Path("models"))
    worker = commands.add_parser("ingest")
    worker.add_argument("--namespace", default="live")
    worker.add_argument("--topic", default="air-quality.live")
    worker.add_argument("--checkpoint", type=Path, default=Path("checkpoints/spark/live"))
    worker.add_argument("--continuous", action="store_true")
    worker.add_argument("--max-offsets", type=int, default=20000)
    gold = commands.add_parser("refresh-gold")
    gold.add_argument("--namespace", default="live")
    args = parser.parse_args()
    if args.command == "smoke":
        smoke()
    elif args.command in {"train", "predict"}:
        from air_quality.forecasting.model import predict, train
        with FileLock(Path("checkpoints/forecast-writer.lock"), timeout=1):
            session = spark_session("air-quality-" + args.command)
            try:
                result = (train if args.command == "train" else predict)(session, args.namespace, args.model_root)
                print(json.dumps(result), flush=True)
            finally:
                session.stop()
    elif args.command in {"benchmark-prepare", "benchmark-compact"}:
        from air_quality.processing.experiments import compact, prepare
        session = spark_session("air-quality-benchmark")
        try:
            result = (prepare if args.command == "benchmark-prepare" else compact)(session, args.namespace)
            print(json.dumps({"namespace": args.namespace, "completed": args.command}), flush=True)
        finally:
            session.stop()
    elif args.command == "ingest":
        if args.max_offsets <= 0:
            parser.error("max-offsets phải dương")
        ingest(args.namespace, args.topic, args.checkpoint, args.continuous, args.max_offsets)
    else:
        spark = spark_session("air-quality-gold")
        try:
            refresh_gold(spark, namespace_name(args.namespace))
        finally:
            spark.stop()


if __name__ == "__main__":
    main()
