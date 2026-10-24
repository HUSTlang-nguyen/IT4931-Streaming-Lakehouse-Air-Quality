# Hạ tầng local

[compose.yaml](compose.yaml) định nghĩa project air-quality-lakehouse. Khởi động bằng CLI start để tạo credential còn trống; không in compose config đã resolve vì chứa secrets.

Kafka/MinIO/REST catalog/Postgres/Trino/Superset là core; Collector/processor profile pipeline, Spark job profile jobs. REST JdbcCatalog SQLite volume UID1000; Postgres giữ Superset metadata. [Kiến trúc](../docs/architecture.md) giải thích RAM, ports, transactions và giới hạn.

Runtime Python3.11.13/Java17/Spark3.5.6 đã smoke cùng Trino476/Iceberg1.9.2. Python freeze ở requirements/runtime-py311.lock, JAR SHA256 ở requirements/java-artifacts.lock.json. MinIO [source build](minio/README.md). Image pin digest trong Compose/Dockerfiles; không dùng latest.

Stop giữ dữ liệu. Dừng processor trước job ML/benchmark/tests JVM riêng trên Docker8GiB; resume bằng start --services processor --no-build. Không down-v hoặc prune.
