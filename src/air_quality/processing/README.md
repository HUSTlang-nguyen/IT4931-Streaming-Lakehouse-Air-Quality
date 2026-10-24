# Xử lý Lakehouse

**Trạng thái:** scaffold, chưa có hàm nghiệp vụ.

PySpark Bronze/Silver/Gold, chuẩn hóa, MERGE chống trùng/correction, late data và quality. Gold mean chỉ sau xác minh khoảng đo.

**I/O dự kiến:** Kafka/raw → các bảng Iceberg có thể chạy lại an toàn, kèm báo cáo chất lượng.

Khi triển khai: thêm module có trách nhiệm cụ thể, giải thích vai trò/I/O và logic khó bằng docstring/comment tiếng Việt; cập nhật [walkthrough](../../../docs/code-walkthrough.md) và lab liên quan. Không thêm hàm giả để lấp thư mục.
