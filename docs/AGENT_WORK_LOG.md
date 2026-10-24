# Nhật ký agent theo thứ tự

Append-only. Ghi một STEP cho công việc có ý nghĩa; không ghi mọi lệnh đọc, suy luận nội bộ hay secret. Đính chính bằng STEP mới. Context là chỉ mục hiện tại; log này là lịch sử.

## Mẫu cho lần ghi tiếp theo

```markdown
## STEP-NNN — YYYY-MM-DDTHH:mm:ss+07:00 — Tên công việc

- Mục tiêu:
- Git: branch; commit nền; dirty state nếu liên quan.
- Đã thực hiện:
- File/hàm liên quan:
- Quyết định và lý do:
- Kiểm chứng: lệnh, kết quả, artifact hoặc chưa kiểm chứng.
- Trạng thái: hoàn thành / một phần / bị chặn.
- Vấn đề còn lại:
- Bước tiếp theo:
```

Hash commit mới ghi ở STEP sau, tránh tự tham chiếu hash chứa chính dòng đó. Timestamp dùng Asia/Ho_Chi_Minh (UTC+7).

## STEP-001 — 2026-10-24T11:09:59+07:00 — Khảo sát repository và phạm vi

- Mục tiêu: chuẩn bị Markdown và khung Python để người dùng chạy Goal sau.
- Git: main, commit nền `f64e464c04310d0d97ebe60bada7139096875458`, working tree sạch lúc khảo sát; origin đúng repository người dùng cung cấp.
- Đã thực hiện: xác nhận Git root là thư mục con, đọc README, báo cáo/dàn ý ngoài repository; chuyển sang `chore/project-scaffold`.
- File/hàm liên quan: README ban đầu, tài liệu đề xuất nguồn; chưa có hàm nghiệp vụ.
- Quyết định và lý do: giữ Git có sẵn, không init repository mới; không crawl/Docker/tạo Goal vì ngoài phạm vi lượt này.
- Kiểm chứng: `git status --short --branch`, `git remote -v`, `git log -1`; Python host 3.13.12, chưa phải runtime Spark đã kiểm chứng.
- Trạng thái: hoàn thành.
- Vấn đề còn lại: cần tạo scaffold và kiểm chứng trước commit/push.
- Bước tiếp theo: STEP-002.

## STEP-002 — 2026-10-24T11:09:59+07:00 — Tạo scaffold, prompt và tài liệu

- Mục tiêu: context bền vững, code structure rõ, prompt Goal độc lập.
- Git: `chore/project-scaffold`, nền `f64e464c04310d0d97ebe60bada7139096875458`; scaffold chưa commit.
- Đã thực hiện: package/docstrings, README trách nhiệm, env template/gitignore/pyproject; prompt và checklist; context/log/architecture/dictionary/walkthrough/presentation/lab outline; sao đề xuất và đồng bộ ML.
- File/hàm liên quan: `src/air_quality/` chỉ có __init__.py, chưa có function; root/docs/labs/infra/sql/dashboards/scripts/tests/artifacts chỉ scaffold.
- Quyết định và lý do: chưa pin runtime Spark khi chưa khảo sát; không giả public API/CLI/test; sửa link nguồn ngoài repo về provenance thay vì tạo link hỏng. Không sao slide/PDF hoặc cả lab gốc.
- Kiểm chứng: file đã được tạo; kiểm tra cấu trúc, links/config/secret và bản gốc giữ nguyên đang chờ STEP-003.
- Trạng thái: một phần, nội dung scaffold có nhưng chưa nghiệm thu.
- Vấn đề còn lại: xác minh, commit, push, cập nhật checkpoint.
- Bước tiếp theo: chạy kiểm tra phù hợp scaffold và lưu evidence.

## STEP-003 — 2026-10-24T11:11:40+07:00 — Kiểm chứng scaffold và chuẩn hóa Markdown

- Mục tiêu: nghiệm thu structure/tài liệu trước commit.
- Git: `chore/project-scaffold`, nền `f64e464c04310d0d97ebe60bada7139096875458`; thay đổi scaffold staged, chưa có commit mới.
- Đã thực hiện: 36 kiểm tra stdlib/Git cho file/thư mục, TOML/src import, links, nguồn nguyên vẹn, phạm vi ML, env/secret/ignore rules và đúng remote.
- File/hàm liên quan: `artifacts/reports/scaffold-verification.md`, `.gitattributes`; chưa có hàm nghiệp vụ.
- Quyết định và lý do: thêm LF policy cho text trên Windows; đổi Markdown hard break từ hai dấu cách cuối dòng sang backslash trong bản báo cáo sao để giữ hiển thị và pass diff check. Nguồn ngoài repo không sửa.
- Kiểm chứng: 36/36 kiểm tra đạt, 70 local links tồn tại; sau sửa hardbreak, `git diff --cached --check` exit 0. Xem stat/danh sách staged: chỉ scaffold/tài liệu, không secret/data/model.
- Trạng thái: hoàn thành phần xác minh scaffold.
- Vấn đề còn lại: chưa commit/push. Không build wheel, chạy pytest, Docker, API hoặc ML; các kiểm tra trên không chứng minh nghiệp vụ.
- Bước tiếp theo: commit scaffold, push branch và ghi Git checkpoint mới ở STEP-004.

## STEP-004 — 2026-10-24T11:12:28+07:00 — Commit và push scaffold lên GitHub

- Mục tiêu: bàn giao scaffold có version control và context để dùng Goal sau.
- Git: `chore/project-scaffold`, checkpoint mới `763b31a19faf95e8a376eba2d87ce5fe389b6376`; origin tracking cùng hash ngay sau push; working tree sạch trước lượt cập nhật log/context này.
- Đã thực hiện: commit `chore: prepare Python scaffold and persistent Goal context` (44 file); push `git push -u origin chore/project-scaffold`; không tạo PR/merge.
- File/hàm liên quan: toàn bộ scaffold, sau đó cập nhật P0/context/log ghi checkpoint; chưa có hàm nghiệp vụ.
- Quyết định và lý do: lưu hash commit scaffold ở bản cập nhật kế tiếp, không tự tham chiếu commit chứa hash của chính nó.
- Kiểm chứng: commit thành công; push trả new branch và thiết lập upstream; `git rev-parse HEAD` bằng `git rev-parse origin/chore/project-scaffold`, status sạch trước cập nhật tài liệu. Lần push trong sandbox lỗi DNS; retry với quyền mạng được duyệt đã thành công.
- Trạng thái: P0 hoàn thành; bản ghi checkpoint này sẽ commit/push tiếp bằng commit docs. Xem Git thực tế để biết hash tài liệu mới nhất.
- Vấn đề còn lại: P1–P6 chưa triển khai; interval semantics/API/runtime và ML vẫn cần kiểm chứng. Không có Goal/Docker/API/ML được khởi chạy trong lượt chuẩn bị.
- Bước tiếp theo: kiểm tra cuối và push commit docs; sau bàn giao chờ người dùng giao Goal, đọc context/plan/log rồi bắt đầu P1 trên nhánh triển khai từ scaffold.

## STEP-005 — 2026-10-24T15:40:39+07:00 — Bắt đầu Goal, khảo sát API và môi trường

- Git: tạo `feat/air-quality-lakehouse` từ `81ab9f2f0163a6cf600b1c56e66ae00a26d68faf`, scaffold có đủ. Người dùng đã giao Goal implement; không thu hẹp phạm vi.
- Đã đọc AGENTS/context/plan/log/GOAL_PROMPT và lab stock trong workspace cha. Xác nhận OpenAQ key cũ dùng được; cấu hình .env ignored, không log key.
- Phát hiện: /hours là series mean nguồn, raw interval/cadence chưa cùng ý nghĩa; giữ series riêng và dùng target nguồn có ghi rõ. Bốn live contract test đã pass sau sửa giả định lượng tử hóa value; coverage nguồn bất thường không được tin trực tiếp.
- Kiểm chứng: metadata + raw/hours payload ở data/discovery; report `artifacts/reports/collector-checkpoint.md`.
- Trạng thái: tiến triển P1; version matrix/runtime chưa kiểm chứng, chưa hoàn thành P1.
- Bước tiếp: Collector/P2 và backfill.

## STEP-006 — 2026-10-24T15:40:39+07:00 — Collector và kiểm thử có ACK/checkpoint

- Git: `feat/air-quality-lakehouse`, nền `81ab9f2f0163a6cf600b1c56e66ae00a26d68faf`, code chưa commit lúc ghi.
- Đã thực hiện: settings/env, UTC/envelope v1, retry/rate limiter SQLite, raw page archive, ACK/checkpoint, publishers JSONL/Kafka, CLI inspect/backfill/live/replay, lab01/02 và unit/live tests.
- Kiểm chứng: 17 unit passed; 4 live passed (không skip), pip editable build/install + pip check; inspect thật 6 hàng. Lỗi test tmpdir sandbox được giải quyết bằng basetemp trong artifacts/local. Lỗi marker nhầm tên thư mục và giả định rounding được sửa có bằng chứng.
- Backfill đang chạy: exec session `21843`, command/tiến độ trong artifacts/local/backfill.log và SQLite; không restart nếu process còn sống. Raw/data ignored; tổng row ACK chưa là Silver count.
- Quyết định: sink identity thuộc job ID để capture file không đánh dấu đã gửi Kafka; protocol interface không phải hàm nghiệp vụ giả.
- Trạng thái: Collector đã kiểm chứng file/API; Kafka chưa kiểm chứng broker thật. Goal còn toàn P2–P6.
- Bước tiếp: dựng broker/REST catalog/MinIO/Spark/Trino, đưa lịch sử đã thu qua Kafka.

## STEP-007 — 2026-10-24T15:40:39+07:00 — Sửa Docker runtime socket theo quyền người dùng

- Lỗi ban đầu: backend crashed initializing inference socket; CLI start/info đang chờ ở sessions 16316/15755. Không coi timeout quan sát là process đã chết.
- Người dùng xác nhận cho phép sửa riêng lỗi Docker ngoài repository. Dừng Desktop bằng CLI; unlink/reparse delete socket lỗi 1920. Sau kiểm tra absolute paths, sao lưu thư mục run trong cùng Docker root, tạo run sạch, start lại. Không sửa settings hoặc volumes/images.
- Kiểm chứng: start session 65016 exit 0; Docker engine 28.4.0, 16 CPU/RAM ~7,46 GiB; các session cũ 16316/15755 đã terminal, không còn chờ. Không có container chạy trước khi dựng dự án.
- Trạng thái: blocker Docker đã giải quyết; backup runtime sockets giữ nguyên.
- Bước tiếp: image tag/digest verification và Compose giới hạn RAM, tiếp tục Goal.

## STEP-008 — 2026-10-24T15:49:35+07:00 — Checkpoint GitHub và backfill nguồn hoàn tất

- Git: `feat/air-quality-lakehouse`, Collector commit `301ab9ebb934ff4ff6644c6f92adb43ac40880ad` đã push; draft PR https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/1 đã tạo/attach, chưa merge.
- Kiểm chứng: session backfill21843 exit0; profiler67325 exit0; 202.041 bản ghi nguồn duy nhất gồm raw/hours bốn sensor, không trùng khóa trong JSONL. 20 unit pass sau bổ sung profiler.
- File/hàm: observability/coverage.py (jsonl_events/profile_events), evidence.py, CLI profile; artifacts/reports/source-coverage.json và backfill-180d.md. Code profiler còn chưa commit lúc ghi STEP.
- Phát hiện: hourly availability 91,597–93,981% trên 4.320 bins, gap hourly tối đa87h. Coverage metadata nguồn không dùng làm chất lượng; không nhầm source count với Silver count.
- Trạng thái: thu thập nguồn180ngày và profile đã có bằng chứng; Kafka/stream/lưu trữ/ML vẫn chưa nghiệm thu.
- Bước tiếp: đưa source archive qua Kafka, đối chiếu Silver với profile; tiếp tục toàn Goal.

## STEP-009 — 2026-10-24T15:49:35+07:00 — MinIO source build để giữ kiến trúc

- Docker engine đã sẵn sàng sau STEP-007. Kiểm tra image tags/version, DockerHub MinIO và Quay tag thử đều401, không đổi sang object store khác.
- Đã đối chiếu README upstream source-only và GitHub release API: RELEASE.2025-10-15T17-29-55Z → commit9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a.
- File: infra/minio/Dockerfile, README, root .dockerignore allowlist. Build Go1.24.9 chỉ là dependency MinIO, Python application giữ nguyên. LICENSE được copy vào image.
- Tiến trình: session69048, `docker build --progress plain -f infra/minio/Dockerfile -t air-quality-minio:2025-10-15 .`, log artifacts/local/minio-build.log; đang download/compile khi ghi. Không restart khi handle còn sống.
- Trạng thái: build chưa có kết quả terminal; runtime compatibility chưa được khẳng định.
- Bước tiếp: poll build, xác nhận minio --version/health, viết Compose cùng Kafka/REST catalog/Trino/Spark/Superset.

## STEP-010 — 2026-10-24T15:53:08+07:00 — Xác minh source profiler và image MinIO

- Git nền301ab9e, draft PR#1 tiếp tục; code profiler và infra chuẩn bị commit riêng.
- Kiểm chứng: 21 unit pass/4 live skip ở lần offline mới nhất; 4 live pass riêng ở STEP-006. Thêm fixture bốn hàng public nguồn với attribution/provider/licenses, không auth header; fixture shape test offline gọi production make_event/profile_events.
- MinIO build69048 exit0, binary --version và license test exit0; pin thêm Go image digest và cached rebuild exit0. Image `sha256:a8835691de731cd242e9246af0212b29e887164dfcf69615f6fd669fc01960e0`, 115590900 bytes. Binary hiển thị DEVELOPMENT.GOGET, không tự báo tag release; provenance là source commit và build recipe.
- File: .dockerignore, infra/minio/Dockerfile/README, artifacts/reports/minio-source-build.md; profiler report và code như STEP-008. Chưa test S3/object persistence/catalog.
- Trạng thái: backfill nguồn/Collector đã có bằng chứng, dependency MinIO build đã có; toàn Goal vẫn active với P2–P6 còn việc. Các process dài trước đều terminal; không có process cần resume lúc ghi.
- Bước tiếp: commit/push các checkpoint rồi dựng Compose project riêng và Spark/Iceberg, xử lý dữ liệu thật đã thu qua Kafka.
