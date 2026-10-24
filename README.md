# Air Quality Streaming Lakehouse

Python/PySpark phân tích PM2.5, PM10 tại ĐHBK và Công viên Nhân Chính, Hà Nội; RF MLlib dự báo PM2.5 một giờ tiếp theo. Hai điểm quan trắc không đại diện toàn thành phố.

Bản triển khai đã merge qua [PR #2](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/2). Pipeline OpenAQ → Kafka → Spark → Iceberg/MinIO → Trino → Superset đã chạy trên máy phát triển; 25 unit và 14 Spark/Iceberg tests pass tại checkpoint đó. Báo cáo nguồn/ML/restart/benchmark trong Git là bằng chứng lịch sử, không phải dữ liệu/model được tải xuống khi clone.

## Contributor bắt đầu ở đây

1. [SETUP từ clone mới](docs/SETUP.md): điều kiện, build/smoke, tự thu JSONL, đối chiếu Silver, train/dashboard và vận hành live. Windows/PowerShell là hướng dẫn chuẩn; Python host3.11+, Docker Linux engine khoảng8GiB RAM.
2. [CONTRIBUTING](CONTRIBUTING.md): nhánh/PR, chuẩn Python và comment tiếng Việt, kiểm thử theo thay đổi, cập nhật log/context.
3. [BACKLOG](docs/BACKLOG.md): việc còn mở và tiêu chí nhận việc. Fresh Docker bootstrap trên máy riêng còn cần kiểm chứng; xem [báo cáo onboarding](artifacts/reports/contributor-onboarding.md).

```powershell
git clone https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality.git
Set-Location IT4931-Streaming-Lakehouse-Air-Quality
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m air_quality.cli test
```

Đoạn trên chỉ kiểm package/unit. Làm tiếp SETUP để dựng pipeline; không cần cài Java/Spark trên host. `.env`, API key, raw/JSONL, models, checkpoints và volumes do bạn tự tạo. Credential Superset sinh trong `.env` của máy bạn; không dùng password máy tác giả. Compose dùng project/cổng cố định nên một checkout vận hành trên mỗi Docker engine.

## Kiến trúc và cách học

```text
OpenAQ v3 → Python Collector → Kafka → Spark Structured Streaming
                                         ↓
                              Iceberg Bronze / Silver / Gold trên MinIO
                                         ↓                 ↓
                                Trino → Superset      Spark MLlib RF
                                         ↑                 ↓
                                         └──── predictions / metrics
```

Gold/ML dùng mean nguồn `/hours`; không tự bình quân raw cadence5phút vì nguồn báo interval1h chưa được giải thích về mặt vật lý. Missing/invalid giữ null; lưu UTC, hiển thị giờ Việt Nam. Backtest hồi cứu snapshot khác operational forecast. RF chưa thắng persistence nhất quán; `predict` chạy theo lần gọi, chưa có scheduler ML nền. Không có AQI hoặc khuyến cáo sức khỏe.

- [Kiến trúc](docs/architecture.md), [dictionary](docs/data-dictionary.md), [walkthrough](docs/code-walkthrough.md).
- [Labs01–07](labs/README.md), [demo khi đã có dữ liệu](docs/demo.md), [6đoạn code cho slide](docs/presentation-guide.md).
- [Báo cáo nghiệm thu](artifacts/reports/end-to-end-summary.md), [chỉ mục evidence](artifacts/README.md), [kế hoạch đã nghiệm thu](IMPLEMENTATION_PLAN.md).
- [Context tiếp tục công việc](docs/IMPLEMENTATION_CONTEXT.md), [nhật ký STEP](docs/AGENT_WORK_LOG.md), [AGENTS](AGENTS.md).

Dashboard sau setup: [Superset local](http://localhost:18088/superset/dashboard/air-quality-hanoi/). `stop` giữ dữ liệu; không `down -v`/prune. Dừng processor trước Spark job train/test integration/benchmark riêng để phù hợp RAM; SETUP có thứ tự và cách resume.

## Git và Goal

[Repository](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality), base đóng góp là `main`; PR #1/#2 đã merge. Kiểm branch/PR hiện tại trước khi tiếp tục checkpoint cũ. Mở nhánh mới cho thay đổi mới, agent không tự merge/force-push/xóa branch hoặc volume.

[GOAL_PROMPT](GOAL_PROMPT.md) lưu đặc tả lần triển khai đã hoàn tất. Contributor đọc để hiểu phạm vi; không cần tạo lại Goal đó hoặc tự triển khai toàn backlog. Khi dùng agent cho yêu cầu mới, bắt đầu từ context và công việc cụ thể được giao.
