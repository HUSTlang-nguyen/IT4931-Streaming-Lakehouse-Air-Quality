"""Train/evaluate Spark MLlib RF, lưu model thật cùng manifest và Iceberg output.

RF không cần scaling/imputation. Chỉ fit train; chọn depth bằng validation;
test dùng đúng một lần sau chọn. Persistence và RF dùng cùng hàng đủ features.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.sql import DataFrame, SparkSession, Window, functions as F

from air_quality.collector.service import atomic_json
from air_quality.forecasting.features import FEATURES, chronological_splits, feature_rows, labelled_rows, split_bounds
from air_quality.observability.evidence import evidence_context
from air_quality.processing.tables import ensure_table, namespace_name


def utc_iso(value: datetime) -> str:
    """Spark trả datetime naive UTC do session UTC; ghi manifest có offset rõ ràng."""
    return value.replace(tzinfo=timezone.utc).isoformat()


def regression_metrics(frame: DataFrame, prediction: str) -> dict:
    """Một aggregation tính MAE/RMSE/count; từ chối sample rỗng/thiếu prediction.

    MAE dễ đọc theo đơn vị nguồn; RMSE phạt sai số lớn mạnh hơn. Caller truyền
    cùng scored frame cho RF và persistence để sample selection không đổi.
    """
    error = F.col(prediction) - F.col("label")
    row = frame.agg(F.count("*").alias("n"), F.count(error).alias("valid_count"), F.avg(F.abs(error)).alias("mae"),
                    F.sqrt(F.avg(error * error)).alias("rmse")).first()
    if not row.n or row.valid_count != row.n or row.mae is None:
        raise ValueError("Không có mẫu để đánh giá; không tạo metric giả")
    return {key: row[key] for key in ("n", "mae", "rmse")}


def merge_predictions(frame: DataFrame, namespace: str) -> None:
    """Idempotent theo model/sensor/target/mode; forecast đầu tiên được giữ.

    Không thay dự báo đã phát hành bằng lần chạy lại gần target hơn. Actual/error
    là enrichment riêng, vì có thể tới muộn hoặc được sửa sau forecast.
    """
    table = f"lake.{namespace_name(namespace)}.predictions"
    ensure_table(frame, table)
    frame.createOrReplaceTempView("incoming_predictions")
    frame.sparkSession.sql(f"""MERGE INTO {table} t USING incoming_predictions s
        ON t.model_version=s.model_version AND t.sensor_id=s.sensor_id
        AND t.target_time=s.target_time AND t.mode=s.mode
        WHEN NOT MATCHED THEN INSERT *""")


def prediction_frame(scored: DataFrame, version: str, snapshot: int, mode: str, issued: datetime) -> DataFrame:
    """Schema chung cho backtest/operational, không gán giả issued_at quá khứ."""
    return scored.select("sensor_id", "location_id", "station_name", F.col("period_end").alias("input_time"),
                         "target_time", "inputs_available_at", F.lit(issued).alias("issued_at"),
                         F.col("prediction").alias("predicted_value"), F.col("current_value").alias("baseline_value"),
                         F.lit("µg/m³").alias("unit"), F.lit(version).alias("model_version"),
                         F.lit(mode).alias("mode"), F.lit(snapshot).cast("long").alias("source_snapshot"),
                         F.lit(False).alias("stale_input"))


def enrich_actuals(spark: SparkSession, namespace: str) -> None:
    """Tạo bảng forecast/actual theo Gold hiện tại, actual chưa có giữ null.

    View SQL tái tính khi query: không cần sửa forecast và luôn phản ánh correction
    của actual. MAE backtest cố định vẫn ở manifest với snapshot riêng.
    """
    # REST Iceberg không hỗ trợ Spark persistent views ở mọi client: materialize
    # một bảng nhỏ atomic, gọi lại sau mỗi predict để nhận actual đến muộn.
    from air_quality.processing.tables import overwrite_table
    predictions = spark.table(f"lake.{namespace}.predictions")
    actual = spark.table(f"lake.{namespace}.hourly").filter("parameter_name='pm25' AND has_data").select(
        "sensor_id", F.col("period_end").alias("target_time"), F.col("value").alias("actual_value"))
    joined = predictions.join(actual, ["sensor_id", "target_time"], "left")
    joined = joined.withColumn("error", F.col("predicted_value") - F.col("actual_value"))
    overwrite_table(joined, f"lake.{namespace}.forecast_actual")


def train(spark: SparkSession, namespace: str = "live", model_root: Path = Path("models")) -> dict:
    """Pin Gold snapshot trước đọc; lưu immutable version và latest manifest sau thành công.

    Snapshot/version/config được hash để cùng dữ liệu có cùng đường dẫn model.
    Backtest là đánh giá hồi cứu trên snapshot, không chứng minh availability cũ.
    """
    namespace = namespace_name(namespace)
    table = f"lake.{namespace}.hourly"
    snapshot = spark.sql(f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1").first()[0]
    config = {"seed": 42, "numTrees": 30, "depth_candidates": [5, 8], "features": FEATURES, "split": [70, 15, 15]}
    version = "rf-" + hashlib.sha256(json.dumps([namespace, snapshot, config], sort_keys=True).encode()).hexdigest()[:16]
    root = model_root / version
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        report = json.loads(manifest_path.read_text())
        atomic_json(model_root / "latest.json", report)
        return report
    hourly = spark.read.option("snapshot-id", str(snapshot)).table(table).cache()
    samples = labelled_rows(hourly).cache()
    now = datetime.now(timezone.utc)
    report = {"model_version": version, "source_snapshot": snapshot, "namespace": namespace, "config": config,
              "trained_at": now.isoformat(), "evaluation_mode": "retrospective_snapshot_backtest",
              "limitation": "Historical ingestion availability unknown; not a historical operational simulation",
              "provenance": evidence_context(), "stations": []}
    metric_rows = []
    try:
        for sensor in hourly.filter("parameter_name='pm25'").select("sensor_id").distinct().collect():
            sensor_id = sensor.sensor_id
            rows = samples.filter(F.col("sensor_id") == sensor_id).cache()
            try:
                bounds = hourly.filter(F.col("sensor_id") == sensor_id).agg(F.min("period_end"), F.max("period_end")).first()
                cut_train, cut_validation = split_bounds(bounds[0], bounds[1])
                splits = {key: value.cache() for key, value in chronological_splits(rows, cut_train, cut_validation).items()}
                try:
                    counts = {key: frame.count() for key, frame in splits.items()}
                    if counts["train"] < 100 or min(counts["validation"], counts["test"]) < 30:
                        raise ValueError(f"Sensor {sensor_id}: thiếu mẫu train/validation/test {counts}")
                    candidates = []
                    for depth in config["depth_candidates"]:
                        pipeline = Pipeline(stages=[VectorAssembler(inputCols=FEATURES, outputCol="features", handleInvalid="error"),
                            RandomForestRegressor(featuresCol="features", labelCol="label", seed=42, numTrees=30, maxDepth=depth)])
                        model = pipeline.fit(splits["train"])
                        validation = regression_metrics(model.transform(splits["validation"]), "prediction")
                        candidates.append((validation["rmse"], depth, model, validation))
                    _, depth, model, validation = min(candidates, key=lambda item: (item[0], item[1]))
                    scored = model.transform(splits["test"]).cache()
                    try:
                        rf = regression_metrics(scored, "prediction")
                        baseline = regression_metrics(scored, "current_value")
                        path = root / str(sensor_id)
                        model.write().overwrite().save(str(path))
                        ranges = {key: {"first_input": utc_iso(r[0]), "last_input": utc_iso(r[1]), "last_target": utc_iso(r[2])}
                                  for key, frame in splits.items()
                                  for r in [frame.agg(F.min("period_end"), F.max("period_end"), F.max("target_time")).first()]}
                        station = {"sensor_id": sensor_id, "station_name": rows.first().station_name, "path": str(path),
                                   "counts": counts, "ranges": ranges, "train_end_exclusive": utc_iso(cut_train),
                                   "validation_end_exclusive": utc_iso(cut_validation), "selected_depth": depth,
                                   "validation_candidates": [{"depth": c[1], **c[3]} for c in candidates],
                                   "test_random_forest": rf, "test_persistence": baseline,
                                   "feature_importances": dict(zip(FEATURES, model.stages[-1].featureImportances.toArray().tolist()))}
                        report["stations"].append(station)
                        merge_predictions(prediction_frame(scored, version, snapshot, "backtest", now), namespace)
                        for algorithm, metrics in (("Random Forest", rf), ("Persistence", baseline)):
                            metric_rows.append((version, sensor_id, station["station_name"], algorithm, metrics["n"],
                                                metrics["mae"], metrics["rmse"], snapshot))
                    finally:
                        scored.unpersist()
                finally:
                    for frame in splits.values():
                        frame.unpersist()
            finally:
                rows.unpersist()
        metrics = spark.createDataFrame(metric_rows, "model_version STRING,sensor_id INT,station_name STRING,algorithm STRING,n LONG,mae DOUBLE,rmse DOUBLE,source_snapshot LONG")
        target = f"lake.{namespace}.model_metrics"
        ensure_table(metrics, target)
        metrics.createOrReplaceTempView("incoming_metrics")
        spark.sql(f"MERGE INTO {target} t USING incoming_metrics s ON t.model_version=s.model_version AND t.sensor_id=s.sensor_id AND t.algorithm=s.algorithm WHEN NOT MATCHED THEN INSERT *")
        enrich_actuals(spark, namespace)
        report["trained_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(manifest_path, report)
        atomic_json(model_root / "latest.json", report)
        atomic_json(Path("artifacts/reports/ml-evaluation.json"), report)
        return report
    finally:
        samples.unpersist()
        hourly.unpersist()


def predict(spark: SparkSession, namespace: str = "live", model_root: Path = Path("models"), issued_at: datetime | None = None) -> dict:
    """Phát hành chỉ khi input/model có trước issue và target còn ở tương lai.

    Không gọi API hoặc điền gap để ép có forecast. Trường hợp trễ/thiếu được
    báo per sensor, vẫn refresh actual cho các forecast đã phát hành trước đó.
    """
    namespace = namespace_name(namespace)
    manifest = json.loads((model_root / "latest.json").read_text())
    if manifest["namespace"] != namespace:
        raise ValueError("Model namespace khác dữ liệu forecast")
    issued = issued_at or datetime.now(timezone.utc)
    if datetime.fromisoformat(manifest["trained_at"]) > issued:
        raise ValueError("Model chưa tồn tại tại issued_at")
    table = f"lake.{namespace}.hourly"
    snapshot = spark.sql(f"SELECT snapshot_id FROM {table}.snapshots ORDER BY committed_at DESC LIMIT 1").first()[0]
    hourly = spark.read.option("snapshot-id", str(snapshot)).table(table)
    features = feature_rows(hourly, issued)
    result = {"issued_at": issued.isoformat(), "source_snapshot": snapshot, "model_version": manifest["model_version"], "stations": []}
    for station in manifest["stations"]:
        frame = features.filter(F.col("sensor_id") == station["sensor_id"]).orderBy(F.col("period_end").desc()).limit(1).cache()
        try:
            first = frame.first()
            if first is None:
                status = "missing_features"
            elif (issued.replace(tzinfo=None) - first.period_end).total_seconds() > 5400 or first.target_time <= issued.replace(tzinfo=None):
                status = "stale_input_target_expired"
            else:
                model = PipelineModel.load(station["path"])
                merge_predictions(prediction_frame(model.transform(frame), manifest["model_version"], snapshot, "operational", issued), namespace)
                status = "issued_or_already_exists"
            result["stations"].append({"sensor_id": station["sensor_id"], "status": status,
                                       "input_time": utc_iso(first.period_end) if first else None})
        finally:
            frame.unpersist()
    enrich_actuals(spark, namespace)
    result["provenance"] = evidence_context()
    atomic_json(Path("artifacts/reports/operational-forecast.json"), result)
    return result
