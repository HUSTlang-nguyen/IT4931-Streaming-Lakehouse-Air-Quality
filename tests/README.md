# Kiểm thử

Unit Collector/coverage/archive/operations chạy offline trên host. `air-quality test` chỉ chạy unit; `test --live` thêm4 API hourly contracts với key local. Live đã chạy riêng, không lặp API khi chỉ sửa docs.

`test --integration` chạy unit host rồi Spark container tests/integration với --run-integration; OpenAQ live tests skip nếu không --run-live. Processor phải dừng trước để dành RAM; core/Kafka/MinIO/catalog/Trino vẫn chạy. Không coi skip vì thiếu pyspark host là Spark pass.

[test_lakehouse.py](integration/test_lakehouse.py): duplicate/correction-old-new, late fills gap/daily, invalid correction removes Gold, missing-key quarantine, UTC/unit, replay vào live bị deadletter. [test_forecasting.py](integration/test_forecasting.py): exact lags/gaps, labels, availability, split purge, metrics cùng mẫu, forecast retry và actual correction. Mỗi fixture có namespace replay_test/replay_ml riêng, không dùng làm số đo thật.

Logs/JUnit ở artifacts/local ignored. Basetemp riêng mỗi lần; pytest có thể dọn thư mục này, không dùng đường dẫn data. Restart thật ở reports/restart-persistence.json; E2E thực trong reconciliation và dashboard screenshot, không suy ra từ unit tests.
