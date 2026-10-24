# Cấu hình

**Đã có:** [Settings/Sensor](settings.py), defaults và nạp env. Chưa có cấu hình stack được kiểm chứng.

Nạp/kiểm tra cấu hình từ môi trường, defaults và secrets đã che. Chưa có loader; `.env.example` chỉ là template dự kiến.

**I/O dự kiến:** Cấu hình đầu vào → đối tượng cấu hình hợp lệ hoặc lỗi rõ nguyên nhân.

`Settings.from_env` chỉ đọc file được chỉ định, không ghi đè env có sẵn. Key được che khỏi repr; chỉ `require_api_key` của lệnh API mới yêu cầu key. Endpoint bị giới hạn chính thức để tránh gửi nhầm secret. Xem [lab OpenAQ](../../../labs/01-openaq.md).
