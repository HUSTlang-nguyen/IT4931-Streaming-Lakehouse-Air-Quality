# Backlog sau bản triển khai đầu

PR #1/#2 đã merge; Goal triển khai ban đầu đã hoàn tất. Đây là thứ tự đề xuất để contributor nhận công việc, không phải yêu cầu agent tự thực hiện tất cả. Trao đổi phạm vi với maintainer trước khi đổi kiến trúc hoặc thêm dịch vụ.

| ID / ưu tiên | Công việc và trạng thái | Tiêu chí nghiệm thu |
|---|---|---|
| ONB-01 / P0 | Kiểm Docker bootstrap từ trắng — còn mở | Một máy/engine riêng không có images/volumes của dự án, theo SETUP từ clone tới build/smoke/JSONL→Kafka→Silver reconciliation/train/dashboard. Ghi OS, Python/Docker/Compose, versions, thời gian và lỗi. Không dùng key/models/data của tác giả hoặc xóa volumes engine đang chạy để kiểm |
| DEV-01 / P1 | CI cho PR — chưa triển khai | Workflow offline cài package dev, chạy unit + repository syntax/TOML/links checks trên checkout sạch không `.env`/API key; có failure exit code rõ. Integration/live vẫn opt-in, không gắn fixture pass thành E2E |
| OPS-01 / P1 | Lịch chạy forecast/actual enrichment — chưa triển khai | Thiết kế job định kỳ phù hợp giới hạn RAM, không chạy JVM chồng processor/job khác; giữ idempotency/model-before-issue/input availability/stale suppression, retry có giới hạn, log sạch secret. Có restart/late-actual tests và tài liệu vận hành; thống nhất cadence với maintainer trước khi code |
| ML-01 / P2 | Đánh giá cải thiện RF — nghiên cứu, chưa có cam kết tăng accuracy | Chốt candidate/config và cách chọn bằng validation trước thực nghiệm; test giữ lại/purge, so persistence cùng mẫu, báo sample coverage và metrics dù model kém. Không dùng tập test hiện tại để chọn model rồi báo nó như held-out mới |
| DATA-01 / P2 | Giải thích physical semantics raw interval — còn mở | Có tài liệu/provider evidence cho interval1h/cadence5min. Giữ raw và source `/hours` riêng; chỉ đề xuất đổi aggregate/target khi có chứng cứ, migration và đối chiếu. Không xem mean nguồn đã dùng là đã giải thích được sensor raw |
| SCALE-01 / P2 | Giảm chi phí full Gold refresh / thử tải lớn hơn — chưa triển khai | Chọn quy mô/query thực nghiệm trước; incremental vẫn xử lý correction/late/invalid/retry đúng như hiện tại. Đo file/scan/timing lặp, ghi rõ dữ liệu nhân bản và namespace riêng; không cam kết tăng tốc khi chưa đo |

## Quy tắc nhận việc

Mỗi việc dùng nhánh/PR riêng từ `main`, mô tả phạm vi và bằng chứng trước/sau theo [CONTRIBUTING](../CONTRIBUTING.md). Nhận ONB-01 trước nếu mục tiêu là xác nhận người mới tự chạy được toàn hệ thống. DEV-01 có thể làm độc lập, không cần API key. OPS/ML/SCALE chỉ bắt đầu khi đã thống nhất phạm vi; tài liệu backlog này không mở một Goal mới.

Khi hoàn tất, cập nhật trạng thái dòng tương ứng và link PR/report thực tế, append work log và đồng bộ context. Các báo cáo 180 ngày/ML/benchmark hiện có là baseline lịch sử, không phải target số dòng/accuracy cần ép đạt trên run mới.
