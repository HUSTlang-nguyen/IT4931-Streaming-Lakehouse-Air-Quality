# Demo tái lập

## Chuẩn bị

Docker Linux engine khoảng8GiB, cổng project không xung đột. Cài package host theo README, `.env` local có OpenAQ key. `start` sinh password ngẫu nhiên còn trống; không hiển thị key/password lên slide. Không down-v/prune.

## Luồng demo 8–10 phút khi lịch sử/model đã có

1. CLI `status`, mở Superset local. Giải thích hai trạm, PM2.5/PM10, UTC+7 và khoảng trống/null.
2. CLI `query 'SELECT * FROM iceberg.live.freshness'`; chỉ ra timestamp khác nhau của từng sensor/resource. Không tuyên bố tất cả sensor mới vì trạm mới.
3. Xem `source-coverage.json` và `lakehouse-history-reconciliation.json`:202.041 unique lịch sử và snapshot IDs. Bảng hiện tại live tăng bình thường, không ép count về số lịch sử.
4. Đọc lab03, hai hàm merge_silver/refresh_gold. Test correction/late riêng namespace, không đưa fixture vào live. `restart-persistence.json` cho counts trước/sau/resume bằng nhau và duplicate0.
5. Dashboard backtest so actual/RF/persistence, bảng MAE/RMSE. RF chưa thắng baseline nhất quán. Model snapshot/config/splits trong ml-evaluation.json.
6. Operational forecast: xem issued_at/target_time/mode. Dự báo phát hành bằng CLI predict khi source-hour mới. Nếu input stale, trình bày suppression thay vì đổi issue về quá khứ.
7. Benchmark report:28→7 files, pruning tháng7, exceptAll0, time travel count bằng nhau. Client timing không giảm; nêu scale nhỏ và caches.
8. Dẫn sáu đoạn code trong presentation-guide và nhật ký/context để giải thích agent đã làm gì, cách khôi phục sau compaction.

## Thu lịch sử từ máy mới

Làm trọn [SETUP](SETUP.md) thay vì dùng lại source/model/snapshot ID của máy tác giả. Hướng dẫn đó cố định bounds180ngày tròn giờ, tạo JSONL local, profile, drain/process tới khi kết thúc và đối chiếu Silver trước khi train. Git không chứa lịch sử/model/volumes đầy đủ. Sau khi có dữ liệu/model, quay lại luồng demo ở trên.

Không yêu cầu run mới bằng202.041 hàng hoặc cùng accuracy với báo cáo cũ. Khi dùng Spark job riêng trên máy8GiB, dừng processor trước, resume sau; không chạy writer live thứ hai.

## Replay lịch sử

`replay --topic air-quality.replay.demo` chỉ đọc archive public local và ghi mode replay. `process --namespace replay_demo --topic air-quality.replay.demo --checkpoint checkpoints/spark/replay_demo` xử lý tách biệt. Khi demo nhiều lần, MERGE bảo vệ khóa logic; không trộn replay/live hoặc gọi replay là sensor đang đo mới.

Native dashboard export YAML ở dashboards/export. ZIP ignored được tạo khi provision; Lab05 có import helper. Cần đúng database URI/cổng nội bộ ở stack mới. Model binaries, source archives, catalog/MinIO volumes nằm local, không có trong Git; Git chứa code/config/fixture nhỏ/báo cáo tái lập.
