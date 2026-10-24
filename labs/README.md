# Lộ trình lab

Người mới hoàn thành [SETUP](../docs/SETUP.md) trước để tự có runtime/dữ liệu/model. Các bài gọi code production Python/PySpark, không sao chép pipeline vào notebook.

| Bài | Nội dung / bằng chứng |
|---|---|
| [01 OpenAQ](01-openaq.md) | Registry, API contract, source hourly semantics |
| [02 Collector](02-collector.md) | Pagination/retry/checkpoint/Kafka/live/backfill/replay |
| [03 Lakehouse](03-lakehouse.md) | Bronze/Silver MERGE, E2E và Spark tests |
| [04 Gold](04-gold-quality.md) | Null gaps, coverage, UTC+7 daily |
| [05 Dashboard](05-dashboard.md) | Trino/Superset, native export/import, visual QA |
| [06 ML](06-forecasting.md) | Causal features, RF/persistence, split và forecast |
| [07 Iceberg](07-iceberg.md) | Pruning/compaction/time travel measurements |

Lần kiểm chứng và phần còn thiếu xem [context](../docs/IMPLEMENTATION_CONTEXT.md); fixture pass không thay bằng chứng live. Tất cả thao tác giữ volume/snapshot, không yêu cầu cleanup xóa dữ liệu.
