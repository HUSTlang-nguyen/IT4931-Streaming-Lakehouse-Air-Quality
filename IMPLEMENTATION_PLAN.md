# Kế hoạch triển khai và nghiệm thu

Trạng thái: các lát cắt pipeline, dashboard, ML và thực nghiệm đã chạy; các tiêu chí đã có bằng chứng, bàn giao trong draft PR#2. [Prompt độc lập](GOAL_PROMPT.md) quy định Goal khi người dùng bắt đầu; [context](docs/IMPLEMENTATION_CONTEXT.md) ghi trạng thái thực tế.

## P0 — Scaffold (lượt chuẩn bị)

- [x] Dùng repository/remote có sẵn, tạo nhánh `chore/project-scaffold`.
- [x] Khung Python, README trách nhiệm và template cấu hình.
- [x] Prompt, quy tắc agent, context, nhật ký, tài liệu lab/thuyết trình.
- [x] Sao chép đề xuất, đồng bộ ML; giữ nguyên bản gốc bên ngoài.
- [x] Kiểm tra package, links, secret, diff và lưu bằng chứng trong `artifacts/reports/scaffold-verification.md`.
- [x] Commit và push nhánh scaffold; checkpoint ở STEP-004, không tạo PR.

## P1 — Khảo sát và hợp đồng dữ liệu

- [x] Kiểm tra Docker, RAM/disk, lab, quyền API và tài liệu chính thức.
- [x] Xác minh sensor, timestamp/khoảng đo và lịch sử; lưu mẫu đã làm sạch.
- [x] Chốt ma trận Python/Java/Spark/Kafka connector/Iceberg/Trino, image version và dependency lock sau khi thử tương thích.
- [x] Chốt schema, đơn vị, khóa dedup, quy tắc correction và tổng hợp.
- [x] Có bằng chứng phương pháp tạo chuỗi giờ ML; nếu khoảng đo chưa rõ, ghi blocker và tiếp tục phần độc lập.

## P2 — Hạ tầng và vận hành

- [x] Docker Compose: Kafka, Spark, Iceberg REST catalog, MinIO, Trino, Superset và PostgreSQL theo nhu cầu metadata.
- [x] Health checks/lưu bền vững; Spark và Trino cùng đọc một bảng Iceberg.
- [x] Python CLI và PowerShell guide cho start/stop/status/backfill/live/replay/train/predict/test/benchmark; tên lệnh chốt khi triển khai.
- [x] Env example, dependency lock, hướng dẫn cấu hình và lab hạ tầng đã được kiểm chứng.

## P3 — Thu thập

- [x] Metadata/measurements: pagination, timeout, rate limit, Retry-After, bounded retry/backoff.
- [x] Backfill nguồn 180 ngày cố định, checkpoint/resume và source coverage (202.041 unique records); đã đối chiếu E2E tại snapshots trong báo cáo.
- [x] Live 5 phút/lần, overlap 24 giờ; đối soát 7 ngày mỗi ngày; cấu hình được.
- [x] Replay namespace riêng; Kafka event giữ provenance và định danh.

## P4 — Bronze / Silver / Gold

- [x] Bronze lưu gốc, metadata, ingested_at và ingest mode.
- [x] Silver UTC/đơn vị, MERGE theo sensor/khoảng đo; xử lý nguồn sửa đổi nhất quán.
- [x] Late data vượt watermark, gap, invalid data và restart được kiểm chứng; không điền thiếu bằng 0.
- [x] Gold coverage/freshness theo sensor; chỉ tổng hợp khi khoảng đo có bằng chứng.

## P5 — Dashboard và ML

- [x] Superset: PM2.5/PM10, so sánh trạm, gap, freshness, forecast/actual; export tái lập được.
- [x] Random Forest Spark MLlib từng trạm; target PM2.5 t+1 giờ; current, lag 1/2/3/24 giờ, hour-of-day theo mốc thời gian thực.
- [x] Train/validation/test 70/15/15 theo thời gian, loại nhãn vượt ranh giới; không leakage hoặc tune trên test.
- [x] MAE/RMSE và persistence trên cùng mẫu; lưu số mẫu, thời gian, snapshot, seed/config/model version.
- [x] Forecast issued_at/target_time; phân biệt backtest/operational; không yêu cầu thắng baseline.

## P6 — Kiểm chứng và bàn giao

- [x] Unit/integration: pagination, retry, duplicate, correction, late data, gap, timezone, restart và leakage.
- [x] Đường đi thật OpenAQ → Kafka → Iceberg → Trino → dashboard; fixture được phân biệt.
- [x] Coverage report backfill, ngày thiếu thực tế; không dùng số ước lượng thay dữ liệu đã tải.
- [x] Partition pruning có query plan/scan evidence; compaction có file count/size và kết quả query; time travel đối chiếu snapshot.
- [x] Benchmark ghi commit/dataset/config/lệnh/số lần đo/giới hạn; dữ liệu nhân bản tách riêng, không cam kết tăng tốc ở quy mô nhỏ.
- [x] Labs gọi code thật và đã chạy; walkthrough và 6 đoạn code thuyết trình khớp phiên bản cuối.
- [x] README, context/log, draft PR#2 và demo hoàn chỉnh; không merge PR.

## Quy tắc hoàn thành

Chỉ hoàn thành Goal khi P1–P6 có bằng chứng. Thiếu key/API, semantic khoảng đo chưa rõ hoặc dữ liệu ML không đủ là blocker của tiêu chí liên quan; tiếp tục phần độc lập. Scaffold, fixture pass hoặc budget cạn không đồng nghĩa hoàn thành hệ thống.
