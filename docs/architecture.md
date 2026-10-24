# Kiến trúc đã triển khai

OpenAQ v3 → Python Collector → Kafka → Spark Structured Streaming → Iceberg Bronze/Silver/Gold trên MinIO → Trino → Superset. Spark MLlib đọc Gold snapshot và ghi predictions/metrics vào cùng catalog.

## Thành phần và lưu bền vững

| Thành phần | Vai trò / nơi lưu |
|---|---|
| Collector | Pagination, retry/rate limit, archive trước ACK; state SQLite volume collector_state; raw pages ở data/ |
| Kafka 3.9.1 | Hai partitions, ACK broker, log volume kafka_data; retention 720 giờ |
| Spark 3.5.6 | Python 3.11.13, Java 17.0.20.1, local[2], Iceberg 1.9.2; jobs và continuous processor cùng code |
| REST catalog 1.6.0 | JdbcCatalog SQLite WAL/busy_timeout30s /catalog/catalog.db trên catalog_data; UID1000, init owner thư mục |
| MinIO | Source build pinned release/commit; minio_data giữ S3 warehouse objects, metadata/data Iceberg |
| Trino 476 | Native S3 + REST catalog chung Spark, query HTTP; không chép measurements vào PostgreSQL |
| Superset 4.1.2 | Dashboard đọc Trino; PostgreSQL 16.9 giữ metadata, credentials local sinh ngẫu nhiên |
| MLlib | Model binary trên model_data; manifest config/snapshot/split/metrics; forecast/actual Iceberg |

REST view endpoints tắt trong Trino476 vì backend1.6.0 không tương thích view API; bảng Iceberg và virtual datasets Superset vẫn hoạt động. WAL cho phép đọc/commit đồng thời; timeout30s hữu hạn đã chạy lại test forecast/actual thành công.

SQLite catalog phù hợp một máy học tập, tránh thêm PostgreSQL catalog server trong ngân sách RAM. Đây không phải kiến trúc HA. Spark local[2] xử lý thật; không dựng worker rỗng chỉ để minh họa. Các daemon core dùng khoảng 4 GiB khi nhàn; dừng processor khi train/benchmark/test JVM riêng để không vượt Docker khoảng 7,46 GiB.

## Luồng và transaction

`Collector.collect_window` giữ metadata liên kết sensor, raw payload và request range. Sau ACK mới tăng checkpoint. Retry có thể tạo lại Kafka message; `merge_bronze` chống trùng event_id và `merge_silver` chống trùng business key. Newest ingested_at thắng, event_id là tie-break ổn định. Raw/hours riêng `series_kind`.

`foreachBatch` không có transaction xuyên nhiều bảng. Nếu crash giữa Silver và Gold, checkpoint chưa commit, microbatch retry MERGE idempotent rồi refresh Gold. `FileLock` giữ một writer/namespace. Full Gold overwrite bằng một Iceberg snapshot mỗi bảng, không truncate rồi append. Với hai trạm/180 ngày, chọn correctness và dễ học; chưa tối ưu cho hàng tỷ hàng.

Gold `/hours` dùng giá trị mean nguồn đã kiểm contract; raw reported interval1h/cadence5 phút vẫn chưa đủ giải thích vật lý. Grid tất cả sensor × giờ giữ missing/invalid null. Daily tính mean giờ hợp lệ theo ngày Việt Nam; giờ kết thúc 00:00 thuộc ngày trước; luôn có count/24 và window_bins cho ngày biên.

## ML và tính sẵn có

Self-join theo timestamp để có current/lag1/2/3/24; inner join loại thiếu. Nhãn là giờ tiếp theo, không đi vào vector. Ranh giới thời gian 70/15/15, purge label vượt ranh; chỉ fit train, chọn depth qua validation, test giữ lại. Persistence cùng hàng đủ features để so sánh công bằng; đây là tập con các giờ có dữ liệu, không đại diện toàn bộ giờ thiếu.

Backtest dùng snapshot hiện tại của lịch sử, không giả availability quá khứ. Operational kiểm ingested_at của mọi input <= issued_at, model đã train trước issue, target còn tương lai. Thiếu/stale thì báo trạng thái, không ép tạo forecast. `predict` là job theo lần gọi, không daemon scheduler; actual được refresh mỗi lần gọi.

## Reproducibility và giới hạn

Compose images có tag/digest, Python runtime và Java jars có lock; MinIO build theo source commit vì prebuilt upstream không truy cập được. Model/báo cáo giữ code revision/dirty và Iceberg snapshot. Secret chỉ qua .env ignored, không dump Compose config. Docker ports bind loopback; không triển khai internet/auth phân quyền đa người dùng.

Historical reconciliation giữ snapshot IDs nên counts không đổi khi live tăng. Restart giữ volume/checkpoint, không xóa dữ liệu. Pruning/compaction/time travel dùng namespace experiment riêng với bản sao không nhân bản hàng; không expire snapshots. Báo cáo benchmark ghi cache/local scale và không suy ra tăng tốc chung.
