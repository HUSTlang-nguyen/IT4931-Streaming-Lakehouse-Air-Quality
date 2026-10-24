# Truy vấn Trino

[station-comparison.sql](station-comparison.sql) so hai trạm trên cùng giờ đủ dữ liệu. [missing-hours.sql](missing-hours.sql) nhóm dải missing liên tiếp từ Gold grid null. Chạy qua CLI query hoặc Superset SQL Lab, catalog iceberg/schema live; không sửa dữ liệu.

DDL thực thi dựa schema DataFrame và Iceberg v2 ở processing/tables.py. Partition Bronze days(ingested_at), Silver/Gold hourly months(period_end); daily/freshness nhỏ không partition. Experiment SQL/procedure trong processing/experiments.py và report benchmark giữ query plans/scan evidence.
