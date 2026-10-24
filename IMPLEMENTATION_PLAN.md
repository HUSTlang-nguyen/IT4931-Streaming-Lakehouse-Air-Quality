# Kế hoạch triển khai và nghiệm thu

Trạng thái: chuẩn bị repository, chưa triển khai nghiệp vụ. [Prompt độc lập](GOAL_PROMPT.md) quy định Goal khi người dùng bắt đầu; [context](docs/IMPLEMENTATION_CONTEXT.md) ghi trạng thái thực tế.

## P0 — Scaffold (lượt chuẩn bị)

- [x] Dùng repository/remote có sẵn, tạo nhánh `chore/project-scaffold`.
- [x] Khung Python, README trách nhiệm và template cấu hình.
- [x] Prompt, quy tắc agent, context, nhật ký, tài liệu lab/thuyết trình.
- [x] Sao chép đề xuất, đồng bộ ML; giữ nguyên bản gốc bên ngoài.
- [x] Kiểm tra package, links, secret, diff và lưu bằng chứng trong `artifacts/reports/scaffold-verification.md`.
- [ ] Commit và push nhánh scaffold; không tạo PR.

## P1 — Khảo sát và hợp đồng dữ liệu

- [ ] Kiểm tra Docker, RAM/disk, lab, quyền API và tài liệu chính thức.
- [ ] Xác minh sensor, timestamp/khoảng đo và lịch sử; lưu mẫu đã làm sạch.
- [ ] Chốt ma trận Python/Java/Spark/Kafka connector/Iceberg/Trino, image version và dependency lock sau khi thử tương thích.
- [ ] Chốt schema, đơn vị, khóa dedup, quy tắc correction và tổng hợp.
- [ ] Có bằng chứng phương pháp tạo chuỗi giờ ML; nếu khoảng đo chưa rõ, ghi blocker và tiếp tục phần độc lập.

## P2 — Hạ tầng và vận hành

- [ ] Docker Compose: Kafka, Spark, Iceberg REST catalog, MinIO, Trino, Superset và PostgreSQL theo nhu cầu metadata.
- [ ] Health checks/lưu bền vững; Spark và Trino cùng đọc một bảng Iceberg.
- [ ] Python CLI và PowerShell guide cho start/stop/status/backfill/live/replay/train/predict/test/benchmark; tên lệnh chốt khi triển khai.
- [ ] Env example, dependency lock, hướng dẫn cấu hình và lab hạ tầng đã được kiểm chứng.

## P3 — Thu thập

- [ ] Metadata/measurements: pagination, timeout, rate limit, Retry-After, bounded retry/backoff.
- [ ] Backfill 180 ngày cố định mốc đầu/cuối, checkpoint/resume, báo cáo ngày thiếu thực tế.
- [ ] Live 5 phút/lần, overlap 24 giờ; đối soát 7 ngày mỗi ngày; cấu hình được.
- [ ] Replay namespace riêng; Kafka event giữ provenance và định danh.

## P4 — Bronze / Silver / Gold

- [ ] Bronze lưu gốc, metadata, ingested_at và ingest mode.
- [ ] Silver UTC/đơn vị, MERGE theo sensor/khoảng đo; xử lý nguồn sửa đổi nhất quán.
- [ ] Late data vượt watermark, gap, invalid data và restart được kiểm chứng; không điền thiếu bằng 0.
- [ ] Gold coverage/freshness theo sensor; chỉ tổng hợp khi khoảng đo có bằng chứng.

## P5 — Dashboard và ML

- [ ] Superset: PM2.5/PM10, so sánh trạm, gap, freshness, forecast/actual; export tái lập được.
- [ ] Random Forest Spark MLlib từng trạm; target PM2.5 t+1 giờ; current, lag 1/2/3/24 giờ, hour-of-day theo mốc thời gian thực.
- [ ] Train/validation/test 70/15/15 theo thời gian, loại nhãn vượt ranh giới; không leakage hoặc tune trên test.
- [ ] MAE/RMSE và persistence trên cùng mẫu; lưu số mẫu, thời gian, snapshot, seed/config/model version.
- [ ] Forecast issued_at/target_time; phân biệt backtest/operational; không yêu cầu thắng baseline.

## P6 — Kiểm chứng và bàn giao

- [ ] Unit/integration: pagination, retry, duplicate, correction, late data, gap, timezone, restart và leakage.
- [ ] Đường đi thật OpenAQ → Kafka → Iceberg → Trino → dashboard; fixture được phân biệt.
- [ ] Coverage report backfill, ngày thiếu thực tế; không dùng số ước lượng thay dữ liệu đã tải.
- [ ] Partition pruning có query plan/scan evidence; compaction có file count/size và kết quả query; time travel đối chiếu snapshot.
- [ ] Benchmark ghi commit/dataset/config/lệnh/số lần đo/giới hạn; dữ liệu nhân bản tách riêng, không cam kết tăng tốc ở quy mô nhỏ.
- [ ] Labs gọi code thật và đã chạy; walkthrough và 6 đoạn code thuyết trình khớp phiên bản cuối.
- [ ] README, context/log, draft PR và demo hoàn chỉnh.

## Quy tắc hoàn thành

Chỉ hoàn thành Goal khi P1–P6 có bằng chứng. Thiếu key/API, semantic khoảng đo chưa rõ hoặc dữ liệu ML không đủ là blocker của tiêu chí liên quan; tiếp tục phần độc lập. Scaffold, fixture pass hoặc budget cạn không đồng nghĩa hoàn thành hệ thống.
