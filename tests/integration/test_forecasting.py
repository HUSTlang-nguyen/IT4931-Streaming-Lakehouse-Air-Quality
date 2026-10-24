"""Kiểm chứng causal features, gaps, availability, split purge và cùng mẫu metrics.

Fixture cố ý có một giờ thiếu và một correction chỉ thu sau issued_at. Tests
không train model trên fixture để rồi coi là bằng chứng accuracy dữ liệu thật.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

pytest.importorskip("pyspark")
from pyspark.sql import functions as F

from air_quality.forecasting.features import FEATURES, chronological_splits, feature_rows, labelled_rows, split_bounds
from air_quality.forecasting.model import regression_metrics
from air_quality.processing.session import spark_session


pytestmark = pytest.mark.integration
START = datetime(2026, 1, 1)


@pytest.fixture(scope="module")
def spark():
    session = spark_session("air-quality-ml-tests")
    yield session
    session.stop()


def hourly(spark, missing=(), late_hour=None):
    rows = [(1, 10, "synthetic", "pm25", START + timedelta(hours=h), float(h), True,
             START + timedelta(hours=h, minutes=5) if h != late_hour else START + timedelta(days=10))
            for h in range(100) if h not in missing]
    return spark.createDataFrame(rows, "sensor_id INT,location_id INT,station_name STRING,parameter_name STRING,period_end TIMESTAMP,value DOUBLE,has_data BOOLEAN,ingested_at TIMESTAMP")


def test_exact_lags_do_not_cross_gaps(spark):
    frame = feature_rows(hourly(spark, missing=(25,)))
    # t=26 cần lag1 ở25, không được thay bằng hàng24 dù nó liền trước trong file.
    assert frame.filter(F.col("period_end") == START + timedelta(hours=26)).count() == 0
    row = frame.filter(F.col("period_end") == START + timedelta(hours=50)).first()
    assert [row[name] for name in FEATURES[:5]] == [50, 49, 48, 47, 26]


def test_label_is_next_exact_hour_and_not_feature(spark):
    row = labelled_rows(hourly(spark)).filter(F.col("period_end") == START + timedelta(hours=30)).first()
    assert row.label == 31 and row.target_time == START + timedelta(hours=31)
    assert "label" not in FEATURES and max(row[name] for name in FEATURES[:5]) <= 30


def test_operational_availability_checks_all_lags(spark):
    issue = (START + timedelta(hours=50, minutes=30)).replace(tzinfo=timezone.utc)
    frame = feature_rows(hourly(spark, late_hour=26), issue)
    assert frame.filter(F.col("period_end") == START + timedelta(hours=50)).count() == 0
    assert frame.filter(F.col("period_end") > F.lit(issue)).count() == 0


def test_chronological_split_purges_boundary_labels(spark):
    train_end, val_end = split_bounds(START, START + timedelta(hours=99))
    assert train_end == START + timedelta(hours=70) and val_end == START + timedelta(hours=85)
    parts = chronological_splits(labelled_rows(hourly(spark)), train_end, val_end)
    assert parts["train"].agg(F.max("target_time")).first()[0] < train_end
    assert parts["validation"].agg(F.min("period_end"), F.max("target_time")).first()[1] < val_end
    assert parts["test"].agg(F.min("period_end")).first()[0] >= val_end
    assert parts["train"].filter(F.col("period_end") == START + timedelta(hours=69)).count() == 0


def test_metrics_use_same_complete_rows(spark):
    frame = spark.createDataFrame([(10., 12., 10.), (20., 18., 25.)], "label DOUBLE,prediction DOUBLE,current_value DOUBLE")
    rf, baseline = regression_metrics(frame, "prediction"), regression_metrics(frame, "current_value")
    assert rf == {"n": 2, "mae": 2., "rmse": 2.}
    assert baseline["n"] == rf["n"] and baseline["mae"] == 2.5
    with pytest.raises(ValueError):
        regression_metrics(frame.withColumn("prediction", F.lit(None).cast("double")), "prediction")


def test_prediction_retry_keeps_first_issue_and_refreshes_actual(spark, tmp_path, monkeypatch):
    import json
    from air_quality.forecasting import model as module
    from air_quality.forecasting.model import enrich_actuals, merge_predictions, prediction_frame, predict
    from air_quality.processing.tables import overwrite_table
    namespace = "replay_ml_" + uuid4().hex[:10]
    spark.sql(f"CREATE NAMESPACE lake.{namespace}")
    gold = hourly(spark)
    overwrite_table(gold, f"lake.{namespace}.hourly")
    scored = feature_rows(gold).filter(F.col("period_end") == START + timedelta(hours=50)).withColumn("prediction", F.lit(52.))
    issued = (START + timedelta(days=10)).replace(tzinfo=timezone.utc)
    first = prediction_frame(scored, "synthetic-model", 1, "backtest", issued)
    merge_predictions(first, namespace)
    retry = first.withColumn("predicted_value", F.lit(999.)).withColumn("issued_at", F.lit(issued + timedelta(minutes=5)))
    merge_predictions(retry, namespace)
    rows = spark.table(f"lake.{namespace}.predictions").collect()
    assert len(rows) == 1 and rows[0].predicted_value == 52
    enrich_actuals(spark, namespace)
    before = spark.table(f"lake.{namespace}.forecast_actual").first()
    assert before.actual_value == 51 and before.error == 1
    corrected = gold.withColumn("value", F.when(F.col("period_end") == START + timedelta(hours=51), F.lit(60.)).otherwise(F.col("value")))
    overwrite_table(corrected, f"lake.{namespace}.hourly")
    enrich_actuals(spark, namespace)
    after = spark.table(f"lake.{namespace}.forecast_actual").first()
    assert after.predicted_value == 52 and after.actual_value == 60 and after.error == -8
    # Operational stale phải suppress trước khi load model. Path cố ý không
    # tồn tại để test bắt được mọi nhánh vô tình vẫn phát hành trên input cũ.
    manifest = {"namespace": namespace, "model_version": "synthetic-model", "trained_at": "2026-01-01T00:00:00+00:00",
                "stations": [{"sensor_id": 1, "path": "must-not-be-loaded"}]}
    (tmp_path / "latest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(module, "atomic_json", lambda *_: None)
    stale = predict(spark, namespace, tmp_path, issued)
    assert stale["stations"][0]["status"] == "stale_input_target_expired"
    assert spark.table(f"lake.{namespace}.predictions").filter("mode='operational'").count() == 0
    manifest["trained_at"] = "2026-02-01T00:00:00+00:00"
    (tmp_path / "latest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Model chưa tồn tại"):
        predict(spark, namespace, tmp_path, issued)
