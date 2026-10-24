# Hướng dẫn contributor

## Bắt đầu và chọn công việc

Đọc [README](README.md), [setup từ clone mới](docs/SETUP.md), [kiến trúc](docs/architecture.md) và [backlog](docs/BACKLOG.md). Bản triển khai ban đầu đã hoàn thành và PR #2 đã merge; contributor không cần chạy lại Goal triển khai để bắt đầu sửa code.

Nếu dùng agent, đọc thêm [AGENTS](AGENTS.md) và [context](docs/IMPLEMENTATION_CONTEXT.md). Context mô tả code/checkpoint; trạng thái container hoặc model trên máy tác giả không tồn tại tự động trên máy bạn. Backlog là đề xuất công việc, không phải lệnh triển khai toàn bộ hoặc tạo Goal mới.

## Git workflow

Chạy tại Git root, kiểm tra thay đổi trước khi chuyển nhánh. Nếu có công việc chưa commit, giữ lại và xử lý riêng; không reset hoặc checkout đè file.

```powershell
git status --short
git switch main
git pull --ff-only origin main
# Ví dụ cho thay đổi tài liệu; dùng tên mô tả đúng công việc của bạn.
git switch -c docs/update-onboarding
```

Dùng tiền tố `feat/`, `fix/`, `test/`, `docs/` hoặc `chore/`. Nhánh PR đã merge là lịch sử; tạo nhánh mới từ main hiện tại thay vì tiếp tục push vào PR đã đóng. Không force-push hoặc rewrite lịch sử đã chia sẻ. PR được maintainer/reviewer xem xét; agent không tự merge.

## Quy chuẩn code và tài liệu

- Python/PySpark cho nghiệp vụ, SQL/YAML/Dockerfile đúng vai trò; tên tiếng Anh rõ nghĩa, type hints cho hàm nghiệp vụ.
- Comment/docstring tiếng Việt giải thích input/output, side effect, giả định và logic khó. Hàm một trách nhiệm; lab gọi package production, không sao chép pipeline vào notebook.
- Giữ invariant: UTC lưu/giờ VN hiển thị, missing là null, raw và source `/hours` riêng, replay tách live. Thay đổi keys/quality/Gold phải mô tả migration và correction/late-data behavior.
- Thay đổi ML phải giữ causal features, chronological split/purge, baseline cùng mẫu và provenance. Không tune bằng test hoặc yêu cầu RF phải thắng baseline.
- Cập nhật lab/dictionary/architecture liên quan. Nếu source của sáu đoạn thuyết trình đổi, chạy lại script trích code; không sửa snippet thành thuật toán khác.
- Sau mốc có ý nghĩa, append STEP mới vào `docs/AGENT_WORK_LOG.md`, rồi cập nhật `docs/IMPLEMENTATION_CONTEXT.md`. Log giữ lịch sử; ghi đính chính bằng STEP mới.

## Kiểm tra trước PR

Package dev đã cài theo SETUP; chạy từ root:

```powershell
.venv/Scripts/python.exe scripts/verify_repository.py
git diff --check
```

| Thay đổi | Kiểm chứng thêm |
|---|---|
| Chỉ Markdown | Kiểm links/lệnh và đọc diff; không cần chạy lại toàn bộ Spark |
| Collector/config/contracts | `air-quality test`; `test --live` chỉ khi cần kiểm API contract và có key riêng |
| Processing/ML/storage | Unit + `test --integration` với core sẵn sàng; dừng processor trước để dành RAM và tránh writer thứ hai |
| Docker/dependency | Build image liên quan, smoke Spark→Trino; ghi phiên bản và môi trường thực tế |
| Superset | Provision, native export/import, kiểm unique chart nodes/UUID và render/API chart; cập nhật YAML export |

Ở bảng trên, `air-quality` tương đương `.venv/Scripts/python.exe -m air_quality.cli`; dùng cách đầy đủ nếu chưa activate venv.

```powershell
.venv/Scripts/python.exe -m air_quality.cli test
# Chỉ khi core/runtime sẵn sàng và thay đổi cần Spark:
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop processor
.venv/Scripts/python.exe -m air_quality.cli test --integration
# Mở lại nếu processor đang được dùng trước test.
.venv/Scripts/python.exe -m air_quality.cli start --services processor --no-build
```

Không coi tests bị skip do thiếu pyspark trên host là integration pass. API live cần opt-in riêng; unit tests không dùng key. Lệnh `smoke/train/predict/benchmark` có thể cập nhật JSON reports được Git theo dõi: xem diff và chỉ đưa vào PR khi đó là bằng chứng cho thay đổi đang làm. Không đổi provenance của báo cáo cũ để gắn commit mới.

```powershell
.venv/Scripts/python.exe scripts/export_presentation_snippets.py
```

Chỉ chạy script trích code khi source tương ứng đổi; xem diff trước khi stage.

## Nội dung PR và dữ liệu local

Commit nhỏ theo `feat:`, `fix:`, `test:`, `docs:` hoặc `chore:`. Stage đúng file đã xem, push nhánh của bạn và mở PR vào `main`; draft khi còn việc cần kiểm chứng. Mô tả PR gồm vấn đề/hành vi sau sửa, cách kiểm thử/kết quả, thay đổi schema/config và giới hạn còn lại. Với bằng chứng local, ghi rõ fixture/live/backtest/operational, source snapshot và revision/dirty state.

Không commit `.env`, key/password/cookie, raw crawl, SQLite checkpoint, model binary, volume hoặc log lớn. Git có fixture nhỏ và báo cáo đã làm sạch; contributor tự tạo key, dữ liệu và model theo SETUP. Không dùng password của máy tác giả. Nếu cần chuyển dữ liệu giữa người dùng, thống nhất cách chia sẻ riêng và giữ provenance; không đẩy raw vào Git để tiện demo.

Compose dùng tên project/cổng cố định. Trên cùng Docker engine, một checkout vận hành stack tại một thời điểm; chạy `start` ở clone thứ hai có thể thay mount của cùng service. Không dùng `down -v`/prune để sửa setup hoặc chạy lại lab.
