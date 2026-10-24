# MinIO source build đã kiểm chứng

- Thời gian `2026-10-24T15:53:08+07:00`; Docker engine28.4.0, Linux/amd64.
- Dockerfile infra/minio/Dockerfile; upstream release RELEASE.2025-10-15T17-29-55Z, source commit9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a.
- Go1.24.9 và Python3.11.13 base pin tag+manifest digest trong Dockerfile. Build lần đầu69048 exit0; rebuild sau pin Go digest cũng exit0, dùng cache.
- Image local `sha256:a8835691de731cd242e9246af0212b29e887164dfcf69615f6fd669fc01960e0`, size 115590900 bytes.
- `docker run --rm air-quality-minio:2025-10-15 --version` exit0, Runtime go1.24.9 linux/amd64, License GNU AGPLv3. Go install build hiển thị DEVELOPMENT.GOGET thay vì release version; source provenance dựa commit pin và build log, không giả binary tự báo release.
- License path /usr/share/licenses/minio/LICENSE có thật, kiểm tra bằng Python trong container.
- Chưa nghiệm thu S3 API/volume/health cùng REST catalog: sẽ kiểm khi Compose được dựng. Không có image đã pull từ mirror không rõ nguồn; không đổi object store.

## Tái lập

```powershell
docker build --progress plain -f infra/minio/Dockerfile -t air-quality-minio:2025-10-15 .
docker run --rm air-quality-minio:2025-10-15 --version
```

Build logs local bị gitignore: artifacts/local/minio-build.log và minio-build-pinned.log. Root dockerignore allowlist không gửi .env, data, checkpoint, Git hoặc .venv vào build context. [Upstream](https://github.com/minio/minio) và [release](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z).
