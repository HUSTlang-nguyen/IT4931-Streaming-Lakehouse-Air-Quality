# Package air_quality

Chỉ có package và docstring; chưa có chức năng chạy. Dùng layout `src` để tách mã thư viện khỏi script/lab.

| Package | Trách nhiệm |
|---|---|
| [config](config/README.md) | Cấu hình |
| [contracts](contracts/README.md) | Hợp đồng dữ liệu |
| [collector](collector/README.md) | Thu thập OpenAQ |
| [processing](processing/README.md) | Xử lý Lakehouse |
| [forecasting](forecasting/README.md) | Dự báo PM2.5 |
| [observability](observability/README.md) | Quan sát vận hành |

Logic biến đổi nên kiểm thử độc lập với API/Kafka/storage I/O. Hàm nghiệp vụ có type hints, docstring tiếng Việt; tên module/hàm bằng tiếng Anh. Chưa export API hoặc CLI giả.
