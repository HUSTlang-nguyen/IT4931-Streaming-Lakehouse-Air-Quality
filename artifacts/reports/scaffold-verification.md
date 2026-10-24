# Kiểm chứng scaffold

- Thời gian: `2026-10-24T11:10:47+07:00`.
- Branch: `chore/project-scaffold`; commit nền: `f64e464c04310d0d97ebe60bada7139096875458`.
- Working tree: thay đổi scaffold chưa commit; báo cáo này mô tả kiểm tra trên các file chuẩn bị.
- Python kiểm tra: `3.13.12`. Không chứng minh runtime Spark tương thích.
- Phương pháp: trình kiểm tra Python tạm thời qua stdin (stdlib AST/importlib/tomllib/pathlib/hashlib/regex) và Git check-ignore/status/remote. Không thêm test nghiệp vụ giả.
- Tổng: **36 kiểm tra đạt**.

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Required documents | PASS | 13 files present |
| Directory responsibilities | PASS | 20 directories have README |
| Package metadata | PASS | Valid TOML; src discovery; no unverified runtime dependencies |
| Package air_quality | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.config | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.contracts | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.collector | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.processing | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.forecasting | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Package air_quality.observability | PASS | Imports successfully; only descriptive docstring, no fake business API |
| Markdown local links | PASS | 70 local links resolve inside repository; 0 broken |
| Original preserved Air_Quality_Topic_Proposal.md | PASS | Source SHA-256 still equals recorded copy-time digest |
| Original preserved Air_Quality_Slides_Outline.md | PASS | Source SHA-256 still equals recorded copy-time digest |
| Proposal ML synchronization | PASS | ML in scope, original sample count preserved, no model success claimed |
| Outline content preserved | PASS | Copied text, only normalized UTF-8/newlines |
| Environment template | PASS | API key empty; proposed defaults only |
| Secret scan | PASS | 0 private-key/token/API-key-value matches; values never printed |
| Ignore .env | PASS | Ignored without creating secret/data files |
| Ignore .env.local | PASS | Ignored without creating secret/data files |
| Ignore data/raw.json | PASS | Ignored without creating secret/data files |
| Ignore models/model.bin | PASS | Ignored without creating secret/data files |
| Ignore checkpoints/offset | PASS | Ignored without creating secret/data files |
| Ignore volumes/pg/data | PASS | Ignored without creating secret/data files |
| Ignore logs/run.log | PASS | Ignored without creating secret/data files |
| Ignore .venv/pyvenv.cfg | PASS | Ignored without creating secret/data files |
| Ignore src/air_quality/__pycache__/x.pyc | PASS | Ignored without creating secret/data files |
| Ignore artifacts/raw.json | PASS | Ignored without creating secret/data files |
| Ignore artifacts/reports/model.bin | PASS | Ignored without creating secret/data files |
| Allow .env.example | PASS | Not ignored; content still requires review |
| Allow artifacts/README.md | PASS | Not ignored; content still requires review |
| Allow artifacts/reports/scaffold-verification.md | PASS | Not ignored; content still requires review |
| Allow artifacts/reports/metrics.json | PASS | Not ignored; content still requires review |
| Allow tests/fixtures/example.json | PASS | Not ignored; content still requires review |
| Allow pyproject.toml | PASS | Not ignored; content still requires review |
| Git target | PASS | Correct existing repository, branch and remote |
| No business runtime started by scaffold | PASS | No Compose or fake passing tests created; this does not assert external Docker state |

## Giới hạn

Không cài hoặc khóa dependency, không build wheel, không chạy pytest (chưa có test), không gọi OpenAQ, không start Docker, không train ML, không tạo dashboard hoặc Goal. Regex secret scan chỉ là kiểm tra mẫu phổ biến, không phải bảo đảm tuyệt đối. Links HTTP và fragment anchors không được kiểm tra mạng ở lượt scaffold. Git diff --check và kết quả commit/push được ghi tiếp trong nhật ký.

## Kiểm tra bổ sung trước commit

- `2026-10-24T11:11:40+07:00`: `git diff --cached --check` exit 0 sau khi đổi hardbreak của bản sao báo cáo sang backslash Markdown; thêm `.gitattributes` cho LF ổn định. Đây là kiểm tra bổ sung ngoài 36 mục ở trên.
- Đã xem staged stat/danh sách file: chỉ scaffold và tài liệu. Chưa commit/push tại thời điểm ghi mục này.
