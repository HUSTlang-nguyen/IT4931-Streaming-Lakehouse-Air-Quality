# Lab 06 — Random Forest PM2.5 t+1h và persistence

## Mục tiêu và điều kiện

Cần Gold `/hours` thật, Docker core hoạt động, runtime Spark có NumPy và đủ model_data volume. Model mỗi trạm riêng. Dừng processor trước job Spark nặng trên máy8GiB, Collector có thể tiếp tục ghi Kafka. Khởi động processor lại sau job. Lần train đã đo khoảng một phút; phụ thuộc máy và dữ liệu.

```text
Gold snapshot → timestamp self joins → label+1h → split/purge
→ train RF → chọn bằng validation → test RF/persistence → model + metrics
→ predict khi input đủ mới → predictions → actual enrichment → Superset
```

## Kiến thức tối thiểu và code thật

- [feature_rows/labelled_rows](../src/air_quality/forecasting/features.py): current, lag1/2/3/24, giờVN; `t=26` thiếu `t=25` thì không lấy hàng24 thay thế lag1. Inner joins loại mẫu thiếu, không nội suy.
- `chronological_splits`: 70/15/15 theo khoảng thời gian, label t+1 chạm boundary bị purge. Validation/test được dùng lag quá khứ, không dùng tương lai. Counts không đúng tỷ lệ hàng vì gaps.
- [train/regression_metrics](../src/air_quality/forecasting/model.py): VectorAssembler error on invalid, RF30 trees seed42, thử depth5/8, fit train và chọn RMSE validation. Không refit/test tuning. Không scaler/imputer cần fit.
- [predict/merge_predictions/enrich_actuals](../src/air_quality/forecasting/model.py): input ingested trước issue, model tồn tại trước issue, target còn tương lai; stale/thiếu thì suppress. Forecast đầu tiên giữ nguyên khi retry, actual cập nhật từ Gold sau đó.

## Chạy

```powershell
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop processor
.venv/Scripts/python.exe -m air_quality.cli train
.venv/Scripts/python.exe -m air_quality.cli predict
.venv/Scripts/python.exe -m air_quality.cli query "SELECT station_name,algorithm,n,mae,rmse FROM iceberg.live.model_metrics"
.venv/Scripts/python.exe -m air_quality.cli dashboard
.venv/Scripts/python.exe -m air_quality.cli start --services processor --no-build
```

Train pin Gold snapshot, version hash(snapshot/config), lưu model binary vào volume, manifest immutable và latest.json. Chạy lại cùng snapshot/config dùng lại manifest/model. `predict` phát hành theo lần gọi; cần gọi sau giờ mới để có operational forecast mới, không có scheduler nền mặc định. Không force train để có metric đẹp hơn.

## Kết quả đã chạy

[ml-evaluation.json](../artifacts/reports/ml-evaluation.json): snapshot5061425689190597954, version rf-f0077526710fd81e. ĐHBK train/validation/test2317/513/555; Nhân Chính2559/648/649. Depth8 được chọn bằng validation.

| Trạm | Test n | RF MAE / RMSE | Persistence MAE / RMSE |
|---|---:|---:|---:|
| ĐHBK | 555 | 11,394 / 16,664 | 11,747 / 15,097 |
| Nhân Chính | 649 | 6,781 / 9,421 | 5,728 / 7,283 |

Đơn vị µg/m³. RF chưa thắng baseline nhất quán. Các metric trên là hồi cứu snapshot hiện tại trên những hàng đủ toàn bộ features; không đánh giá các giờ thiếu hoặc chứng minh forecast operational quá khứ. Backtest issued_at là ngày chạy thật, mode backtest; không giả thời điểm phát hành lịch sử.

## Kiểm chứng và lỗi

[Test ML](../tests/integration/test_forecasting.py) gọi production transforms: gap đúng timestamp, label không trong features, mọi lag có trước issue, purge boundary, metrics cùng mẫu, forecast retry giữ giá trị đầu và actual correction cập nhật sai số.

```powershell
# Processor đang paused, core vẫn chạy.
.venv/Scripts/python.exe -m air_quality.cli test --integration
```

- Missing features/stale target: kiểm freshness nguồn /hours; chờ Collector/processor nhận giờ mới rồi gọi predict, không đổi issue về quá khứ.
- FileNotFound latest.json: train chưa thành công hoặc model volume chưa mount; đọc train log, không tạo model giả.
- Container exit137: thiếu RAM, dừng processor trước job; không xóa data/model để chữa lỗi.
- RF kém persistence: báo đúng metric và sample selection; không tune trên tập test để ép thắng.

Bài tập: bỏ một giờ trong fixture và dự đoán các mốc mất lag1/2/3/24, chạy test đối chiếu; giải thích vì sao baseline cũng phải dùng cùng hàng RF.
