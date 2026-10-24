# Lab 03 — Kafka → Bronze → Silver, ACK và MERGE

## Mục tiêu/prerequisite

Hoàn thành Lab01/02; Docker Desktop chạy, khoảng 8GiB RAM engine và đủ disk cho image/build cache. Python host chỉ làm Collector/điều khiển; Spark chạy trong container Python3.11/Java17/Spark3.5.6/Iceberg1.9.2. Lần build đầu tải dependency nên lâu hơn các lần sau.

## Dựng và chứng minh kết nối thật

```powershell
.venv/Scripts/python.exe -m air_quality.cli start --services kafka minio catalog postgres trino superset
.venv/Scripts/python.exe -m air_quality.cli smoke
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT * FROM iceberg.validation.smoke'
```

`start` tạo credential thiếu vào `.env` và không đổi secret đang bảo vệ volume. `catalog-init` gán owner1000 cho đúng volume catalog mới; server không chạy root. PostgreSQL giữ metadata Superset, SQLite persist volume giữ REST catalog. MinIO giữ data/manifest/metadata Iceberg. Không xóa volume để chữa lỗi.

Smoke ghi một hàng bằng Spark và đọc lại bằng Trino; chỉ import package hoặc container xanh không đủ chứng minh cùng catalog. [Report smoke](../artifacts/reports/spark-smoke.json), [reconciliation lịch sử](../artifacts/reports/lakehouse-history-reconciliation.json).

## Đưa dữ liệu thật đã thu qua Kafka

Sau khi có `data/history-180d.jsonl` từ backfill:

```powershell
.venv/Scripts/python.exe -m air_quality.cli drain --input data/history-180d.jsonl --run-name history-to-kafka
.venv/Scripts/python.exe -m air_quality.cli process
```

`drain` giữ mode backfill/ingested_at/event_id của lần thu, không gọi API lần nữa và không giả là cảm biến đang live. ACK toàn lô mới checkpoint. Lệnh `replay` khác: topic/namespace replay riêng và nhãn replay.

`process` là Structured Streaming availableNow, từ earliest nếu chưa có checkpoint, chia micro-batch rồi dừng khi bắt kịp. Nếu processor continuous đang chạy, không chạy writer thứ hai cho live; dừng đúng service processor bằng Compose project trước hoặc dùng namespace replay riêng cho thí nghiệm.

## Đọc code theo luồng

1. [parse_kafka](../src/air_quality/processing/transforms.py): envelope v1, giữ message sai schema/mode trong dead-letter.
2. [process_events](../src/air_quality/processing/tables.py): Bronze trước; chuẩn hóa; reject bản ghi không có key; Silver; Gold refresh.
3. [normalize](../src/air_quality/processing/transforms.py): UTC, unit micro Unicode, value/period/metadata/source flags. Không đổi đơn vị số học hay zero-fill.
4. [merge_silver](../src/air_quality/processing/tables.py): key `(sensor_id,series_kind,period_start,period_end)`; observation mới hơn theo ingested_at, event_id tie-break mới được thay.

Bronze key là event_id, khác business key Silver. Bản nguồn sửa value có event_id mới nhưng cùng key Silver; raw cũ vẫn truy được ở Bronze. Invalid correction thay valid cũ sẽ làm Gold null, không để lại số hợp lệ cũ gây hiểu nhầm.

## Kết quả đã kiểm chứng

202.041 bản ghi nguồn đã đi qua Kafka → Structured Streaming → Iceberg; Trino đối chiếu Bronze/Silver đúng từng sensor/resource. Đây là snapshot lịch sử trước live; bảng live hiện có thể tăng, vì vậy report gắn snapshot IDs và time travel count thay vì ép số hiện tại bằng số cũ.

```powershell
.venv/Scripts/python.exe -m air_quality.cli test --integration
```

Sáu test Spark/Iceberg thật kiểm duplicate/correction cũ-mới, late data/gap, invalid correction, missing period/rejected, timezone/unit và replay lọt topic live. Namespace replay_test_* tách dữ liệu thật. Test đầu từng phát hiện fixture dùng offset nondeterministic bị Catalyst từ chối MERGE; fixture đã sửa thành offset dữ liệu cố định như Kafka thật.

## Chẩn đoán/bài tập

- Connection refused/UnknownHost catalog khi nó crash: xem owner/health và HTTP readiness, không reset volume hoặc retry job vô hạn.
- Job bị lock: xem processor thực sự còn sống; không xóa lock của writer đang chạy.
- Giải thích crash sau Silver trước Gold: Kafka checkpoint chưa tiến, retry MERGE không nhân đôi và Gold được tái tính.
- Bài tập: đọc report snapshot, truy vấn một snapshot Silver cũ qua Trino rồi so hiện tại. Không expire snapshot làm mất bằng chứng.
