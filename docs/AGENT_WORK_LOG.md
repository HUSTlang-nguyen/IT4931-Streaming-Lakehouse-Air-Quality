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
