# Context triển khai hiện tại

## Checkpoint

- Cập nhật `2026-10-24T15:53:08+07:00`, đồng bộ STEP-010; Goal active `start goal implement`, phạm vi đầy đủ theo [GOAL_PROMPT](../GOAL_PROMPT.md).
- Git root repository con `IT4931-Streaming-Lakehouse-Air-Quality`, remote GitHub giữ nguyên; nhánh `feat/air-quality-lakehouse` từ `81ab9f2f0163a6cf600b1c56e66ae00a26d68faf`. Collector checkpoint `301ab9ebb934ff4ff6644c6f92adb43ac40880ad` đã commit/push, draft PR #1 đã attach. Profiler và MinIO build đã kiểm chứng ở mức mô tả bên dưới, đang ghi checkpoint tiếp; đối chiếu git status khi tiếp tục.
- P0 xong; P1/P3 tiến triển; P2–P6 chưa hoàn thành.

## Đã code và đã kiểm chứng

- [Settings](../src/air_quality/config/settings.py): secret repr-hidden, explicit .env, sensors, defaults, input validation.
- [Events](../src/air_quality/contracts/events.py): UTC, fixed windows, envelope v1 với series_kind measurements/hours và provenance.
- Collector [HTTP](../src/air_quality/collector/openaq.py), [state SQLite](../src/air_quality/collector/state.py), [service](../src/air_quality/collector/service.py), [publishers](../src/air_quality/collector/publisher.py), [CLI](../src/air_quality/cli.py). Raw archive trước publish, checkpoint sau ACK, retry dùng lại archive, sink-specific job identity.
- 21 unit pass (Collector+coverage); 4 live contract pass, pip editable install và pip check sạch. XML ở artifacts/local, [báo cáo nhỏ](../artifacts/reports/collector-checkpoint.md).
- Lab 01/02 đã có code/lệnh thật cho API/JSONL; Kafka phần lab chưa được kiểm chứng. Chưa có Spark/ML/dashboard/Compose.

## Tiến trình / artifact cần kiểm tra trước khi thao tác

- **Không còn tiến trình dài đang chạy ở checkpoint này.** MinIO build69048 exit0; pinned rebuild exit0; image air-quality-minio:2025-10-15 đã chạy --version và xác nhận LICENSE. Log artifacts/local/minio-build*.log. S3/health/catalog chưa kiểm chứng; xem báo cáo minio-source-build.md.
- Backfill21843 và profiler67325 đã exit0. Full source JSONL `data/history-180d.jsonl`, raw page archive `data/raw/`, SQLite `checkpoints/collector.sqlite` đều ignored. Run hanoi-180d-20261024 cố định 2026-04-27..2026-10-24 UTC.
- [Coverage](../artifacts/reports/source-coverage.json): **202.041 records unique** gồm raw+hours bốn sensor; [báo cáo](../artifacts/reports/backfill-180d.md). Hour bins: PM2.5 ĐHBK3957, Nhân Chính4042; PM10 ĐHBK4060, Nhân Chính4037 /4320 expected. Gap hourly87h. Không nhầm với Silver count hay accuracy.
- Các session Docker cũ và live test đều terminal. PR draft https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/1; chưa merge.

## Dữ liệu / quyết định

Hai trạm và sensor theo dictionary. Poll 300s, overlap24h, reconcile7days/24h; ingest UTC/display Asia/Ho_Chi_Minh. Key ở .env local ignored, không đọc/in key khi chỉ kiểm tra trạng thái.

/hours là nguồn mean chính thức; live contract kiểm period1h/boundary/unique/parameter và lượng tử hóa3sig so summary.avg. Target ML/Gold sẽ là source-hourly series, không tự bình quân raw5phút. Raw interval vật lý vẫn chưa rõ, không tuyên bố resolved. Coverage nguồn>100% được giữ raw và không dùng trực tiếp. Khóa Silver phải gồm sensor_id, series_kind, period_start/end trong namespace; correction và DDL chi tiết chưa chốt.

RF từng trạm t+1h, lag1/2/3/24h theo giờ thật, train/validation/test70/15/15 chronological, không leakage, baseline cùng mẫu, backtest tách operational. Chưa có ML.

## Môi trường / Docker

Python host3.13.12, .venv editable với dependencies pin pyproject; chưa khóa Python/Java/Spark runtime. Docker28.4.0 đã chạy, 16CPU/~7,46GiB RAM engine, host~15,4GiB.

Người dùng đã cho phép sửa lỗi khởi động Docker ngoài repo. Đã dừng Desktop, sao lưu `%LOCALAPPDATA%/Docker/run` thành `run.before-air-quality-20261024` sau unlink/reparse delete lỗi1920, tạo lại run và start thành công. Không xóa backup, không sửa settings/volumes/images.

Đã xác minh tags Python3.11.13-slim-bookworm, Kafka3.9.1, iceberg-rest1.6.0, Trino476, Superset4.1.2, PostgreSQL16.9-bookworm qua registry; digest ở data/discovery/image-manifests.json. **MinIO DockerHub và Quay tag thử trả401; đã chọn build source release chính thức** pin commit9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a, Go1.24.9, LICENSE giữ trong image. Build69048 đã exit0, binary Go1.24.9 chạy được; S3 compatibility chưa kiểm chứng. Tags khác mới được kiểm tra registry, chưa chứng minh runtime tương thích.

## Lệnh hiện có

- `.venv/Scripts/python.exe -m air_quality.cli --help` (inspect/backfill/live/replay). inspect default JSONL, không broker.
- `.venv/Scripts/python.exe -m pytest tests -q --basetemp=artifacts/local/<unique-dir>`: offline skips live; basetemp phải là chỗ test riêng vì pytest có thể dọn.
- Live: thêm --run-live, dùng chung limiter SQLite với backfill. Không --run-integration trừ khi stack đã sẵn sàng.
- Có thêm CLI profile offline; chưa có start/train/predict/benchmark.

## Bước tiếp theo cụ thể

1. MinIO image đã build/version verified; kiểm S3/health qua Compose. Viết Compose project riêng, SQLite-persist REST catalog nếu driver phù hợp, PostgreSQL metadata Superset. Chốt/pin matrix sau chạy thật.
2. Giới hạn RAM tổng phù hợp8GiB Docker; start Kafka/MinIO/catalog/Trino và build Python3.11/Java17/Spark3.5.6, Iceberg1.9.2 + Kafka connector3.5.6 (dự kiến, chưa verify).
3. Cần cách publish archive đã tải qua Kafka giữ mode backfill (khác replay mode) để dùng dữ liệu đã thu mà không gọi lại API. Sau đó Bronze/Silver/Gold, ML/dashboard và P6.
4. Coverage nguồn đã xong, cần đối chiếu Silver sau ingest. Commit/push profiler+docs và tiếp tục cập nhật draft PR #1, không merge. Ghi kết quả build thực trước khi claim runtime.

[Nhật ký](AGENT_WORK_LOG.md), [kế hoạch](../IMPLEMENTATION_PLAN.md), [kiến trúc](architecture.md), [dictionary](data-dictionary.md) là chỉ mục tiếp tục. Kiểm Git/process/file thực tế trước khi tin trạng thái Markdown.
