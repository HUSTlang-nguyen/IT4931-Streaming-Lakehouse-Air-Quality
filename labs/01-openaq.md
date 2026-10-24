# Lab 01 — Đọc một measurement và chuỗi giờ OpenAQ

## Mục tiêu và prerequisite

Hiểu location → sensor → measurement, thời gian đo khác thời gian thu thập, và raw khác hourly nguồn. Cần Python >=3.10, truy cập mạng và API key của bạn. Runtime Spark chưa được chốt; lab này chỉ dùng Collector Python.

## Chuẩn bị trên PowerShell

Chạy tại Git root. Không ghi API key vào lệnh được chia sẻ/slide/log.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
```

Mở `.env` cục bộ và điền `OPENAQ_API_KEY`. File này bị gitignore. Env hiện có ưu tiên hơn `.env`. `Settings.require_api_key` báo lỗi nếu key trống; các lệnh help và tests offline không cần key.

## Kiến thức và luồng

```text
Sensor đã chọn → OpenAQ /measurements hoặc /hours
             → metadata + envelope chứa raw_payload
             → data/raw/<job>/page-N.json → JSONL local + SQLite checkpoint
```

Một hàng chỉ có một chất. `period.datetimeFrom/To` mô tả khoảng đo do nguồn báo; `ingested_at` là lúc Collector tải. Raw mẫu có interval một giờ nhưng timestamp cách nhau 5 phút, vì vậy không tự tính trung bình raw như các quan trắc tức thời độc lập.

Theo [tài liệu nguồn](https://docs.openaq.org/resources/measurements), `/hours` là mean do OpenAQ cung cấp. Pipeline giữ series này riêng để định nghĩa target ML: **PM2.5 trung bình giờ theo OpenAQ**, không tuyên bố đã giải thích được cơ chế vật lý của cảm biến. Coverage nguồn có thể trên 100%; giữ nguyên raw, không coi đó là chứng nhận độ đầy đủ.

## Chạy đúng code production

```powershell
.venv/Scripts/python.exe -m air_quality.cli inspect --sensor 13502154 --resource hours --start 2026-10-23T00:00:00Z --end 2026-10-23T06:00:00Z --run-name lab01-hours
```

`inspect` mặc định ghi JSONL, chưa cần Kafka. Cấu hình đi qua [settings.py](../src/air_quality/config/settings.py); HTTP dùng [OpenAQClient.get](../src/air_quality/collector/openaq.py); envelope dùng [make_event](../src/air_quality/contracts/events.py).

## Kết quả và kiểm tra

Trong lần kiểm chứng 24/10/2026, truy vấn mẫu trên trả 6 hàng giờ; số lượng ở nguồn có thể thay đổi do correction. Terminal chỉ in job/sensor/resource/from/to/count, không key. Xem `data/reports/inspect-latest.json` và raw archive để đối chiếu period, value, summary, coverage, location_metadata.

Chạy lại cùng lệnh: `published_this_call=0` nếu job trước đã hoàn tất. Thay run-name nếu muốn một lượt quan sát mới. Test hợp đồng nguồn chủ động gọi mạng:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_openaq_live.py --run-live -q --basetemp=artifacts/local/lab01-live
```

## Lỗi thường gặp

- 401/403: kiểm tra key/account; không lặp vô hạn. Key không được in trong error.
- 429: Collector chờ Retry-After và xin budget mỗi retry; không chạy script bỏ limiter song song.
- Job đang chạy: FileLock báo timeout. Không xóa checkpoint/lock để vượt một process còn sống; xem trạng thái process trước.
- Timestamp thiếu Z/offset bị từ chối để tránh lệch UTC+7.
- Zero rows: là phát hiện nguồn, không điền bằng zero hay tạo số đo giả.

## Bài tập

Lấy raw của cùng sensor trong một giờ bằng `--resource measurements` với run-name mới. So `period.interval`, khoảng cách `datetimeTo`, value và `summary` với `/hours`. Giải thích vì sao Silver cần `series_kind` trong khóa và vì sao không lấy coverage metadata làm kết luận chất lượng.
