# Air Quality Streaming Lakehouse

Đồ án Python/PySpark giám sát PM2.5, PM10 tại ĐHBK và Công viên Nhân Chính, Hà Nội; dự kiến bổ sung dự báo PM2.5 trước một giờ.

**Trạng thái: đã có Collector Python và kiểm chứng OpenAQ; stack Lakehouse/ML chưa triển khai xong.** Unit tests và hợp đồng hourly bốn sensor đã chạy; đã tải/profile 180 ngày với 202.041 bản ghi nguồn raw/hourly duy nhất, có checkpoint. Không coi JSONL là bằng chứng Kafka/Iceberg/dashboard.

## Bắt đầu với Goal

1. Mở đúng thư mục repository này trong Codex; không dùng thư mục cha làm Git root.
2. Đọc [quy tắc agent](AGENTS.md), [context](docs/IMPLEMENTATION_CONTEXT.md) và [kế hoạch](IMPLEMENTATION_PLAN.md).
3. Khi muốn triển khai, gửi toàn bộ phần prompt trong [GOAL_PROMPT.md](GOAL_PROMPT.md). File prompt không tự tạo Goal; xem context để biết phiên đang chạy tới đâu.
4. Khi Collector được triển khai, cung cấp `OPENAQ_API_KEY` qua môi trường hoặc `.env` cục bộ. [.env.example](.env.example) chỉ là danh mục cấu hình dự kiến; chưa có config loader.

Các lệnh Collector đã có: `.venv/Scripts/python.exe -m air_quality.cli --help` (inspect/backfill/live/replay). Xem [Lab 01](labs/01-openaq.md) và [Lab 02](labs/02-collector.md). Các lệnh start/train/predict/benchmark chưa có, sẽ bổ sung cùng module tương ứng.

## Kiến trúc dự kiến

```text
OpenAQ v3 → Python Collector → Kafka → PySpark
                                      ↓
                         Iceberg / MinIO (Bronze → Silver → Gold)
                                      ↓                     ↓
                              Trino → Superset       Spark MLlib
                                                           ↓
                                                   Bảng dự báo Iceberg
```

Spark/Trino dùng chung Iceberg REST catalog. PostgreSQL phục vụ metadata cần thiết; catalog backend và phiên bản cụ thể được chốt trong khảo sát.

## Cấu trúc

| Đường dẫn | Trách nhiệm |
|---|---|
| [src/air_quality](src/air_quality/README.md) | Package config, contracts, collector, processing, forecasting, observability |
| [infra](infra/README.md) | Docker Compose và cấu hình dịch vụ |
| [sql](sql/README.md) | DDL, truy vấn và thực nghiệm |
| [dashboards](dashboards/README.md) | Cấu hình Superset tái tạo được |
| [scripts](scripts/README.md) | Gọi logic trong package, không sao chép nghiệp vụ |
| [tests](tests/README.md) | Unit, integration và fixtures |
| [labs](labs/README.md) | Lộ trình học từ OpenAQ đến ML và Iceberg |
| [docs](docs/README.md) | Context, nhật ký, thiết kế và thuyết trình |
| [artifacts](artifacts/README.md) | Bằng chứng và báo cáo nhỏ |

## Đọc và tiếp tục

- [Kiến trúc](docs/architecture.md) và [data dictionary](docs/data-dictionary.md).
- [Walkthrough code](docs/code-walkthrough.md) và [hướng dẫn thuyết trình](docs/presentation-guide.md).
- [Nhật ký theo thời gian](docs/AGENT_WORK_LOG.md) và [đề xuất/nguồn tài liệu](docs/proposal/README.md).

Code dùng Python; comment/docstring và lab bằng tiếng Việt. Chưa chốt Python cho Spark; phiên bản trên host không phải cam kết tương thích hệ thống.

## GitHub

[Repository](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality). Nhánh chuẩn bị `chore/project-scaffold`; nhánh triển khai dự kiến `feat/air-quality-lakehouse`. Khi scaffold chưa merge, tạo nhánh triển khai từ checkpoint scaffold để giữ tài liệu. Không tự merge `main`.
