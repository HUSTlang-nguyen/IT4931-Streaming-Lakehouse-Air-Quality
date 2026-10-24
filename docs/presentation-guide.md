# Sáu đoạn code thật cho thuyết trình

Sinh bằng `scripts/export_presentation_snippets.py`; chạy lại sau thay đổi source. Mỗi đoạn10–25 dòng nguyên bản, lời dẫn khoảng30–60 giây. Hash là SHA256 cả source file, không giả hash commit chứa chính tài liệu. Chỉ trình bày kết quả kiểm chứng trong reports; không tự sửa slide cũ.

## 1. Crawl và lưu trang trước ACK

Source: [collect_window](../src/air_quality/collector/service.py#L87), bắt đầu dòng87. SHA256 `03629d016a887e3020bf665eaf0ede1735541ced401f5a473eaa21592861d444`.

Input: sensor/khoảng UTC/trang; output: raw archive và envelope có provenance.

```python
            while not done:
                archive = self.settings.data_dir / "raw" / job_id / f"page-{page:06d}.json"
                if archive.exists():
                    envelope = json.loads(archive.read_text(encoding="utf-8"))
                else:
                    response = self.client.get(f"sensors/{sensor.sensor_id}/{resource}", {
                        "datetime_from": iso_utc(start), "datetime_to": iso_utc(end),
                        "limit": self.settings.page_size, "page": page,
                    })
                    observed_at = datetime.now(timezone.utc)
                    events = [make_event(sensor, resource, row, metadata, job_id, page, index,
                                         observed_at, self.settings.ingest_mode, start, end)
                              for index, row in enumerate(response["results"])]
                    envelope = {"meta": response.get("meta", {}), "events": events}
                    atomic_json(archive, envelope)
                events = envelope["events"]
                page_hash = stable_hash([event["raw_payload"] for event in events])
                if events and page_hash == previous_hash:
                    raise RuntimeError(f"OpenAQ lặp trang {page}; không tăng checkpoint để tránh vòng lặp")
                previous_hash = page_hash
                acknowledged = self.publisher.publish(events) if events else 0
                if acknowledged != len(events):
```

Lời dẫn: Một khoảng thời gian có thể có nhiều trang API. Code giữ từng trang thành archive bất biến trước khi gửi Kafka. Khi process chết, lần tiếp đọc lại chính archive để giữ event ID và thời điểm thu. Chỉ ACK đủ trang mới tăng checkpoint; downstream MERGE xử lý trường hợp broker đã nhận nhưng checkpoint chưa ghi. Đây là cơ chế tránh mất trang, không phải giả định mạng luôn thành công. Test crash-before-ACK và source reconciliation cung cấp bằng chứng.

## 2. Chuẩn hóa measurement

Source: [normalize](../src/air_quality/processing/transforms.py#L54), bắt đầu dòng54. SHA256 `2a1d33cec6d8aba1d8ecfe2e80eb4e9564a820ab62b372d51811291270fb9bd1`.

Input: envelope raw JSON; output: period UTC/value/unit/provider và flags trong Silver.

```python
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
```

Lời dẫn: Một dòng chỉ đo một chỉ số của một sensor. Code parse hai đầu khoảng đo, giữ interval nguồn và metadata liên kết ID. Chỉ chuẩn hóa hai ký tự micro giống nghĩa, không tự đổi mg sang microgram. Các điều kiện phía dưới gắn flags cho giá trị âm, sai unit, sai khoảng hoặc metadata. Bản invalid còn raw để truy vết, Gold giữ null thay vì zero; đây là cách tránh đồ thị nhìn đẹp nhưng sai dữ liệu.

## 3. MERGE chống trùng và correction

Source: [merge_silver](../src/air_quality/processing/tables.py#L57), bắt đầu dòng57. SHA256 `d1eb4fbfe893bbafb6a30c4cc63c7416d05c0d4d30012e5d50361099a2e48ead`.

Input: normalized rows; output: một hàng mỗi sensor/series/khoảng đo.

```python
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
```

Lời dẫn: Khóa Silver gồm sensor, series_kind và cả đầu/cuối khoảng đo. Raw và hours không bị gộp nhầm. Trong batch chọn observation mới nhất, sau đó MERGE chỉ cho observation mới hơn sửa hàng hiện có; event_id là tie-break xác định. Chạy lại cùng trang không nhân đôi khóa, observation cũ không ghi đè correction. Tests gửi original, correction và original lần nữa; count vẫn một và giá trị cuối đúng correction.

## 4. Dữ liệu đến muộn và Gold

Source: [refresh_gold](../src/air_quality/processing/tables.py#L77), bắt đầu dòng77. SHA256 `d1eb4fbfe893bbafb6a30c4cc63c7416d05c0d4d30012e5d50361099a2e48ead`.

Input: Silver sau MERGE; output: snapshots hourly/daily/freshness mới.

```python
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
```

Lời dẫn: Watermark không dùng để bỏ vĩnh viễn số đo cũ. Late record đi vào Silver như các bản khác rồi Gold được tính lại. Với hai trạm, full refresh đơn giản và dễ kiểm hơn incremental phức tạp. Overwrite commit một snapshot từng bảng, tránh lộ bảng rỗng. Nếu crash sau Silver trước Gold, Kafka checkpoint chưa tiến nên batch retry phục hồi. Test gap ở giờ2 rồi nhận giờ2 muộn chứng minh null được lấp và daily count/mean cập nhật.

## 5. Features causal theo giờ thật

Source: [feature_rows](../src/air_quality/forecasting/features.py#L22), bắt đầu dòng22. SHA256 `5cfa43ccbeda7c0ca9d35cb90fbc750bd6aa8c5d162dc04e985e29e494e0078e`.

Input: Gold snapshot PM2.5; output: current/lag1/2/3/24/hour và max availability.

```python
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
```

Lời dẫn: Lag một giờ phải là số đo đúng timestamp t trừ một giờ. Code dịch timestamp bảng tra cứu rồi inner join, không dùng hàng trước trong file. Thiếu một giờ thì mẫu bị loại thay vì kéo một số đo cách xa làm lag. Operational còn lọc ingested_at trước issued_at cho mọi input. Nhãn giờ kế tiếp được join ở hàm riêng và không có trong vector. Test có gap và input đến muộn kiểm hai ranh giới này; split purge loại target chạm validation/test.

## 6. Đánh giá RF và persistence cùng mẫu

Source: [regression_metrics](../src/air_quality/forecasting/model.py#L28), bắt đầu dòng28. SHA256 `c85f3775646e4749c033ab9e4fc66ffb5226648d51aa8908036f4aac44e12c85`.

Input: cùng scored test rows, cột prediction hoặc current_value; output: n/MAE/RMSE.

```python
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
```

Lời dẫn: MAE là trung bình trị tuyệt đối sai số, RMSE nhạy hơn với sai số lớn. Helper tính cả count để chứng minh RF và persistence được đo cùng số mẫu. Trong train, model chỉ fit train, depth được chọn bằng validation; helper này đánh giá test sau khi đã chọn. Kết quả thật RF chưa thắng persistence nhất quán: ĐHBK MAE gần nhau nhưng RMSE RF cao hơn, Nhân Chính baseline tốt hơn. Backtest snapshot không chứng minh forecast đã phát hành trong quá khứ.

## Bằng chứng đi cùng

[Collector](../tests/unit/test_collector.py), [Spark quality](../tests/integration/test_lakehouse.py), [ML leakage/retry](../tests/integration/test_forecasting.py), [source coverage](../artifacts/reports/source-coverage.json), [reconciliation](../artifacts/reports/lakehouse-history-reconciliation.json), [restart](../artifacts/reports/restart-persistence.json), [ML metrics](../artifacts/reports/ml-evaluation.json), [Iceberg experiment](../artifacts/reports/iceberg-benchmark.json).
