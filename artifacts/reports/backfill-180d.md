# Backfill nguồn 180 ngày

- Ghi nhận: `2026-10-24T15:49:35+07:00`; nền code `301ab9ebb934ff4ff6644c6f92adb43ac40880ad` và các thay đổi profiler chưa commit lúc đo.
- Run: `hanoi-180d-20261024`, start exclusive 2026-04-27T00:00:00Z, end inclusive 2026-10-24T00:00:00Z.
- Process 21843 đã exit 0; raw + source hourly của bốn sensor, tổng **202,041** bản ghi duy nhất, duplicate/outside-range bằng 0 trong file lịch sử đã thu.
- Đây là source/profile count, chưa có Silver/Iceberg để xác nhận E2E. Raw/key/model không commit. [Số liệu máy đọc](source-coverage.json).

| Sensor | Chỉ số | Bin giờ có nguồn | Availability trên 4.320 giờ |
|---|---|---:|---:|
| 13502151 | pm25 | 4042 | 93.565% |
| 13502152 | pm10 | 4060 | 93.981% |
| 13502153 | pm10 | 4037 | 93.449% |
| 13502154 | pm25 | 3957 | 91.597% |

Các series có gap nội bộ tối đa 87 giờ đối với hourly; raw gap tối đa 315.900 giây. Bốn sensor không có invalid theo kiểm tra value/unit/period hoặc hasFlags trong mẫu tải này. Không chứng nhận độ chính xác cảm biến. Nhiều coverage nguồn >100%; không dùng tỷ lệ đó làm availability. Không tính tỷ lệ raw với giả định interval một giờ hoặc cadence năm phút như xác nhận chất lượng.

## Tái lập profiler offline

```powershell
.venv/Scripts/python.exe -m air_quality.cli profile --input data/history-180d.jsonl --start 2026-04-27T00:00:00Z --end 2026-10-24T00:00:00Z --output artifacts/reports/source-coverage.json
```

Profiler production đọc JSONL streaming, dedup sensor/resource/period và latest observation, loại replay khỏi source report. 20 unit tests đã pass sau khi thêm ba test coverage: dedup/correction/biên/gap, invalid/flags, và replay isolation. Test này không thay thế đối chiếu Spark sau khi triển khai.
