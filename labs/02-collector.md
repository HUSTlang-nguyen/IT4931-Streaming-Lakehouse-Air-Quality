# Lab 02 — Thu thập, ACK và tiếp tục sau gián đoạn

## Mục tiêu/prerequisite

Hoàn thành [Lab 01](01-openaq.md), có Python/env/key. Học checkpoint, pagination và ranh giới ACK bằng code production. Phần JSONL đã chạy; phần Kafka còn chờ stack local được kiểm chứng.

## Đọc luồng trước khi chạy

Trong [Collector.collect_window](../src/air_quality/collector/service.py):

1. Hash run/sensor/resource/khoảng/sink thành job ID. File sink và Kafka sink tách checkpoint để capture offline không vô tình đánh dấu đã gửi Kafka.
2. Lấy location metadata, kiểm tra sensor/parameter; đọc `next_page` SQLite.
3. Nếu raw page archive có, dùng lại đúng envelope; nếu chưa, gọi API rồi ghi file tạm + fsync + replace.
4. Publish toàn trang và đợi ACK. Nếu có lỗi, không tăng tiến độ.
5. Commit `next_page` và số dòng ACK. Crash giữa ACK/SQLite có thể gửi lại, vì vậy downstream vẫn phải idempotent.

`meta.found` có thể là `>1000`. Service dừng theo trang ngắn/rỗng; trang lặp bất thường gây lỗi thay vì vòng lặp. Event ID ổn định khi retry trang khác business key Silver.

## Backfill có mốc cố định

```powershell
.venv/Scripts/python.exe -m air_quality.cli backfill --start 2026-10-22T00:00:00Z --end 2026-10-23T00:00:00Z --sensor 13502154 --sink jsonl --output data/lab02.jsonl --run-name lab02-day
```

Mặc định lấy cả measurements và hours, cửa sổ tối đa 7 ngày, 1.000 rows/trang. Mốc run lưu SQLite; chạy lại cùng run-name resume thay vì trượt cửa sổ tới hiện tại. Cố đổi start/end cho run cũ sẽ bị từ chối. Backfill đầy đủ bỏ `--start` và `--sensor`, mặc định 180 ngày trước end; dung lượng và thời gian phụ thuộc nguồn.

## Kiểm chứng không dùng mạng

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/test_collector.py -q --basetemp=artifacts/local/lab02-unit
```

Test `test_crash_before_ack_reuses_archived_page` mô phỏng broker timeout sau khi nhận trang: SQLite còn trang 1, lần tiếp dùng cùng archive/ID rồi mới tiếp trang 2. Test `test_file_sink_does_not_poison_kafka_checkpoint` xác nhận capture file không chặn việc gửi Kafka sau này. SQLite restart test xác nhận request budget vẫn còn.

Không coi những test này là bằng chứng broker thật. `--basetemp` phải là thư mục test dùng riêng trong artifacts/local; pytest có thể dọn thư mục đó, không trỏ vào dữ liệu người dùng.

## Live và replay

Sau khi stack/Kafka đã được kiểm chứng, dùng `--sink kafka` (default của backfill/live). `live --once` chạy một chu kỳ rồi dừng; live không `--once` tiếp tục tới Ctrl+C. Chu kỳ đầu đối soát 7 ngày, sau đó overlap 24 giờ và định kỳ 24 giờ đối soát lại. Hiện lịch chờ 300 giây tính sau chu kỳ trước, nên chu kỳ thực phụ thuộc cả thời gian xử lý.

`replay --topic air-quality.replay.demo` đọc raw archive, gắn mode replay và giữ original_ingested_at; không được gửi vào topic live. Kafka được cấu hình qua `KAFKA_BOOTSTRAP_SERVERS`; broker local đã ACK 202.041 bản ghi nguồn khi drain lịch sử (xem Lab03).

## Chẩn đoán và bài tập

- Delivery timeout: sửa kết nối broker trước, checkpoint không tiến. Không coi fsync JSONL là Kafka ACK.
- DB/lock bận: chỉ chạy một Collector chính; các test live chia sẻ limiter SQLite nhưng không thay progress.
- Lịch sử có gap/correction: xem raw và báo cáo, đừng nhân count theo kỳ vọng để thay số thực tế.
- Bài tập: đọc test ACK failure, vẽ hai vị trí crash (trước ACK và sau ACK trước SQLite), giải thích tại sao cần cả checkpoint và downstream MERGE.

Collector container dùng SQLite volume Linux riêng để tránh Windows/Linux cùng mở DB. Khi backfill API nặng trên host, dừng service collector trước và mở lại sau; hai limiter không chia sẻ budget giữa hai filesystem. Drain/replay offline không gọi API.
