# Checkpoint Collector và khảo sát nguồn

- Thời gian: `2026-10-24T15:40:39+07:00`. Branch `feat/air-quality-lakehouse`, nền `81ab9f2f0163a6cf600b1c56e66ae00a26d68faf`, working tree có implementation chưa commit tại lúc kiểm tra.
- Package Python editable đã build/cài thành công trong .venv Python 3.13.12; `pip check` sạch. Đây không phải runtime Spark.
- Offline: 17 passed, 4 live skipped theo chủ ý. Live riêng: 4 passed, 0 skip/fail/error. XML đầy đủ ở artifacts/local (ignored).

## Lệnh bằng chứng

```powershell
.venv/Scripts/python.exe -m pytest tests -q --basetemp=artifacts/local/pytest-collector-2 --junitxml=artifacts/local/tests-offline.xml
.venv/Scripts/python.exe -m pytest tests/integration/test_openaq_live.py --run-live -q --basetemp=artifacts/local/pytest-live-4 --junitxml=artifacts/local/tests-openaq-live.xml
.venv/Scripts/python.exe -m air_quality.cli inspect --sensor 13502154 --resource hours --start 2026-10-23T00:00:00Z --end 2026-10-23T06:00:00Z --run-name source-hours-check
```

Inspect thực tế ACK 6 hàng vào JSONL. Backfill 180 ngày cố định `[2026-04-27T00:00:00Z, 2026-10-24T00:00:00Z]`, run `hanoi-180d-20261024`, hai resource/bốn sensor đang chạy; chưa kết luận tổng độ phủ. Snapshot SQLite lúc ghi: 171 job, 174606 hàng ACK lũy kế (bao gồm inspect), 171 job done. Đây không phải số bản ghi Silver duy nhất.

## Phát hiện làm thay đổi thiết kế

- API key đã cấp trước đó còn dùng được; chỉ lưu .env local bị gitignore, không ghi key vào báo cáo/repo.
- Raw có khoảng báo một giờ nhưng timestamp cách 5 phút; giữ nguyên. Theo [OpenAQ measurements](https://docs.openaq.org/resources/measurements), /hours là chuỗi mean nguồn. Target/Gold chọn series này riêng, không diễn giải raw thành số đo tức thời hoặc độc lập.
- Qua live tests bốn sensor: hour boundary/parameter/uniqueness hợp lệ, value được lượng tử hóa ba chữ số có nghĩa so với summary.avg. Nửa chữ số cuối cho phép quy tắc midpoint khác Python (82.05 thành 82.1). Các test đầu đã bắt lỗi giả định hai số thập phân; không thay value nguồn để qua test.
- Coverage metadata raw có thể >100%; không dùng làm coverage phân tích. series_kind phải tham gia khóa Silver để raw và hourly không đè nhau.
- Pagination meta.found là số hoặc chuỗi >N; dừng theo trang ngắn/rỗng. File/Kafka có checkpoint riêng; toàn trang phải ACK trước tiến độ.
- [Hạn mức nguồn](https://docs.openaq.org/using-the-api/rate-limits): 60/phút, 2.000/giờ; limiter SQLite bảo thủ 2,1s và 1.800/h, chia sẻ với các test live.

## Môi trường và Docker

Host RAM khoảng 15,4 GiB, D còn khoảng 98 GiB ở khảo sát. Docker engine 28.4.0 đã xác nhận sau sửa; engine có 16 CPU và 8.011.026.432 byte RAM. Không có container đang chạy ở lúc kiểm tra.

Docker ban đầu crashed ở socket dockerInference. Sau xác nhận của người dùng, dừng Desktop, thử unlink/reparse delete đều lỗi 1920. Sao lưu đúng thư mục runtime sockets thành `%LOCALAPPDATA%/Docker/run.before-air-quality-20261024`, tạo lại run rồi khởi động thành công. Giữ nguyên settings/images/volumes; không xóa backup.

## Giới hạn

Chưa có broker/Kafka ACK thật, Spark/Iceberg/Trino/Superset/ML. Chưa khóa matrix runtime hoặc kết luận toàn lịch sử đủ. Live test chỉ chứng minh hợp đồng nguồn hiện tại, không độ chính xác cảm biến. Goal vẫn active.
