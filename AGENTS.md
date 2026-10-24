# Hướng dẫn agent

## Khôi phục context

1. Xác định Git root, branch, remote và thay đổi chưa commit; giữ nguyên công việc của người dùng.
2. Đọc `docs/IMPLEMENTATION_CONTEXT.md`, `IMPLEMENTATION_PLAN.md`, rồi các STEP sau mốc đã đồng bộ trong `docs/AGENT_WORK_LOG.md`. Đọc lịch sử trước đó khi cần quyết định liên quan.
3. Đối chiếu code và bằng chứng thực tế trước khi tin trạng thái Markdown. Context là chỉ mục, không thay cho kiểm chứng.
4. Nếu lượt trước bị gián đoạn, kiểm tra diff/commit/artifact rồi thêm STEP khôi phục; không đoán việc đã xong.

## Phạm vi

Goal triển khai đã được người dùng khởi động ngày 24/10/2026. Đọc `GOAL_PROMPT.md` làm hợp đồng phạm vi. Collector đã có; stack/ML còn triển khai. Không suy ra hoàn thành từ scaffold hoặc unit tests. Dependency host đã cài, runtime Spark chưa kiểm chứng.

## Python và cách giải thích

- Python cho ứng dụng/CLI/pytest, PySpark và Spark MLlib cho xử lý/ML; SQL/YAML/Dockerfile đúng vai trò.
- Tên module/hàm/biến bằng tiếng Anh rõ nghĩa, có type hints; comment/docstring/lab bằng tiếng Việt.
- Hàm một trách nhiệm, tách biến đổi khỏi API/Kafka/storage I/O. Không áp giới hạn dòng máy móc hoặc abstraction thừa.
- Mỗi module mô tả vai trò trong pipeline, đầu vào/đầu ra. Hàm nghiệp vụ mô tả tham số, kết quả, side effect/lỗi và ví dụ khi hữu ích.
- Logic khó có comment từng bước giải thích vì sao, giả định, đánh đổi và edge case: pagination/retry, dedup/late data, khoảng đo, features/leakage. Không chú thích lại từng phép gán đơn giản.
- Script/lab gọi lại package `src`, không sao chép nghiệp vụ. Không tạo hàm giả `pass`/`NotImplementedError` để làm đầy cấu trúc.
- Không nuốt lỗi bằng `except` chung. Log không chứa secret.

## Bộ nhớ bền vững

- `IMPLEMENTATION_PLAN.md`: checklist; chỉ đánh dấu với bằng chứng.
- `docs/AGENT_WORK_LOG.md`: append-only, một STEP cho một công việc có ý nghĩa; ghi kết quả, quyết định, bằng chứng và bước tiếp theo. Không ghi suy luận nội bộ, secret hoặc mọi lệnh đọc file.
- `docs/IMPLEMENTATION_CONTEXT.md`: cập nhật tại chỗ khi kiến trúc, trạng thái, blocker hoặc bước tiếp theo đổi; tách dự kiến/đã code/đã kiểm chứng.
- Ghi log rồi đồng bộ context sau mỗi mốc và trước bàn giao. Đính chính bằng STEP mới, không xóa lịch sử.
- STEP ghi branch và commit nền. Hash commit vừa tạo được ghi lần cập nhật kế tiếp; không cố ghi hash của commit chứa chính dòng đó.

## Git workflow

- Dùng Git root/remote hiện tại; không tạo repository lồng nhau.
- Scaffold ở `chore/project-scaffold`; triển khai trên `feat/air-quality-lakehouse` từ commit có đủ scaffold. Không giả định scaffold đã ở `main`.
- Commit nhỏ theo `feat:`, `fix:`, `test:`, `docs:`, `chore:`; xem diff, check secret/test phù hợp rồi stage đúng file liên quan.
- Khi Goal được giao, push checkpoint và tạo draft PR theo prompt. Lượt scaffold chỉ commit/push, chưa tạo PR.
- Không tự merge, force-push, xóa branch, reset phá thay đổi hoặc rewrite lịch sử đã push. Không mua cloud, xóa volume hay sửa dịch vụ ngoài dự án.
- Không commit `.env`, credentials, crawl lớn, model binary, volumes, cache, raw logs. Theo dõi env example, fixture nhỏ, lock, dashboard config và báo cáo nhỏ đã làm sạch.

## Kiểm chứng và giao tiếp

Chạy kiểm tra đúng phạm vi. Ghi lệnh, kết quả, phiên bản code và giới hạn. Fixture không chứng minh live, backtest không phải operational forecast. Không tuyên bố pipeline/ML hoàn thành khi chưa chạy. Báo cáo ngắn bằng tiếng Việt; hỏi đúng thiếu sót cần người dùng quyết định, tiếp tục phần độc lập khi bị chặn.
