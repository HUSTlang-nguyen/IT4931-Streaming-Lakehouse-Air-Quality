# MinIO từ source pin

DockerHub `minio/minio` và tag Quay thử trong lượt khảo sát trả 401. [MinIO upstream](https://github.com/minio/minio) hướng dẫn source-only. Không thay MinIO bằng object store khác để né yêu cầu đồ án.

Dockerfile build source của release [RELEASE.2025-10-15T17-29-55Z](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z), commit `9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a`, Go 1.24.9; giữ LICENSE trong image. Python base chỉ phục vụ healthcheck. Ứng dụng vẫn viết Python/PySpark.

Build và binary --version đã được kiểm chứng; xem [báo cáo](../../artifacts/reports/minio-source-build.md). S3/volume/catalog compatibility vẫn chờ Compose. Binary Go install hiển thị DEVELOPMENT.GOGET; source pin trong Dockerfile là provenance thực tế. Không yêu cầu người dùng cài Go trên host. Root `.dockerignore` chỉ cho mã/config cần thiết vào context, loại dữ liệu/key/venv.
