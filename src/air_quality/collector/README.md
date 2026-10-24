# Thu thập OpenAQ

**Đã có:** HTTP adapter, checkpoint SQLite, rate limiter, raw page archive và publishers Kafka/JSONL. Kafka publisher chưa được kiểm chứng với broker thật do Docker chưa khởi động được.

Metadata/measurement, phân trang, retry/rate limit, checkpoint và live/backfill/replay. Tách API I/O khỏi logic chia khoảng và biến đổi.

**I/O dự kiến:** Khoảng thời gian/sensor → event Kafka có provenance và tiến độ có thể resume.

## Đọc theo thứ tự

1. [openaq.py](openaq.py): timeout, bounded retry, Retry-After; error chỉ có path/status.
2. [state.py](state.py): request budget SQLite bền vững, tiến độ trang và mốc run cố định.
3. [service.py](service.py): metadata → raw page bất biến → publish ACK → checkpoint. Retry cùng trang dùng lại archive.
4. [publisher.py](publisher.py): JSONL fsync hoặc Kafka delivery ACK; sink khác dùng checkpoint khác.
5. [CLI](../cli.py): inspect/backfill/live/replay. Xem [lab Collector](../../../labs/02-collector.md).

Không diễn giải `meta.found` kiểu `>1000` thành số. FileLock nhả khi process chết, SQLite chỉ tiến sau ACK. Replay gắn nhãn riêng và không sửa archive nguồn.
