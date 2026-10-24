# Air Quality Streaming Lakehouse

Python/PySpark phân tích PM2.5, PM10 tại ĐHBK và Công viên Nhân Chính, Hà Nội. Hai điểm quan trắc không đại diện toàn thành phố.

**Đã chạy:** OpenAQ → Kafka → Spark → Iceberg/MinIO → Trino → Superset. Lịch sử nguồn 180 ngày có 202.041 bản ghi raw/hourly; Silver được đối chiếu tại snapshot cụ thể. Restart giữ nguyên dữ liệu, Silver không trùng khóa. RF/persistence, operational forecast và benchmark Iceberg đã chạy; xem [context](docs/IMPLEMENTATION_CONTEXT.md) để biết checkpoint mới nhất.

## Chạy trên Windows / PowerShell

Cần Docker Desktop Linux engine khoảng 8 GiB RAM, Python host3.11+ và Git. Spark chạy trong container Python 3.11, không cài Java/Spark lên host.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Điền OPENAQ_API_KEY trong .env bằng editor, không đưa key vào lệnh hoặc Git.
.venv/Scripts/python.exe -m air_quality.cli start
.venv/Scripts/python.exe -m air_quality.cli status
# Không chạy hai Collector API nặng cùng key ở host và container.
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop collector
.venv/Scripts/python.exe -m air_quality.cli backfill --run-name history-180d
.venv/Scripts/python.exe -m air_quality.cli start --services collector --no-build
.venv/Scripts/python.exe -m air_quality.cli dashboard
```

`start` tạo các credential local còn trống, giữ credential đã có, build image pinned và mở continuous Collector/processor. Lần đầu build MinIO source/Spark có thể lâu. Có thể chỉ mở core bằng `start --services kafka minio catalog postgres trino superset` nếu chưa có API key. Trong khi lịch sử được tải, các bảng chưa đầy đủ; kiểm tra báo cáo coverage thay vì chờ count ước lượng.

Dashboard: [Superset local](http://localhost:18088/superset/dashboard/air-quality-hanoi/). Tài khoản/password xem `.env` local bằng editor; không dùng credential mẫu chung. Trino: localhost:18080; Kafka external: localhost:19092. Ports chỉ bind loopback.

```powershell
# Dừng processor khi chạy Spark job nặng để phù hợp RAM laptop; checkpoint được giữ.
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop processor
.venv/Scripts/python.exe -m air_quality.cli train
.venv/Scripts/python.exe -m air_quality.cli predict
.venv/Scripts/python.exe -m air_quality.cli benchmark
.venv/Scripts/python.exe -m air_quality.cli start --services processor --no-build
.venv/Scripts/python.exe -m air_quality.cli test
# Tạm dừng processor trước test --integration vì tests dùng JVM riêng.
.venv/Scripts/python.exe -m air_quality.cli stop
```

`stop` giữ volumes; không chạy `down -v`. `predict` phát hành theo lần gọi; không có scheduler ML nền. Gọi lại sau một giờ hoặc qua lịch vận hành do người dùng thiết lập. Backtest được ghi riêng operational, không xem dữ liệu lịch sử tải hôm nay là dữ liệu đã có trong quá khứ. Xem [Lab 06](labs/06-forecasting.md).

## Thiết kế và bằng chứng

```text
OpenAQ v3 → Collector → Kafka → Spark Structured Streaming
                                  ↓
                       Iceberg Bronze / Silver / Gold trên MinIO
                                  ↓                 ↓
                         Trino → Superset      Spark MLlib RF
                                  ↑                 ↓
                                  └──── predictions/metrics
```

Gold dùng mean nguồn `/hours`, không tự bình quân raw timestamp 5 phút vì raw báo interval một giờ. Thiếu giữ null, UTC lưu/giờ Việt Nam hiển thị. RF dự báo PM2.5 một giờ tiếp theo từng trạm, so persistence cùng mẫu; không có AQI, dự báo khí hay khuyến cáo sức khỏe.

- [Kiến trúc](docs/architecture.md), [dictionary](docs/data-dictionary.md), [walkthrough](docs/code-walkthrough.md).
- [Labs 01–07](labs/README.md), [demo](docs/demo.md), [code lên slide](docs/presentation-guide.md).
- [Báo cáo nhỏ](artifacts/README.md), [kế hoạch](IMPLEMENTATION_PLAN.md), [context](docs/IMPLEMENTATION_CONTEXT.md), [nhật ký](docs/AGENT_WORK_LOG.md).
- [Goal prompt độc lập](GOAL_PROMPT.md) và [quy tắc agent](AGENTS.md). Goal active thì tiếp tục, không tạo trùng.

## GitHub

[Repository](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality), nhánh `feat/lakehouse-ml-completion`, [draft PR #2](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/2). Không tự merge. Chỉ commit code, config, lock, fixture/báo cáo nhỏ sạch secret; raw/model/checkpoint/cache local được ignore.
