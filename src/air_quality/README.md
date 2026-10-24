# Package air_quality

Collector/envelope/config và source profiler đã có code và kiểm chứng. Processing/forecasting còn scaffold; chưa có bảng Spark/ML chạy. Dùng layout `src` để tách mã thư viện khỏi script/lab.

| Package | Trách nhiệm |
|---|---|
| [config](config/README.md) | Cấu hình |
| [contracts](contracts/README.md) | Hợp đồng dữ liệu |
| [collector](collector/README.md) | Thu thập OpenAQ |
| [processing](processing/README.md) | Xử lý Lakehouse |
| [forecasting](forecasting/README.md) | Dự báo PM2.5 |
| [observability](observability/README.md) | Quan sát vận hành |

Logic biến đổi kiểm thử độc lập với API/Kafka/storage I/O. Hàm nghiệp vụ có type hints, docstring tiếng Việt; tên module/hàm tiếng Anh. [CLI](cli.py) hỗ trợ inspect/backfill/live/replay/profile; stack và ML sẽ bổ sung khi module có implementation thật.
