# Thu thập OpenAQ

**Trạng thái:** scaffold, chưa có hàm nghiệp vụ.

Metadata/measurement, phân trang, retry/rate limit, checkpoint và live/backfill/replay. Tách API I/O khỏi logic chia khoảng và biến đổi.

**I/O dự kiến:** Khoảng thời gian/sensor → event Kafka có provenance và tiến độ có thể resume.

Khi triển khai: thêm module có trách nhiệm cụ thể, giải thích vai trò/I/O và logic khó bằng docstring/comment tiếng Việt; cập nhật [walkthrough](../../../docs/code-walkthrough.md) và lab liên quan. Không thêm hàm giả để lấp thư mục.
