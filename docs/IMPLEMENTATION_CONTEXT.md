# Context triển khai hiện tại

## Checkpoint để tiếp tục

- Loại công việc hiện tại: chỉ scaffold/tài liệu, chưa tạo Goal.
- Cập nhật: `2026-10-24T11:11:40+07:00`. STEP đã đồng bộ: `STEP-003`.
- Git root: repository `IT4931-Streaming-Lakehouse-Air-Quality` (thư mục con workspace ban đầu); không init Git ở thư mục cha.
- Remote: `https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality.git`.
- Nhánh hiện tại: `chore/project-scaffold`; commit nền `f64e464c04310d0d97ebe60bada7139096875458`.
- Các file scaffold đang chưa commit tại thời điểm checkpoint này; cần kiểm tra `git status` khi tiếp tục, không coi ghi chú này là trạng thái Git live.
- Bước tiếp theo ngay: commit và push scaffold; ghi hash/remote checkpoint ở STEP-004, chưa tạo PR.

## Yêu cầu được chốt

Docker local, Python/PySpark/Spark MLlib, pytest; PM2.5/PM10 hai trạm, backfill 180 ngày, polling 300 giây, overlap 24 giờ, đối soát 7 ngày mỗi 24 giờ. Thời gian lưu UTC, hiển thị Asia/Ho_Chi_Minh. RF từng trạm dự báo PM2.5 trước một giờ, persistence, MAE/RMSE, split thời gian 70/15/15. Không AQI/khuyến cáo sức khỏe/đại diện toàn Hà Nội.

Code tên tiếng Anh, type hints, comment/docstring/lab tiếng Việt giải thích từng bước khó. Lab và script dùng code thật trong src; hướng dẫn thuyết trình chọn 6 đoạn code thật sau khi có implementation. Không tạo hàm giả.

Sensor ĐHBK: location 4946813, PM2.5 13502154, PM10 13502152. Nhân Chính: location 4946812, PM2.5 13502151, PM10 13502153. Khí chỉ mở rộng khi đủ dữ liệu.

## Thiết kế và triển khai thực tế

| Hạng mục | Thiết kế | Thực tế hiện tại |
|---|---|---|
| Hạ tầng | Kafka, Spark, REST catalog, MinIO, Trino, Superset, PostgreSQL metadata | Chưa có Compose/dịch vụ nào được dựng |
| Thu thập | Metadata, live/backfill/replay, retry/checkpoint | Chỉ package/docstring, chưa gọi API |
| Lưu trữ | Bronze raw, Silver MERGE, Gold có điều kiện | Chưa có bảng/DDL/job |
| ML | RF/persistence causal features, split theo giờ | Chưa có model/dataset/metrics |
| Dashboard | Trino/Superset, gaps/freshness/forecast | Chưa có dashboard |
| Tài liệu | Prompt, kế hoạch, lab outline, walkthrough, presentation guide | Scaffold đã tạo, đã kiểm chứng scaffold, không kiểm chứng pipeline |
| Kiểm thử | pytest unit/integration/live rõ ranh giới | Chưa có test nghiệp vụ; không báo pass pipeline |

## Điểm vào code và tài liệu

- [Package](../src/air_quality/README.md): config/contracts/collector/processing/forecasting/observability mới có README và __init__.py, chưa có public function/CLI.
- [Kiến trúc](architecture.md), [dictionary](data-dictionary.md), [walkthrough](code-walkthrough.md), [presentation guide](presentation-guide.md), [labs](../labs/README.md).
- [Prompt Goal độc lập](../GOAL_PROMPT.md), [kế hoạch](../IMPLEMENTATION_PLAN.md), [nhật ký](AGENT_WORK_LOG.md), [provenance đề xuất](proposal/README.md).
- Evidence scaffold: [scaffold-verification](../artifacts/reports/scaffold-verification.md), 36 kiểm tra đạt và diff check sạch; chưa có kết quả pipeline.

## Invariant và quyết định đang hiệu lực

Giữ raw/provenance; Silver chống trùng theo sensor/khoảng đo, correction cần quy tắc từ nguồn; watermark không đủ cho dedup. Missing không thành 0. Replay tách namespace. Freshness theo sensor. ML không dùng tương lai để fill/tune, nhãn không vượt split cutoff. Bản khảo sát cũ 7.987 records không phải dữ liệu đã crawl ở repo.

## Blocker và quyết định còn mở cho Goal

- Chưa xác minh `period.interval` một giờ so với nhịp timestamp 5 phút; chặn mean và target ML liên quan cho đến khi có cơ sở.
- Chưa kiểm tra key/API/Docker/RAM/disk ở lượt scaffold; key không được lưu. Không giả định credential cũ còn dùng được.
- Python host phát hiện 3.13.12, nhưng package chỉ khai báo nền >=3.10. Runtime Spark/Java và version matrix/dependency lock/catalog backend chưa chốt ở P1.
- Chưa chốt schema wire/DDL/partition, correction tie-break, endpoint/cổng/CLI thực thi. `.env.example` chỉ là danh mục dự kiến, chưa có loader hoặc credentials dịch vụ.
- Lab gốc ngoài repository, chưa được vendor; xem provenance. Không tạo dependency vào file ngoài repo để chạy sản phẩm.

## Lệnh đã có và chưa có

Có thể kiểm tra Git bằng `git status --short --branch`, `git log -5 --oneline` và đọc pyproject bằng Python `tomllib` khi Python >=3.11. Package chỉ import bằng src path; đây không phải CLI. Chưa có start/backfill/live/train/predict/test/benchmark runnable; Goal phải thêm và kiểm chứng trước khi ghi cách dùng.

## Quy trình tiếp tục sau scaffold

Không tự bắt đầu Goal hoặc Docker. Khi người dùng giao Goal, đọc AGENTS/context/plan/log, xác minh Git và tạo/reuse `feat/air-quality-lakehouse` từ checkpoint chứa scaffold nếu main chưa merge. Làm P1 trước. Push checkpoint và draft PR theo Goal; scaffold chỉ push, không PR/merge. Cập nhật log/context sau mỗi mốc; không copy toàn bộ log vào đây.
