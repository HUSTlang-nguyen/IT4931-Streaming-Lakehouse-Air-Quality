# Context triển khai và contributor

Checkpoint STEP-021, cập nhật ngày25/10/2026. Repository root là thư mục IT4931-Streaming-Lakehouse-Air-Quality, không phải thư mục cha. Goal triển khai ban đầu đã complete; yêu cầu hiện tại chỉ hoàn thiện tài liệu contributor, không triển khai backlog/tạo lại Goal.

## Git và yêu cầu đang làm

- PR#1/#2 đã merge bởi maintainer. Mainf39b307 có cùng tree với checkpoint bàn giao4889243; đã xác minh từ GitHub. Không còn draft PR#2 hoặc phần push dang dở của Goal cũ.
- Nhánh docs/contributor-onboarding từ origin/mainf39b307; docs candidatec02c3f1, fix first-run testsfbff886 và evidence1012e7e đã push. Draft [PR#3](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/3) OPEN, đã attach; chờ maintainer review/merge. Onboarding docs và bản sửa test đã hoàn tất; main chỉ nhận phần này sau khi PR#3 được merge.
- Đã kiểm clone độc lập không .env/data/models/checkpoints/cache, venv mới Python3.13.12, pip install/check, CLI help,26unit pass, repo checks và Compose config --quiet.19PowerShell blocks parse pass. Báo cáo artifacts/reports/contributor-onboarding.md phân biệt kiểm chứng này với full Docker cold bootstrap.
- Pipeline/ML behavior không đổi; operations.run_tests nay tạo artifacts/local trước pytest sau khi probe sạch phát hiện parent thiếu (15pass/10errors). Fixfbff886 và regression test26pass trên clone mới khác; source SHA256 `1c84eeafb37e7dad3e588004510fd1dd9d09c4abf81befa9daf27ffa3258b918`. Full Docker bootstrap trên máy/engine riêng còn mở ONB-01; không dùng cache/volumes hiện có làm bằng chứng máy sạch. Không xóa/dừng stack hiện có để giả lập.

## Điểm vào cho contributor/agent

[SETUP](SETUP.md) là luồng clone→core/build→smoke→thu JSONL bounds UTC tròn giờ→profile→drain→process availableNow→đối chiếu Silver→train/predict/dashboard→live. Chưa mở producer live/continuous processor trong bước capture/reconciliation để tách ACK Kafka khỏi dữ liệu đã xử lý. [CONTRIBUTING](../CONTRIBUTING.md) quy định Git/tests/docs. [BACKLOG](BACKLOG.md) có ưu tiên/tiêu chí, không tự cho phép thực hiện mọi việc.

Dữ liệu lớn/key/model/volumes/ZIP/log/screenshot của máy phát triển không nằm trong Git. Contributor tự thu và train; không dùng lại snapshot IDs hay password của tác giả. Một checkout vận hành mỗi Docker engine vì project/cổng cố định. Windows/PowerShell là hướng dẫn chuẩn, Pythonhost3.11+; runtime Spark ở container.

## Kiến trúc hiện thực và nơi đọc code

- Collector → Kafka → Spark Structured Streaming → Iceberg/MinIO → Trino/Superset; MLlib RF từng trạm dự báo PM2.5 t+1h. Registry: ĐHBK location4946813 sensors13502154/13502152, Nhân Chính4946812 sensors13502151/13502153.
- Runtime pin: Python3.11.13/Java17.0.20.1/Spark3.5.6/Iceberg1.9.2/Kafka connector3.5.6/NumPy1.26.4; Kafka3.9.1, Trino476, Superset4.1.2, PostgreSQL16.9; MinIO source release2025-10-15/commit9e49d5e. Locks/digests trong requirements/infra.
- REST1.6.0 JdbcCatalog SQLite WAL/busy_timeout30s volume UID1000; Trino view-endpoints=false do backend viewAPI không tương thích. PostgreSQL giữ metadata Superset, MinIO giữ Iceberg objects. Local single-node, không HA.
- processing/transforms.py/tables.py/jobs.py: Bronzeevent_id; Silverkey(sensor_id,series_kind,period_start,period_end), mọi thành phần non-null, newest observation ưu tiên timestamp hợp lệ hơn null, event_id tie-break. Rejected source cũng dedup trước MERGE; additive nullable schema giữ original_ingested_at replay. Atomic full Gold refresh mỗi bảng, foreachBatch retry phục hồi giữa Silver/Gold, một writer/namespace.
- forecasting/features.py/model.py: exact lag1/2/3/24/current/hourVN, label+1h riêng, split70/15/15 có purge, train/validation/test/persistence cùng mẫu; operational kiểm input/model availability, stale suppression, forecast đầu giữ nguyên, actual enrichment mỗi predict. Chưa có scheduler ML nền.
- dashboard.py: provision5panel dữ liệu, sau train có8panel; native import cần meta.uuid từng chart, helper đọc UUID qua native export vì REST GET4.1.2 không trả UUID. operations.py/cli.py unified commands; benchmark.py/experiments.py đo riêng namespace.
- scripts/verify_repository.py kiểm syntax/TOML/links/secret/diff và source fingerprint; export_presentation_snippets.py trích6đoạn code thật cho slide. Docs-only không cần regenerate snippet hoặc chạy lại Spark khi source không đổi.

## Bằng chứng lịch sử trên máy phát triển (24/10/2026)

-25unit +14Spark/Iceberg pass,4API live pass riêng,4live skip trong run offline; null-key/quarantine/timestamp recovery đã có regression test. Source code SHA256 checkpoint685835732171bae50029777c6f28da1c596bf6d4c6f488e0c06597fe4b7e7644.
-180ngày2026-04-27..2026-10-24UTC có202.041 unique nguồn raw+hours, coverage91,597–93,981%, hourly gap87h. Kafka ACK và historical Bronze/Silver202041; hourly17280/missing1184/daily724/freshness8 tại snapshots report. Không dùng count này làm target cho ngày khác.
-RF snapshot5061425689190597954/version rf-f0077526710fd81e: ĐHBK test555 MAE11.3942/RMSE16.6638 vs persistence11.7468/15.0972; Nhân Chính649 RF6.7809/9.4208 vs5.7281/7.2831. Model local volume, không trên Git. Operational2trạm issue10:06UTC target11:00UTC và retry giữ forecast đầu; actual tại lần đo còn null.
-Restart counts trước/sau/resume bằng nhau, Silverduplicate0. Replay168public hourly riêng topic/namespace, original_ingested_at preserved168. Dashboard8unique UUID nodes sau import,17YAML, chart APIs200 và visual QA. Benchmark copy202537hàng thật riêng namespace,28→7files/exceptAll0/time travel cùngcount; clientmedian2.178→2.204s, không claim tăng tốc.

Các số/trạng thái trên là checkpoint lịch sử; file reports giữ provenance/revision/dirty lúc đo, không thay bằng hash tương lai. Không suy ra container/process đang sống trên máy contributor. Kiểm thực tế bằng status/HTTP/query khi cần vận hành; file context không thay monitor.

## Invariants và giới hạn phải giữ

Gold/ML dùng mean nguồn /hours đã kiểm contract; physical semantics raw interval1h/cadence5min chưa rõ, không tự average raw. Missing/invalid null; UTC lưu/VN hiển thị; daily count/24/windowbins. Hai trạm không đại diện toàn Hà Nội. Backtest snapshot không giả historical ingestion availability; RF không thắng baseline nhất quán.

Khoảng8GiB Docker: một JVM Spark mỗi lúc, dừng processor trước job riêng rồi resume; không writer live thứ hai. Host Collector và container dùng limiter SQLite khác filesystem nên không chạy API backfill nặng song song cùng key. Secrets qua .env ignored, không dump Compose config. Stop giữ dữ liệu, không down-v/prune/reset phá thay đổi hoặc forcepush.

[Nhật ký](AGENT_WORK_LOG.md) append-only; đọc STEP sau checkpoint này nếu có. [Kế hoạch](../IMPLEMENTATION_PLAN.md) là nghiệm thu cũ; [BACKLOG](BACKLOG.md) là việc tương lai. Đối chiếu Git/PR/process/artifacts trước khi tiếp tục, giữ thay đổi của người dùng.
