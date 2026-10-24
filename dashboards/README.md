# Superset dashboard

Python provision [dashboard.py](../src/air_quality/dashboard.py), source spec air-quality-spec.json, native YAML ở export/. Chạy CLI dashboard sau khi bảng tồn tại. Database URI nội bộ Trino không có password; admin credentials chỉ đọc .env local.

Native ZIP ở output/playwright/dashboard-native.zip ignored. import_native helper đọc ZIP và giữ UUID; export YAML cấu hình được theo dõi Git, không có secret. Xem [Lab05](../labs/05-dashboard.md) và bằng chứng reports/stack-dashboard-checkpoint.json.
