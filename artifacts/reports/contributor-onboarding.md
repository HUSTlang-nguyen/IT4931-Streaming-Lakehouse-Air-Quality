# Kiểm chứng onboarding contributor

Cập nhật ngày25/10/2026. Kiểm clone sạch thực hiện24/10/2026 trên candidate `fbff886e1c50fd9eb5bb0186431743f74a98e195`, nhánh `docs/contributor-onboarding` từ mainf39b307 (PR#2 đã merge). Đây là kiểm onboarding mới, tách khỏi bằng chứng pipeline lịch sử.

## Thay đổi bàn giao

- [SETUP](../../docs/SETUP.md): clone/install → core/runtime build/smoke → JSONL với bounds UTC tròn giờ → profile/drain/process availableNow → đối chiếu Silver → train/dashboard/live; tài nguyên local và cách chẩn đoán lỗi.
- [CONTRIBUTING](../../CONTRIBUTING.md): nhánh/PR, chuẩn Python/comment dạng lab, kiểm chứng theo loại thay đổi, cập nhật log/context và dữ liệu không được commit.
- [BACKLOG](../../docs/BACKLOG.md): ưu tiên/acceptance ONB/DEV/OPS/ML/DATA/SCALE; không tự triển khai toàn bộ hoặc tạo Goal mới.
- README/context/Goal prompt/kế hoạch/labs/demo phản ánh PR#1/#2 đã merge; hướng dẫn contributor không phụ thuộc model/data/password hoặc process IDs máy tác giả.

## Kiểm chứng đã chạy

| Kiểm tra | Kết quả / giới hạn |
|---|---|
| Clone độc lập | Git clone đúng candidate từ object store local, không copy working-tree files; trước setup không `.env`, `.venv`, data, models, checkpoints hoặc artifacts/local |
| Python environment | Windows11 build26200, Python3.13.12, venv mới; không dùng package từ venv dự án cũ. pip có thể dùng download cache; không tuyên bố tải mọi dependency từ mạng trắng |
| Cài package | `pip install -e ".[dev]"` và `pip check` pass |
| CLI | `python -m air_quality.cli --help` pass, không có API credentials được kế thừa |
| Unit trên clone mới |26pass,0fail,0error,0skip; JUnit timestamp2026-10-24T18:20:26+07:00 |
| Repository checks | Python syntax/TOML/Markdown links/diff pass; working tree clone sạch sau verification |
| PowerShell |19code blocks ở README/CONTRIBUTING/SETUP/Lab03 parse thành công; UTC date format/parse đã chạy. Không coi parser là đã chạy OpenAQ hoặc toàn bộ Docker commands |
| Compose | Client2.39.2, `config --quiet` với credential tạm sinh riêng trong clone pass; không in credentials, không start services hoặc gắn lại volumes |
| Thời gian probe |38,41giây cho clone/venv/install/CLI/unit/repo/Compose config trên máy kiểm; không phải thời gian dựng toàn stack |

Application source fingerprint sau fix: `1c84eeafb37e7dad3e588004510fd1dd9d09c4abf81befa9daf27ffa3258b918`. Log/JUnit/credential tạm chỉ local ignored hoặc thư mục temp; không đưa hostname, password hay absolute temp path vào báo cáo Git.

## Lỗi được phát hiện nhờ clone sạch

Probe đầu ở candidate c02c3f1 có15pass/10setup errors: `air-quality test` truyền basetemp trong `artifacts/local` khi thư mục cha chưa tồn tại. Working copy cũ đã có log nên không lộ lỗi này. JUnit lại tạo thư mục cha cuối run, vì vậy chỉ chạy lại cùng clone sẽ che lỗi.

Fix fbff886 tạo parent trước khi gọi pytest, thêm regression test kiểm thời điểm tạo thư mục. Sau đó dùng một clone và venv mới khác, assert parent chưa có trước test, đạt26pass. Không đổi pipeline/ML behavior, schema hoặc dependencies. Không cần chạy lại toàn bộ Spark cho thay đổi khởi tạo artifact của host test runner; baseline14Spark pass nằm trong [báo cáo triển khai](end-to-end-summary.md).

## Phần chưa được chứng minh

Chưa chạy Docker bootstrap hoàn chỉnh trên một máy/engine riêng không có images/volumes. Không xóa cache/volume, dừng stack người dùng hoặc khởi động clone thứ hai trên cùng Compose project để giả lập máy sạch. Không thu lại180ngày hoặc train lại model chỉ để kiểm Markdown.

ONB-01 trong BACKLOG giữ tiêu chí thử full build/smoke/OpenAQ→Kafka→Iceberg/train/dashboard trên môi trường riêng. Các report lịch sử202.041records, model metrics và snapshot IDs không trở thành artifacts máy contributor chỉ vì clone repo. Hướng dẫn đã có đường tái tạo, nhưng chỉ phần package/unit/config trên clone sạch được xác nhận ở lần onboarding này.
