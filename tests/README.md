# Chiến lược kiểm thử

**Hiện có:** unit Collector/coverage và live hourly contract bốn sensor. Chưa có kiểm thử stack E2E.

Unit dùng MockTransport và SQLite/file thật để kiểm checkpoint/ACK, retry/pagination/timezone, replay isolation và source coverage. `pytest` mặc định skip live; cần bật `--run-live` để gọi OpenAQ thật. Marker `integration` sau này cần `--run-integration`. Dùng `--basetemp` ở thư mục test riêng trong artifacts/local khi sandbox không cho ghi temp hệ thống. Fixture/live không chứng minh Kafka/Iceberg E2E. Xem Lab 01/02.
