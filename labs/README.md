# Lộ trình lab

**Đã có phần Collector/API:** [Lab 01](01-openaq.md), [Lab 02](02-collector.md). Phần Kafka và các bài sau còn chờ kiểm chứng stack; không tạo notebook riêng sao chép nghiệp vụ.

| Bài | Chủ đề | Đầu ra nghiệm thu dự kiến |
|---|---|---|
| 01 | Khám phá OpenAQ | Metadata/payload sạch, sensor/cadence/interval được kiểm tra |
| 02 | Collector và Kafka | Phân trang, retry, checkpoint, live/backfill/replay |
| 03 | Bronze và Silver | Giữ gốc, chuẩn hóa, dedup/correction và late data |
| 04 | Gold và chất lượng | Coverage/freshness/gap, tổng hợp có cơ sở |
| 05 | Trino và Superset | Query/dashboard tái tạo được |
| 06 | Features và ML | Split theo thời gian, baseline, MAE/RMSE thật |
| 07 | Iceberg experiments | Pruning, compaction, time travel có bằng chứng |

## Cấu trúc bắt buộc mỗi bài

1. Mục tiêu và prerequisite: dịch vụ/dữ liệu/quyền, thời gian chạy dự kiến khi đã đo.
2. Kiến thức tối thiểu và sơ đồ input → xử lý → output.
3. Link file/hàm production thực tế, ví dụ nhỏ đã làm sạch và comment giải thích bước khó.
4. Lệnh PowerShell/Python có thể chạy; không ghi lệnh giả như đã tồn tại.
5. Kết quả kỳ vọng, cách đối chiếu/invariant và vị trí bằng chứng.
6. Lỗi thường gặp, cách chẩn đoán, cách chạy lại không mất dữ liệu.
7. Bài tập nhỏ và tiêu chí tự kiểm tra.
8. Nếu có thao tác sửa/xóa dữ liệu, đánh dấu rõ và không tự chạy cleanup phá volume.

Khi hoàn thành bài, ghi phiên bản code và lần chạy kiểm chứng. Thay đổi code phải cập nhật lab. Liên kết từ đây tới bài đã có; không tạo liên kết tới tên file chưa tồn tại.
