# Prompt Goal — Air Quality Streaming Lakehouse

File chuẩn bị, chưa có Goal được tạo. Khi muốn triển khai, gửi toàn bộ nội dung phần dưới cho Codex trong repository này ở chế độ có thể chỉnh sửa file.

---

Tạo và theo đuổi một Goal: triển khai, chạy và kiểm chứng hoàn chỉnh Air Quality Streaming Lakehouse trên Docker local bằng Python, với code học được theo dạng lab và dùng được khi thuyết trình. Không tự đặt ngân sách token.

## 1. Context và tiến độ

Đọc `AGENTS.md`, `docs/IMPLEMENTATION_CONTEXT.md`, `IMPLEMENTATION_PLAN.md`, các STEP mới trong `docs/AGENT_WORK_LOG.md`, tài liệu trong `docs/proposal/`. Đối chiếu Git/code thực tế và giữ thay đổi của người dùng. Phạm vi mới nhất có ML; không cần tìm lại hội thoại.

Sau mỗi mốc có ý nghĩa, append nhật ký rồi cập nhật context: công việc, file/hàm, quyết định/lý do, kiểm chứng, branch/commit nền, blocker, phần dang dở và bước tiếp theo. Context là trạng thái hiện tại, nhật ký là lịch sử không xóa. Ghi hash commit mới ở lần cập nhật kế tiếp. Sau compaction, đọc lại và kiểm tra bằng chứng trước khi tiếp tục.

## 2. Phạm vi và hạ tầng

- ĐHBK: location `4946813`, PM2.5 sensor `13502154`, PM10 `13502152`.
- Công viên Nhân Chính: location `4946812`, PM2.5 `13502151`, PM10 `13502153`.
- OpenAQ API v3; PM2.5/PM10 bắt buộc. NO₂/SO₂/O₃/CO chỉ mở rộng nếu phù hợp. Không có nhiệt độ/độ ẩm, AQI, khuyến cáo sức khỏe; hai điểm không đại diện toàn Hà Nội.
- Python Collector → Kafka → Spark Structured Streaming/Batch → Iceberg/MinIO (Bronze/Silver/Gold) → Trino → Superset; Spark MLlib ghi dự báo vào Iceberg.
- Docker Compose với Iceberg REST catalog chung Spark/Trino; PostgreSQL phục vụ metadata cần thiết. Khảo sát/chọn backend catalog và ghi lý do.
- Kiểm tra Docker, RAM/disk, lab, tài liệu chính thức trước khi dựng stack. Chốt/khóa Python/Java/Spark/Kafka connector/Iceberg/Trino và image tương thích; không dùng image `latest`. Python trên host chưa phải runtime Spark đã được chứng minh.
- Chỉ thao tác trong dự án; tránh xung đột cổng. Không mua cloud, xóa volume hoặc sửa dịch vụ ngoài dự án; ghi rõ thao tác cần quyền hệ thống nếu có.

## 3. Thu thập và quy tắc dữ liệu

- `OPENAQ_API_KEY` qua môi trường hoặc `.env` bị gitignore. Không log/commit secret. Nếu thiếu key, yêu cầu cách cung cấp an toàn và tiếp tục phần độc lập.
- Collector có metadata/live/backfill/replay, pagination/timeout, bounded retry/backoff, HTTP 429/Retry-After; xác minh hạn mức hiện hành. Không chỉ dùng latest để đảm bảo completeness.
- Backfill 180 ngày gần nhất: cố định khoảng thời gian khi bắt đầu, lưu checkpoint theo sensor/khoảng/trang để resume; báo coverage và ngày thiếu thực tế, không giả định đủ lịch sử.
- Polling 300 giây, overlap 24 giờ, đối soát 7 ngày mỗi 24 giờ; cấu hình được, tránh job chồng và tuân thủ rate limit.
- Bronze giữ payload gốc, metadata/provenance, request range, ingested_at và ingest mode. Silver chuẩn hóa UTC/đơn vị/period_start/end, metadata liên kết ID, cờ chất lượng và lý do quarantine/loại.
- MERGE theo sensor/khoảng đo chống trùng, xử lý cả số đo nguồn sửa đổi theo quy tắc có tài liệu; không chỉ dựa watermark. Live/backfill chung quy tắc. Replay namespace riêng, không trộn vào live/metrics live.
- Không điền thiếu bằng 0, không đổi đơn vị âm thầm, không dùng freshness cấp trạm thay sensor. Dashboard không nối qua gap gây hiểu nhầm.
- Bắt buộc xác minh khoảng đo: khảo sát cũ thấy interval một giờ dù timestamp thường cách nhau 5 phút. Không xem đây là các số đo tức thời độc lập. Chỉ tạo trung bình giờ/ngày và chuỗi giờ ML sau khi có phương pháp được chứng minh. Nếu chưa rõ, ghi blocker Gold/ML liên quan và tiếp tục phần khác; không bịa quy tắc để hoàn thành.
- Lưu UTC, hiển thị Asia/Ho_Chi_Minh; phân biệt event time, ingested_at và thời điểm dữ liệu thực sự sẵn có.

## 4. ML và dashboard

- Random Forest Regression Spark MLlib, mỗi trạm một model, dự báo PM2.5 t+1 giờ trên chuỗi giờ hợp lệ.
- Features: current PM2.5, lag 1/2/3/24 giờ, hour-of-day. Join theo mốc giờ thực, không theo vị trí dòng khi gap.
- Train/validation/test 70/15/15 theo thời gian; loại nhãn vượt ranh giới. Fit preprocessing/chọn tham số chỉ trên tập được phép; không dùng tương lai điền thiếu hoặc tune bằng test.
- Persistence baseline giữ giá trị hiện tại. MAE/RMSE trên cùng mẫu; ghi số mẫu, thời gian, snapshot dữ liệu, seed/config/model version. Không yêu cầu thắng baseline hoặc bịa metrics.
- Lưu model/config/metrics; prediction có trạm, issued_at, target_time, value/unit, model version và chế độ backtest/operational. Bổ sung actual/error khi có dữ liệu hợp lệ, chạy lại an toàn.
- Không coi lịch sử tải hôm nay là dữ liệu đã có tại thời điểm quá khứ. Replay lịch sử ghi rõ backtest. Forecast operational chỉ dùng dữ liệu sẵn có khi phát hành và báo stale input.
- Superset đọc Trino: diễn biến PM2.5/PM10, so sánh trạm trên khoảng phù hợp, gap/coverage/freshness theo sensor, forecast/actual. Export/import dashboard tái tạo được.

## 5. Python, lab và thuyết trình

- Python cho nghiệp vụ/CLI/pytest, PySpark/Spark MLlib cho xử lý/ML. SQL/YAML/Dockerfile đúng vai trò; không thêm ngôn ngữ lập trình khác nếu không cần.
- Dùng cây thư mục hiện có; chỉ tạo module có trách nhiệm thực tế. Không hàm giả, notebook khổng lồ hay abstraction để làm đầy structure.
- Tên tiếng Anh rõ nghĩa, type hints, cấu hình tập trung, hàm một trách nhiệm. Tách API/Kafka/storage I/O khỏi biến đổi; script/lab gọi package `src`, không nhân bản nghiệp vụ.
- Comment/docstring tiếng Việt dạng lab: module mô tả vai trò/I/O; hàm nghiệp vụ mô tả mục đích/params/output/side effect/lỗi/ví dụ khi cần. Logic khó chia bước giải thích vì sao, giả định, tradeoff/edge case; không comment lại từng phép gán. Không nuốt lỗi.
- Lệnh thống nhất start/stop/status/backfill/live/replay/train/predict/test/benchmark có hướng dẫn PowerShell và kiểm tra kết quả; không ghi lệnh chưa tồn tại như đã chạy được.
- Phát triển lab cùng tính năng: OpenAQ → Collector/Kafka → Bronze/Silver → Gold/quality → Trino/Superset → ML → Iceberg experiments. Mỗi lab có prerequisite, mục tiêu, kiến thức tối thiểu, sơ đồ, code thật, lệnh, kết quả kỳ vọng, cách kiểm tra, lỗi thường gặp, bài tập nhỏ; đánh dấu thao tác phá dữ liệu nếu có.
- `docs/code-walkthrough.md` dẫn một measurement qua file/hàm thật. `docs/presentation-guide.md` chọn 6 đoạn code thật khoảng 10–25 dòng: crawl, chuẩn hóa, dedup, late data, features ML, evaluation; có file/hàm, input/output, ý chính, lời giải thích 30–60 giây. Đoạn trích khớp code cuối; không tự sửa slide cũ.

## 6. GitHub

- Dùng repository hiện tại, remote `https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality.git`; không khởi tạo Git lồng nhau.
- Kiểm tra base có scaffold, tạo/reuse `feat/air-quality-lakehouse` từ đó; không mặc định scaffold đã merge `main`.
- Commit nhỏ có ý nghĩa (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), xem diff/check secret/test phù hợp, stage đúng file; giữ thay đổi ngoài nhiệm vụ của người dùng.
- Push checkpoint đã kiểm chứng, tạo draft PR khi có implementation review được và cập nhật mô tả theo trạng thái cuối. Attach PR vào chat nếu công cụ hỗ trợ. Không tự merge, force-push, xóa branch hoặc rewrite lịch sử đã push.
- Không commit `.env`, credentials, crawl lớn, model binary, volume/cache/raw logs. Theo dõi env example, fixture nhỏ đã làm sạch, lock, dashboard config, báo cáo gọn. Gắn kiểm chứng với commit và ghi rõ nếu working tree dirty.

## 7. Nghiệm thu

- Test pagination/retry, duplicate/correction/late data/gap/timezone/checkpoint/restart và leakage bằng fixture có kiểm soát.
- Có dữ liệu thật đi OpenAQ → Kafka/Spark/Iceberg/Trino → Superset; fixture không thay bằng chứng live. Đối chiếu mẫu nguồn với kết quả theo quy tắc đã xác minh.
- Restart không mất dữ liệu bền vững/nhân đôi Silver; backfill resume đúng, coverage thực tế, không dùng ước lượng thay số thực.
- Pruning có query plan/scan evidence; compaction có file count/size và đối chiếu query; time travel có snapshot trước/sau và query. Ghi lệnh/dataset/config/số lần đo/giới hạn. Dữ liệu nhân bản thử tải tách namespace/ghi nhãn; không cam kết tăng tốc chưa đo.
- Có model/metrics/baseline/forecast/dashboard trên dữ liệu hợp lệ; không tuyên bố ML thành công nếu thiếu dữ liệu hoặc target semantics chưa rõ.
- Bàn giao README, kiến trúc, dictionary, coverage/tests/benchmarks, labs đã chạy, walkthrough, presentation guide và demo tái lập. Bằng chứng nhỏ đã làm sạch ở `artifacts/reports/`; raw/model/data ở nơi gitignore.
- Chỉ hoàn thành Goal khi mọi tiêu chí bắt buộc có bằng chứng. Budget cạn, scaffold xong, API bị chặn hoặc fixture pass không đồng nghĩa hoàn thành. Nêu đúng blocker và điều cần để tiếp tục.

## 8. Cách làm việc

Làm từng lát cắt xuyên suốt, kiểm chứng rồi mở rộng; tự giải quyết lựa chọn thường lệ và tiếp tục sau checkpoint. Chỉ hỏi khi cần quyết định/quyền/thông tin từ người dùng; làm phần độc lập trong lúc chờ. Không lặp vô hạn thao tác lỗi; lưu kết quả và đổi hướng có cơ sở. Trước bàn giao cập nhật context đủ để tiếp tục không cần hội thoại. Kết thúc nêu chức năng đã chạy, bằng chứng, cách demo và tiêu chí còn thiếu.
