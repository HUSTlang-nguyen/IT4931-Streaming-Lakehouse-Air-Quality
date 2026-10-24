# Lab 05 — Trino và dashboard Superset tái tạo được

## Mục tiêu/prerequisite

Có stack và Gold từ Lab03/04. Không cần viết frontend riêng; cấu hình dashboard được provision bằng Python API và export native YAML.

```powershell
.venv/Scripts/python.exe -m air_quality.cli dashboard
```

Mở `http://localhost:18088/superset/dashboard/air-quality-hanoi/`. Username/password ở `.env` cục bộ: SUPERSET_ADMIN_USERNAME/SUPERSET_ADMIN_PASSWORD; không đưa lên slide, log hoặc Git. [dashboard.py](../src/air_quality/dashboard.py) chỉ gửi admin secret tới localhost đã chọn, giữ JWT/CSRF trong session và không log chúng.

## Các panel đã có

- PM2.5/PM10, hai trạm, rolling7ngày tới hiện tại; nhãn giờ Việt Nam từ SQL, không phụ thuộc timezone browser.
- Độ phủ giờ trên toàn cửa sổ đã thu, với count và mẫu số.
- Độ mới theo từng sensor và raw/hourly, không lấy mốc mới nhất cấp trạm thay mọi chỉ số.
- Backtest dùng Gold left-grid, null khi thiếu features; model metrics RF/persistence cùng test mẫu và bảng operational issued/target/actual.
- Mean ngày Việt Nam, số giờ hợp lệ/kỳ vọng và độ phủ; số được format dễ đọc, không in tên trường kỹ thuật cho người dùng.

Null của hourly grid giữ khoảng trống trên line, không điền0. Header ghi nguồn OpenAQ/upstream, đơn vị và giới hạn ngày hiện tại chưa đủ24giờ. Auto-refresh60giây; dữ liệu mới vẫn phụ thuộc cadence/độ trễ nguồn.

## Tái tạo và export/import

Provision tìm theo tên/slug của project, chạy lại không nhân dashboard/chart. Dataset SQL/formData và layout ở code; [spec](../dashboards/air-quality-spec.json) không chứa ID/credentials. [Native export](../dashboards/export/metadata.yaml) có UUID và cấu hình Superset; ZIP native tương ứng ở output/playwright/dashboard-native.zip bị gitignore.

API import_native trong dashboard.py đã chạy thành công với ZIP xuất từ stack này, overwrite theo UUID. Có thể import ZIP bằng Superset UI ở stack local khác sau khi tạo kết nối phù hợp. Không dùng ZIP nếu scan phát hiện secret; exporter kiểm credential thực tế trước khi ghi YAML/ZIP và chặn path vượt thư mục đích.

## Bằng chứng và bài tập

Playwright browser đã render cả8panel; tất cả /api/v1/chart/data trả200, xem screenshot local output/playwright/dashboard-final.png. Đây là kiểm chứng UI thực, khác việc chỉ tạo object qua API. Native export/import cũng đã chạy; ML panels có backtest/actual, RF/persistence metrics và2forecast operational thật; forecast actual chưa tới giữ null.

Bài tập: so tuổi dữ liệu raw và hours tại cùng trạm, rồi giải thích vì sao hours có thể chậm hơn raw. Mở một ngày có ít giờ hợp lệ; không diễn giải mean ngày đó như full24giờ. Nếu chart lỗi, xem API chart/data/Trino query trước khi chỉnh màu hoặc điền dữ liệu.
