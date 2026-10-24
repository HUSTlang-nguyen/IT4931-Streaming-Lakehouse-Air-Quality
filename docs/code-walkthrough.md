# Đọc code theo đường đi của một measurement

**Trạng thái:** chỉ có package scaffold và docstring. Chưa có hàm nghiệp vụ để trích. Các đường dẫn sau là trách nhiệm dự kiến, không phải chức năng đã chạy.

## Trình tự đọc

1. [config](../src/air_quality/config/README.md): cấu hình lấy từ đâu, kiểm tra gì, che secret như thế nào.
2. [contracts](../src/air_quality/contracts/README.md): ID, schema, timestamp/đơn vị và định danh bản ghi.
3. [collector](../src/air_quality/collector/README.md): metadata, khoảng truy vấn, phân trang/retry, event Kafka, checkpoint.
4. [processing](../src/air_quality/processing/README.md): raw Bronze → chuẩn hóa/dedup Silver → Gold có điều kiện.
5. [sql](../sql/README.md) và [dashboards](../dashboards/README.md): đọc cùng bảng qua Trino, hiển thị gap/freshness.
6. [forecasting](../src/air_quality/forecasting/README.md): chuỗi giờ hợp lệ → causal features → split → model/baseline → forecast table.
7. [observability](../src/air_quality/observability/README.md) và [tests](../tests/README.md): thấy lỗi ở đâu, bằng chứng nào xác nhận đúng.

## Mẫu cập nhật cho mỗi tính năng đã có

- File và tên hàm thật; link tới source thay cho bản copy logic khác.
- Một input nhỏ đã làm sạch, output mong đợi và invariant được kiểm tra.
- Các bước biến đổi, I/O và lỗi/side effect, lý do quyết định khó.
- Lệnh chạy thực tế, prerequisite và evidence tương ứng; test gọi đúng production function.
- Mối liên hệ với bước trước/sau, tác động khi duplicate/late/corrected data.

Không ghi tên hàm/lệnh giả ở scaffold. Agent hoàn thiện từng mục cùng implementation và đồng bộ sau refactor. [Labs](../labs/README.md) là đường học thực hành; file này là chỉ mục đọc code.
