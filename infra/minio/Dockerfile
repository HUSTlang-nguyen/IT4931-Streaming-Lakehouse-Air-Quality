# MinIO community hiện source-only; không đổi object store sang sản phẩm khác.
# Release chính thức RELEASE.2025-10-15T17-29-55Z, commit immutable bên dưới.
# Build Go chỉ dành cho dependency MinIO; logic ứng dụng vẫn là Python.
FROM golang:1.24.9-bookworm@sha256:737b40b61ce956d738bed59f18ba854d8d67e7a4c4fa63f64437f4c70247ac5b AS build
ENV CGO_ENABLED=0 GOTOOLCHAIN=local GOMAXPROCS=2
RUN go install github.com/minio/minio@9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a \
    && cp /go/pkg/mod/github.com/minio/minio@*/LICENSE /tmp/minio.LICENSE

FROM python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1
LABEL org.opencontainers.image.source="https://github.com/minio/minio" \
      org.opencontainers.image.revision="9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a" \
      org.opencontainers.image.licenses="AGPL-3.0-only"
COPY --from=build /go/bin/minio /usr/local/bin/minio
COPY --from=build /tmp/minio.LICENSE /usr/share/licenses/minio/LICENSE
RUN useradd --uid 10001 --create-home minio \
    && mkdir /data && chown minio:minio /data
USER minio
EXPOSE 9000 9001
HEALTHCHECK --interval=10s --timeout=5s --retries=12 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/minio/health/live', timeout=3)"
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--address", ":9000", "--console-address", ":9001"]
