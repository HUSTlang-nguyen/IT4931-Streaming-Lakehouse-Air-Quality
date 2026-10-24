"""Features PM2.5 theo giờ thật, không dịch hàng qua khoảng thiếu.

Đầu vào là Gold /hours tại một Iceberg snapshot; đầu ra có current, lag1/2/3/24,
hour Việt Nam, thời điểm sẵn có muộn nhất của các input và target giờ kế tiếp.
Không impute: thiếu bất kỳ input bắt buộc nào thì mẫu không đủ điều kiện.
"""

from datetime import datetime, timedelta

from pyspark.sql import DataFrame, functions as F


FEATURES = ["current_value", "lag_1", "lag_2", "lag_3", "lag_24", "hour_of_day"]


def feature_rows(hourly: DataFrame, available_at: datetime | None = None) -> DataFrame:
    """Ghép exact timestamp; available_at chỉ bật cho forecast operational.

    Backtest dùng snapshot hiện tại, không giả nguồn đã có trong quá khứ.
    Operational loại observation thu sau issued_at trước khi tạo mọi lag.
    """
    valid = hourly.filter("parameter_name='pm25' AND has_data AND value IS NOT NULL")
    if available_at is not None:
        valid = valid.filter(F.col("ingested_at") <= F.lit(available_at))
    base = valid.select("sensor_id", "location_id", "station_name", "period_end",
                        F.col("value").alias("current_value"), F.col("ingested_at").alias("available_0"))
    for lag in (1, 2, 3, 24):
        # Dịch timestamp của bảng tra cứu về mốc hiện tại: t-lag + lag = t.
        # inner join chủ động loại gap, không lấy "hàng trước" cách đó nhiều giờ.
        previous = valid.select("sensor_id", (F.col("period_end") + F.expr(f"INTERVAL {lag} HOURS")).alias("period_end"),
                                F.col("value").alias(f"lag_{lag}"), F.col("ingested_at").alias(f"available_{lag}"))
        base = base.join(previous, ["sensor_id", "period_end"], "inner")
    return (base.withColumn("hour_of_day", F.hour(F.from_utc_timestamp("period_end", "Asia/Ho_Chi_Minh")).cast("double"))
            .withColumn("target_time", F.col("period_end") + F.expr("INTERVAL 1 HOUR"))
            .withColumn("inputs_available_at", F.greatest(*[F.col(f"available_{lag}") for lag in (0, 1, 2, 3, 24)]))
            .drop(*[f"available_{lag}" for lag in (0, 1, 2, 3, 24)]))


def labelled_rows(hourly: DataFrame) -> DataFrame:
    """Nhãn là source mean ở t+1h, tách hoàn toàn khỏi vector features."""
    targets = hourly.filter("parameter_name='pm25' AND has_data AND value IS NOT NULL").select(
        "sensor_id", F.col("period_end").alias("target_time"), F.col("value").alias("label"))
    return feature_rows(hourly).join(targets, ["sensor_id", "target_time"], "inner")


def split_bounds(first: datetime, last: datetime) -> tuple[datetime, datetime]:
    """Ranh giới 70/15/15 theo độ dài thời gian, làm tròn xuống giờ UTC."""
    hours = int((last - first).total_seconds() // 3600) + 1
    return first + timedelta(hours=int(hours * .70)), first + timedelta(hours=int(hours * .85))


def chronological_splits(frame: DataFrame, train_end: datetime, validation_end: datetime) -> dict[str, DataFrame]:
    """Purge nhãn vượt boundary; validation/test được dùng lag từ quá khứ.

    Mẫu t ngay trước boundary có target đúng boundary bị loại khỏi tập trước.
    Vì thế không có một nhãn huấn luyện thuộc khoảng validation/test.
    """
    return {
        "train": frame.filter((F.col("period_end") < F.lit(train_end)) & (F.col("target_time") < F.lit(train_end))),
        "validation": frame.filter((F.col("period_end") >= F.lit(train_end)) & (F.col("target_time") < F.lit(validation_end))),
        "test": frame.filter(F.col("period_end") >= F.lit(validation_end)),
    }
