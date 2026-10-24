# processing

- session.py: Spark UTC, REST/S3 chung catalog Trino, readiness/bucket.
- transforms.py: parse Kafka/deadletter, normalize/quality, dedup và Gold pure transforms.
- tables.py: Iceberg v2 create/MERGE, atomic Gold overwrite, correction/late recovery.
- jobs.py: entrypoint smoke/ingest/train/predict/benchmark jobs trong container.
- experiments.py: copy real Silver riêng namespace, pruning/compaction/time travel.

[Lab03](../../../labs/03-lakehouse.md) và [Lab04](../../../labs/04-gold-quality.md). foreachBatch at-least-once, MERGE + checkpoint tạo kết quả idempotent; không transaction đa bảng.
