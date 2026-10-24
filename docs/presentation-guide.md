# Trích code thật cho thuyết trình

**Trạng thái:** chưa có nghiệp vụ, vì vậy chưa có snippet để trình bày như kết quả triển khai. Không tự sửa bộ slide cũ trong lượt scaffold.

## Sáu điểm trình bày dự kiến

| Chủ đề | Điều người nghe cần hiểu | Kiểm chứng cần đi kèm |
|---|---|---|
| Collector / pagination | Một khoảng thời gian có nhiều trang, retry không làm mất trang | Fixture nhiều trang và đối chiếu mẫu API thật |
| Chuẩn hóa measurement | Một dòng tương ứng sensor/khoảng đo, UTC và unit rõ | Raw nhỏ → Silver hợp lệ/quality flag |
| Chống trùng | Thu thập lại cùng khóa không nhân đôi Silver | Count trước/sau, correction riêng |
| Dữ liệu đến muộn | Bản ghi cũ xuất hiện muộn vẫn cập nhật đúng phần liên quan | Inject late event và đối chiếu Gold |
| Features ML | Lag theo giờ thật và chỉ dùng thông tin quá khứ | Mẫu có gap và kiểm tra không leakage |
| Đánh giá model | So RF với persistence trên cùng tập tương lai | MAE/RMSE, sample count, split range thật |

## Mẫu cho mỗi đoạn code khi có implementation

1. Tên chủ đề, file/hàm và commit được trình bày; snippet khoảng 10–25 dòng từ code thật.
2. Một ý chính, input/output tối giản có đơn vị/mốc thời gian.
3. Giải thích tiếng Việt 30–60 giây: vấn đề → cách code giải quyết → bằng chứng.
4. Link source và artifact/test liên quan; ghi rõ mock/live/backtest/operational.

Nếu snippet bỏ bớt đoạn phụ để vừa slide, đánh dấu phần lược bằng comment và không thay đổi ngữ nghĩa. Dẫn toàn bộ hàm trong source. Sau refactor, cập nhật snippet hoặc chuyển sang link nguồn mới; không giữ số dòng đã cũ. Không vẽ kết quả/model metrics giả.
