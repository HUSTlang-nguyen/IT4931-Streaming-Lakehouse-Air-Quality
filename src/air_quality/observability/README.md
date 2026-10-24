# Quan sát vận hành

**Đã có:** [coverage.py](coverage.py) đọc envelope JSONL và thống kê nguồn; [evidence.py](evidence.py) gắn thời gian/code revision/dirty state. Chưa có metrics vận hành Spark.

Log không secret, tiến độ thu thập, freshness/coverage theo sensor, lỗi và metadata bằng chứng. Chưa chọn framework metrics.

**I/O dự kiến:** Trạng thái/thống kê job → log/metrics/báo cáo đã làm sạch.

Profiler kiểm uniqueness/correction/range/gap, availability bin giờ, invalid/flags và coverage nguồn bất thường. Không gọi API/đọc key và không nhầm source count với Silver count. Xem CLI profile và [backfill report](../../../artifacts/reports/backfill-180d.md).
