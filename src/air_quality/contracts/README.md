# Hợp đồng dữ liệu

**Đã có:** [envelope v1 và thời gian](events.py); chưa có DDL/schema Spark.

Schema, định danh measurement, metadata, đơn vị và quy tắc thời gian. Chốt bằng mẫu API thật trước khi tạo schema thực thi.

**I/O dự kiến:** Payload/metadata → các hợp đồng dùng chung cho Collector, Spark và tests.

Envelope giữ raw JSON và `series_kind=measurements|hours`, ID ổn định khi retry một trang/job, mode/provenance riêng. Khóa logic Silver phải gồm series_kind; event_id không thay business key. UTC parser từ chối timestamp naive. Xem [dictionary](../../../docs/data-dictionary.md).
