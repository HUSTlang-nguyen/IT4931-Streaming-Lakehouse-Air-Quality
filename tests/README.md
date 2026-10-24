# Chiến lược kiểm thử

**Trạng thái ban đầu:** scaffold.

Chưa có test; không coi scaffold import được là pipeline đã pass. Unit kiểm logic với fixture; integration kiểm ranh giới Kafka/Iceberg/Trino; live cần key và API thật. Chạy test offline mặc định không được tự gọi mạng, start Docker hoặc đọc key ngoài cấu hình chủ động.
