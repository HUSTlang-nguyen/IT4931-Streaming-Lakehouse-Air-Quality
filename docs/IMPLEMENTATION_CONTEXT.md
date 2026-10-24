# Context triển khai hiện tại

## Checkpoint

- Cập nhật `2026-10-24T15:40:39+07:00`, đồng bộ STEP-007; Goal active `start goal implement`, phạm vi đầy đủ theo [GOAL_PROMPT](../GOAL_PROMPT.md).
- Git root repository con `IT4931-Streaming-Lakehouse-Air-Quality`, remote GitHub giữ nguyên; nhánh `feat/air-quality-lakehouse` từ `81ab9f2f0163a6cf600b1c56e66ae00a26d68faf`. Code Collector hiện chưa commit lúc ghi, đối chiếu git status khi tiếp tục.
- P0 xong; P1/P3 tiến triển; P2–P6 chưa hoàn thành.

## Đã code và đã kiểm chứng

- [Settings](../src/air_quality/config/settings.py): secret repr-hidden, explicit .env, sensors, defaults, input validation.
- [Events](../src/air_quality/contracts/events.py): UTC, fixed windows, envelope v1 với series_kind measurements/hours và provenance.
- Collector [HTTP](../src/air_quality/collector/openaq.py), [state SQLite](../src/air_quality/collector/state.py), [service](../src/air_quality/collector/service.py), [publishers](../src/air_quality/collector/publisher.py), [CLI](../src/air_quality/cli.py). Raw archive trước publish, checkpoint sau ACK, retry dùng lại archive, sink-specific job identity.
- 17 unit pass; 4 live contract pass, pip editable install và pip check sạch. XML ở artifacts/local, [báo cáo nhỏ](../artifacts/reports/collector-checkpoint.md).
- Lab 01/02 đã có code/lệnh thật cho API/JSONL; Kafka phần lab chưa được kiểm chứng. Chưa có Spark/ML/dashboard/Compose.

## Tiến trình đang sống cần kiểm tra trước khi thao tác

- Backfill `21843`: `.venv/Scripts/python.exe -m air_quality.cli backfill --end 2026-10-24T00:00:00Z --run-name hanoi-180d-20261024 --sink jsonl --output data/history-180d.jsonl`, stdout/stderr artifacts/local/backfill.log. Từ 2026-04-27 tới 2026-10-24, 4 sensor × raw/hours, job checkpoint trong checkpoints/collector.sqlite. Poll đúng handle hoặc xác minh PID; không restart vì timeout.
- Các session Docker 16316/15755/65016 và live test 64845 đã terminal.

## Dữ liệu / quyết định

Hai trạm và sensor theo dictionary. Poll 300s, overlap24h, reconcile7days/24h; ingest UTC/display Asia/Ho_Chi_Minh. Key ở .env local ignored, không đọc/in key khi chỉ kiểm tra trạng thái.

/hours là nguồn mean chính thức; live contract kiểm period1h/boundary/unique/parameter và lượng tử hóa3sig so summary.avg. Target ML/Gold sẽ là source-hourly series, không tự bình quân raw5phút. Raw interval vật lý vẫn chưa rõ, không tuyên bố resolved. Coverage nguồn>100% được giữ raw và không dùng trực tiếp. Khóa Silver phải gồm sensor_id, series_kind, period_start/end trong namespace; correction và DDL chi tiết chưa chốt.

RF từng trạm t+1h, lag1/2/3/24h theo giờ thật, train/validation/test70/15/15 chronological, không leakage, baseline cùng mẫu, backtest tách operational. Chưa có ML.

## Môi trường / Docker

Python host3.13.12, .venv editable với dependencies pin pyproject; chưa khóa Python/Java/Spark runtime. Docker28.4.0 đã chạy, 16CPU/~7,46GiB RAM engine, host~15,4GiB.

Người dùng đã cho phép sửa lỗi khởi động Docker ngoài repo. Đã dừng Desktop, sao lưu `%LOCALAPPDATA%/Docker/run` thành `run.before-air-quality-20261024` sau unlink/reparse delete lỗi1920, tạo lại run và start thành công. Không xóa backup, không sửa settings/volumes/images.

Đã xác minh tags Python3.11.13-slim-bookworm, Kafka3.9.1, iceberg-rest1.6.0, Trino476, Superset4.1.2, PostgreSQL16.9-bookworm qua registry; digest ở data/discovery/image-manifests.json. **MinIO DockerHub repo trả401, cần chọn image official registry khả dụng (Quay)**. Đây mới kiểm tag, chưa chứng minh tương thích runtime.

## Lệnh hiện có

- `.venv/Scripts/python.exe -m air_quality.cli --help` (inspect/backfill/live/replay). inspect default JSONL, không broker.
- `.venv/Scripts/python.exe -m pytest tests -q --basetemp=artifacts/local/<unique-dir>`: offline skips live; basetemp phải là chỗ test riêng vì pytest có thể dọn.
- Live: thêm --run-live, dùng chung limiter SQLite với backfill. Không --run-integration trừ khi stack đã sẵn sàng.
- Chưa có start/train/predict/benchmark.

## Bước tiếp theo cụ thể

1. Xác minh tag MinIO trên Quay, viết Compose project riêng (không ảnh hưởng n8n images hiện có), SQLite-persist REST catalog nếu driver phù hợp, PostgreSQL metadata Superset. Chốt/pin matrix sau chạy thật.
2. Giới hạn RAM tổng phù hợp8GiB Docker; start Kafka/MinIO/catalog/Trino và build Python3.11/Java17/Spark3.5.6, Iceberg1.9.2 + Kafka connector3.5.6 (dự kiến, chưa verify).
3. Cần cách publish archive đã tải qua Kafka giữ mode backfill (khác replay mode) để dùng dữ liệu đã thu mà không gọi lại API. Sau đó Bronze/Silver/Gold, ML/dashboard và P6.
4. Ghi coverage thực khi backfill xong; không lấy rows ACK lũy kế làm unique coverage. Viết/push checkpoint Collector, draft PR khi có implementation review được; chưa merge.

[Nhật ký](AGENT_WORK_LOG.md), [kế hoạch](../IMPLEMENTATION_PLAN.md), [kiến trúc](architecture.md), [dictionary](data-dictionary.md) là chỉ mục tiếp tục. Kiểm Git/process/file thực tế trước khi tin trạng thái Markdown.
