# Data dictionary thực thi

## Registry

| Trạm | location_id | PM2.5 | PM10 |
|---|---:|---:|---:|
| ĐHBK | 4946813 | 13502154 | 13502152 |
| Công viên Nhân Chính | 4946812 | 13502151 | 13502153 |

PM `parameter_name` là pm25/pm10, đơn vị µg/m³. Metadata được kiểm lại qua API ngày 24/10/2026. Không có temperature/humidity/gas trong scope hiện tại.

## Bảng Iceberg namespace live

| Bảng | Khóa / trường quan trọng | Ý nghĩa |
|---|---|---|
| bronze | event_id; schema_version, job_id, ingest_mode, ingested_at, request_from/to, raw_payload, location_metadata, Kafka topic/partition/offset, original_ingested_at (replay) | Envelope v1, raw JSON strings giữ nguyên; partition ngày ingested_at |
| silver | sensor_id,series_kind,period_start,period_end; value,unit,quality_flags,ingested_at,provider,latitude,longitude | Trạng thái mới nhất của phép đo; partition tháng period_end |
| rejected | event_id + fields normalized | Thiếu period/sensor không tạo key; vẫn giữ Bronze |
| dead_letter | Kafka topic,partition,offset,message,reason | Sai envelope/schema/mode; replay vào live bị cách ly |
| hourly | sensor_id,period_end; value,has_data,quality_flags,ingested_at,observed_count,period_start,unit | Grid giờ với mean nguồn /hours, null khi thiếu/invalid; partition tháng |
| daily | sensor_id,local_date; mean_value,valid_hours,expected_hours=24,window_bins,coverage_percent | Mean giờ hợp lệ theo UTC+7, ngày biên có thể chưa đủ24 giờ |
| freshness | sensor_id,series_kind; last_measurement_at,last_ingested_at,records,valid_records | Độ mới từng sensor/resource, không suy từ trạm |
| predictions | model_version,sensor_id,target_time,mode; input_time,issued_at,inputs_available_at,predicted_value,baseline_value,unit,source_snapshot,stale_input | Giữ forecast đầu tiên mỗi key, không thay bằng lần phát hành muộn hơn |
| forecast_actual | predictions + actual_value,error | Materialize join actual Gold hiện tại mỗi predict; actual chưa có null, error=predicted-actual |
| model_metrics | model_version,sensor_id,algorithm; n,mae,rmse,source_snapshot | Test RF/Persistence cùng mẫu; metrics snapshot cố định khác actual có thể sửa sau |

Mọi timestamp lưu UTC; local_date là date Việt Nam. `period_end` của /hours tròn giờ, period dài3600 giây đã qua live contract bốn sensor; value nguồn có lượng tử hóa3 chữ số có nghĩa. Không diễn giải mean này như số đo tức thời. observed_count giữ nguồn để truy vết, không dùng metadata percentCoverage>100% làm độ phủ phân tích.

## Quality và correction

Flags gồm invalid_value (null/NaN/inf/âm), unexpected_unit, invalid_period, source_flagged, metadata_mismatch, unknown_series, invalid_ingested_at. Hai ký tự micro được chuẩn hóa, không tự đổi mg/m³. Bản invalid có key vẫn ở Silver nhưng loại khỏi Gold bằng null. Correction mới hơn có thể thay valid thành invalid, Gold được tính lại để bỏ giá trị cũ.

Newest ingested_at thắng cùng Silver key, event_id tie-break ổn định. Bronze event_id là lần quan sát logic bất biến; thu lại payload sau đó có thể thêm Bronze nhưng không thêm Silver key. Replay topic/namespace riêng, không trộn live/ML metrics.

## ML features, split và coverage

Current PM2.5, lag1/2/3/24 giờ theo timestamp, hour_of_day UTC+7. Target=current timestamp+1h; label chỉ join để train/evaluate. Không impute. Split theo thời gian 70/15/15, purge target chạm boundary; counts có thể khác tỷ lệ do gaps. MAE/RMSE tính cùng mẫu cho RF/persistence; không yêu cầu RF thắng.

Operational input phải thu trước issued_at, target chưa hết hạn; input quá90 phút hoặc target đã qua bị suppress. Backtest issued_at là lúc chạy đánh giá hôm nay, mode=backtest, không giả issue timestamp lịch sử. manifest chứa model path, version/config/seed/splits/data snapshot/code provenance. Model binaries ở volume ignored.

Source coverage: số hourly bins có /hours hợp lệ trên số bins lịch sử, không phải độ chính xác cảm biến. Daily coverage=valid_hours/24, luôn trình bày ngày biên/hiện tại chưa đầy đủ. Khoảng thiếu dài nhất là timestamp gap87h, tương ứng86 bins giữa hai điểm hợp lệ.
