# Context triển khai hiện tại

Checkpoint STEP-018, ngày24/10/2026. Phạm vi GOAL_PROMPT.md đã được triển khai và nghiệm thu, không tạo Goal trùng. Repository con IT4931-Streaming-Lakehouse-Air-Quality; không dùng Git root thư mục cha.

## Bàn giao Git / Goal

- Nhánh feat/lakehouse-ml-completion từ main78fffbb; code checkpoint e18e0b0. Draft PR#2 OPEN, đã attach: https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/2. PR#1 merged bên ngoài tác vụ, giữ nguyên nhánh/lịch sử cũ. Không merge/forcepush/deletebranch/volume.
- P0–P6 đã có bằng chứng. Context/log/plan/reports cập nhật để commit/push metadata cuối; đối chiếu git status và remote HEAD nếu khôi phục ngay lúc bàn giao. Sau push đồng bộ mới đóng Goal bằng tool. Trạng thái Goal xem công cụ, không tạo lại cùng công việc đã hoàn tất.
- Test26515 terminal0:25unit+14Spark pass,4live skip;4OpenAQ live pass riêng trước đó. Processor12624 đã resume healthy; Collector/core sống. Không còn Spark job dài hoặc blocker bắt buộc.

## Đã chạy thật

- OpenAQ4sensors ĐHBK13502154/13502152, Nhân Chính13502151/13502153. Source180ngày202.041 unique raw+hours, bounds2026-04-27..2026-10-24UTC; source coverage91,597–93,981%, hourly gap87h. data/history-180d.jsonl/raw/metadata/key local ignored.
- Kafka ACK202.041, Structured Streaming11batches, historical Bronze/Silver202.041/hourly17280(missing1184)/daily724/freshness8, fixed snapshots trong lakehouse-history-reconciliation.json. Live đã tăng, không ép current count bằng lịch sử.
- Restart: counts trước/sau/resume bằng nhau, Silver duplicate0. Replay riêng168public source events, original_ingested_at preserved168, Bronze/Silver168/hourly672; không trộn live.
- Unit25pass, Spark14pass/4live skip ở tests-final-null-guards-fixed.log và tests-spark.xml;4OpenAQ contract pass riêng trước đó. Cases: retry/pagination/ACK, duplicate/correction/late/gap/invalid/UTC/replay/schema evolution, lag availability/label purge/null metrics/stale/model issue/retry actual enrichment.
- RF MLlib từng trạm, snapshot5061425689190597954, version rf-f0077526710fd81e,30trees seed42, depth8 chọn qua validation. ĐHBK test555 RF MAE11.3942/RMSE16.6638 vs persistence11.7468/15.0972; Nhân Chính649 RF6.7809/9.4208 vs persistence5.7281/7.2831. Model binary/manifest trên model_data; ml-evaluation.json giữ splits/ranges/config/importances/provenance.
- Operational issue10:06:41UTC target11:00UTC,2trạm dùng source hours10:00, forecast đầu tiên giữ nguyên khi gọi lại. forecast-idempotency.json, operational-forecast.json. Actual chưa có giữ null, enrich mỗi predict; không có ML scheduler nền mặc định.
- Dashboard8charts,17nativeYAML files, export/import verified UUID layout8unique nodes, chart APIs200, screenshot output/playwright/dashboard-final.png đã kiểm. Browser Playwright session airquality riêng task, auth state ignored, không print cookies/token.
- Benchmark experiment_20261024_095728 copy202537 hàng thật không nhân bản,28→7files/10515307→9327132bytes, tháng7chạm4→1files, exceptAll0/time travelSpark+Trino202537; clientmedian2.178→2.204s, không claim tăng tốc. Giữ snapshots/experiment failed đầu để audit.

## Kiến trúc / điểm đọc code

Compose project air-quality-lakehouse: Kafka3.9.1, MinIO source pinned release2025-10-15/commit9e49d5e, REST1.6.0 SQLite WAL/busy_timeout30s volumeUID1000, PostgreSQL16.9 metadata Superset4.1.2, Trino476. Runtime Python3.11.13/Java17.0.20.1/Spark3.5.6/Iceberg1.9.2/Kafka connector3.5.6/NumPy1.26.4 đã chạy; locks và digests trong requirements/infra. Trino view-endpoints=false vì REST viewAPI1.6 lỗi, vẫn dùng Iceberg tables/SQL virtual datasets.

processing/transforms,tables,jobs: Bronzeevent_id, Silverkey(sensor_id,series_kind,period_start,period_end), newest ingested_at/event_id, additive nullable schema; atomic full Gold refresh từng bảng, foreachBatch retry phục hồi giữa Silver/Gold. FileLock một writer/namespace. forecasting/features,model: timestamp joins/purge70/15/15/validation/test/persistence/availability. dashboard.py: API provision và chart_uuids cho native import. operations.py/cli.py unified commands; observability/benchmark.py+processing/experiments.py đo thật. scripts/export_presentation_snippets.py và verify_repository.py đã chạy.

## Quyết định và giới hạn

Gold/ML dùng source /hours mean đã kiểm contract; không average raw cadence5min vì reported interval1h vật lý chưa rõ. Missing/invalid null, UTC lưu/VN hiển thị, daily count/24/windowbins; hai trạm không đại diện Hà Nội. Backtest final snapshot không giả historical ingestion availability. RF không thắng baseline nhất quán. Local single-node không HA, benchmark nhỏ có cache/HTTP overhead.

## Trạng thái vận hành / tiếp tục

8daemons đã resume sau test cuối:7Docker healthchecks pass, catalogHTTP200, init exited0. Collector/processor continuous đã resume sau jobs, Silver duplicate0. Không còn Spark job dài. Docker RAM khoảng7,46GiB: dừng processor trước train/test integration/benchmark riêng, sau đó start --services processor --no-build. Không writer live thứ hai. Khi backfill API nặng trên host, pause Collector container vì SQLite limiter Linux riêng; resume sau đó. Predict theo lần gọi, source stale thì suppress, không đổi issued_at để ép forecast.

CLI: inspect/backfill/live/replay/profile/start/stop/status/query/drain/process/smoke/dashboard/train/predict/test/benchmark. Lệnh và demo trong README/labs/docs/demo.md. .env secrets local ignored; không dump Compose config. Người dùng đã cho phép sửa Docker socket ngoài repo, đã sửa trước đó và engine hoạt động; không sửa lại/xóa volumes. Stop giữ dữ liệu. Source/model/auth/raw logs không ở Git. Final-verification.json giữ source SHA256 và checks; reports cũ ghi revision/dirty đúng lúc chạy, không thay hash quá khứ bằng commit tương lai.

[Nhật ký](AGENT_WORK_LOG.md), [kế hoạch](../IMPLEMENTATION_PLAN.md), [báo cáo](../artifacts/README.md), [demo](demo.md), [thuyết trình](presentation-guide.md). Kiểm Git/process/artifact thực tế trước khi tin status; cập nhật context tại chỗ, log append-only sau checkpoint.
