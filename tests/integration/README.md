# Integration tests

**Đã có:** test_openaq_live.py; chưa có test broker/Spark/Iceberg.

`--run-live` kiểm ID/parameter và chuỗi giờ API của bốn sensor, dùng chung SQLite limiter với Collector. Không bật flag thì skip trước khi đọc key. Marker integration/live tách biệt; test live trong thư mục này không bắt buộc marker integration. Phần Kafka/Spark/Iceberg/Trino/restart còn chờ implementation. Cleanup không được phá dữ liệu người dùng.
