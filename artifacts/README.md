# Bằng chứng đã chạy

Báo cáo nhỏ sạch secret được theo dõi trong reports. Data/raw/model/volumes/full logs/auth browser chỉ local ignored. Không coi fixture là live hoặc backtest là operational.

| Báo cáo | Nội dung |
|---|---|
| [Collector](reports/collector-checkpoint.md) | API hourly contracts và unit checkpoint/retry |
| [Nguồn180ngày](reports/source-coverage.json) / [giải thích](reports/backfill-180d.md) |202.041 unique nguồn, gaps/coverage thực tế |
| [Spark smoke](reports/spark-smoke.json) | Spark ghi và đọc Iceberg; Trino cùng catalog |
| [Reconciliation](reports/lakehouse-history-reconciliation.json) | Counts sensor/resource tại snapshots lịch sử, time travel |
| [Restart](reports/restart-persistence.json) | Counts trước/sau/resume bằng nhau, Silver duplicate0 |
| [Stack/dashboard checkpoint](reports/stack-dashboard-checkpoint.json) | Bằng chứng giai đoạn trước ML |
| [ML](reports/ml-evaluation.json) | RF/persistence cùng test mẫu, splits/config/snapshot/seed/model version |
| [Operational](reports/operational-forecast.json) | Issue time/input snapshot/status từng trạm |
| [Iceberg](reports/iceberg-benchmark.json) | Pruning,28→7files, nguyên hàng không đổi, time travel và timings thật |

Reports ghi code revision/working_tree_dirty tại lần chạy. Nếu đo trước commit, dirty=true là minh bạch; không thay provenance cũ bằng hash commit tương lai. Runtime dependency locks trong requirements và Compose/Dockerfiles; log/JUnit/screenshot local trong artifacts/local, output/playwright.

[Nghiệm thu toàn hệ thống](reports/end-to-end-summary.md), [final verification](reports/final-verification.json), [forecast retry](reports/forecast-idempotency.json), [replay isolation](reports/replay-isolation.json), [live status](reports/live-final-status.json).
