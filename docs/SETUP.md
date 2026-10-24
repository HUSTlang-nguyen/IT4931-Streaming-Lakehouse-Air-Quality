# Setup từ clone mới — Windows / PowerShell

Luồng chuẩn: clone → kiểm offline → dựng core/runtime → smoke → thu JSONL có bounds cố định → profile → Kafka → xử lý hết batch → train/predict → dashboard → live.

Hướng dẫn dùng đường dẫn/cổng mặc định trong `.env.example`. Dành cho máy chưa có stack dự án; trên cùng Docker engine chỉ dùng một checkout vận hành vì Compose project tên cố định `air-quality-lakehouse`. Đối với máy đang chạy, dùng [demo](demo.md) và kiểm trạng thái trước; không tạo stack thứ hai đè mount/volume.

## 1. Điều kiện và clone

- Windows với Docker Desktop chạy Linux containers, Compose v2; Docker engine được cấp khoảng 8 GiB RAM. Python host 3.11+ và Git. Bản triển khai trước được kiểm với host Python 3.13, runtime Spark Python 3.11; không cần cài Java/Spark lên host.
- Mạng để tải image, Python packages, Maven jars và build MinIO từ source. Có dung lượng trống cho images/build cache/data; thời gian build đầu phụ thuộc mạng và máy. Dành một JVM Spark mỗi lúc trong giới hạn RAM này.
- `OPENAQ_API_KEY` của bạn cho phần dữ liệu thật. Core/smoke/unit/integration fixture không cần key. Khí, AQI và khuyến cáo sức khỏe nằm ngoài phạm vi.

```powershell
git clone https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality.git
Set-Location IT4931-Streaming-Lakehouse-Air-Quality
git switch main
git pull --ff-only origin main
python --version
docker version
docker compose version
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
```

Khi review hướng dẫn trong PR chưa merge, checkout nhánh PR sau clone trước khi làm tiếp. Không cần activate venv hoặc thay PowerShell execution policy khi dùng đường dẫn Python đầy đủ như trên.

## 2. Kiểm package khi chưa có Docker/API data

```powershell
.venv/Scripts/python.exe -m air_quality.cli --help
.venv/Scripts/python.exe -m air_quality.cli test
.venv/Scripts/python.exe scripts/verify_repository.py
```

Kỳ vọng unit suite pass; tại checkpoint triển khai có 25 unit tests. Số lượng có thể tăng theo đóng góp. `verify_repository` kiểm Python syntax, TOML, links, diff và credential local không xuất hiện trong candidate files; không chứng minh pipeline đã chạy.

## 3. Dựng core và runtime, rồi smoke

```powershell
.venv/Scripts/python.exe -m air_quality.cli start --services kafka minio catalog postgres trino superset
docker compose --env-file .env -f infra/compose.yaml --profile jobs build spark
# Nếu build vừa lỗi, sửa lỗi trước; không chạy smoke tiếp rồi gọi setup thành công.
.venv/Scripts/python.exe -m air_quality.cli smoke
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT * FROM iceberg.validation.smoke'
.venv/Scripts/python.exe -m air_quality.cli status
```

`start` sinh credential còn trống vào `.env`; giữ password đã bảo vệ volumes. Không tự điền password khác cho volume cũ. Build `spark` tường minh để nhánh core-only cũng có runtime trước các job; image dùng lại cho processor/collector. Chưa mở Collector/processor ở bước này.

Smoke phải có một hàng `id=1`, message `Spark / REST / MinIO` và Trino đọc cùng hàng. Kafka/Postgres/Trino/Superset/MinIO có Docker healthchecks; catalog không có native healthcheck, CLI kiểm HTTP readiness riêng. Container màu xanh chưa thay được kiểm đọc/ghi bảng.

Có thể chạy `test --integration` ở đây, trước thu lịch sử. Tests dùng namespace fixture riêng; checkpoint triển khai đã có 14 Spark/Iceberg pass và 4 API live skip chủ đích trong run offline. Không gọi đây là dữ liệu OpenAQ thật.

## 4. Tạo lịch sử trên máy bạn

Mở `.env` bằng editor và điền `OPENAQ_API_KEY`. Không in key vào lệnh/log/slide. Collector container vẫn chưa chạy nên host backfill là tác vụ API duy nhất; nếu dùng một stack cũ, dừng Collector trước. Hai máy dùng cùng key cũng chia sẻ hạn mức OpenAQ, cần phối hợp.

Lưu bounds UTC tròn giờ vào file local trước lần đầu. Giữ file khi resume; không tính lại end mỗi ngày cho cùng run-name.

```powershell
if (-not (Test-Path -LiteralPath data)) { New-Item -ItemType Directory data | Out-Null }
if (-not (Test-Path -LiteralPath data/setup-history-bounds.json)) {
    $aqEnd = (Get-Date).ToUniversalTime().Date
    @{
        start = $aqEnd.AddDays(-180).ToString('yyyy-MM-ddTHH:mm:ssZ')
        end = $aqEnd.ToString('yyyy-MM-ddTHH:mm:ssZ')
    } | ConvertTo-Json | Set-Content -Encoding utf8 data/setup-history-bounds.json
}
$aqBounds = Get-Content -LiteralPath data/setup-history-bounds.json -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m air_quality.cli backfill --start $aqBounds.start --end $aqBounds.end --sink jsonl --output data/history-180d.jsonl --run-name onboarding-180d
```

Chờ backfill exit 0. Bước này chủ động tạo `data/history-180d.jsonl`; file không có sẵn khi clone. Mặc định thu cả measurements và hours cho bốn sensor. Archive/SQLite checkpoint nằm local; chạy lại đúng lệnh sẽ resume, không xóa file/checkpoint. Khi đổi khoảng nghiên cứu, chọn run-name và output mới, giữ cặp bounds tương ứng; không append một run khác vào file lịch sử cũ.

```powershell
.venv/Scripts/python.exe -m air_quality.cli profile --input data/history-180d.jsonl --start $aqBounds.start --end $aqBounds.end --output data/reports/onboarding-coverage.json
$aqProfile = Get-Content -LiteralPath data/reports/onboarding-coverage.json -Raw | ConvertFrom-Json
$aqProfile | Select-Object unique_records, duplicate_keys, outside_range
$aqProfile.series | Format-Table sensor_id, series_kind, unique_records, invalid_records, flagged_records, hourly_availability_percent
```

Kỳ vọng có dữ liệu của bốn sensor/cả hai resources; nếu thiếu nhóm, kiểm nguồn và báo cáo trước khi train. Không ép count bằng 202.041 hoặc coverage 100%: đó là bằng chứng một khoảng lịch sử của máy tác giả, không phải điều kiện cho mọi ngày chạy. `/hours` là target chuẩn; không tự bình quân raw interval chồng nhau.

## 5. Kafka và Iceberg: phải xử lý hết trước khi train

```powershell
.venv/Scripts/python.exe -m air_quality.cli drain --input data/history-180d.jsonl --run-name onboarding-to-kafka
.venv/Scripts/python.exe -m air_quality.cli process
```

Chờ cả hai lệnh exit 0. `drain` giữ mode backfill và timestamp thu gốc, chỉ checkpoint sau ACK; không gọi API. `process` là Structured Streaming availableNow, kết thúc sau khi xử lý hết offset đã có. Chưa mở live producer/continuous processor nên đây là ranh giới kiểm chứng rõ ràng. ACK Kafka không đồng nghĩa Gold đã sẵn sàng.

```powershell
$aqStartSql = [DateTimeOffset]::Parse($aqBounds.start).UtcDateTime.ToString('yyyy-MM-dd HH:mm:ss')
$aqEndSql = [DateTimeOffset]::Parse($aqBounds.end).UtcDateTime.ToString('yyyy-MM-dd HH:mm:ss')
$aqStored = (.venv/Scripts/python.exe -m air_quality.cli query "SELECT count(*) FROM iceberg.live.silver WHERE period_end > TIMESTAMP '$aqStartSql' AND period_end <= TIMESTAMP '$aqEndSql'" | ConvertFrom-Json).data[0][0]
if ([long]$aqStored -ne [long]$aqProfile.unique_records) { throw 'Silver khác source unique count: kiểm rejected/deadletter và log ingest trước khi tiếp tục' }
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT sensor_id,series_kind,count(*) FROM iceberg.live.silver GROUP BY 1,2 ORDER BY 1,2'
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT parameter_name,count(*) bins,count(value) valid_hours FROM iceberg.live.hourly GROUP BY 1'
```

So từng nhóm với source profile; nếu thiếu key bị quarantine, đối chiếu rejected/deadletter thay vì ép equality bằng sửa/xóa nguồn. Source coverage không phải độ chính xác cảm biến. Snapshot IDs trong các report lịch sử không tồn tại tự động trên catalog mới; dùng snapshots/run report của máy bạn.

## 6. Model và dashboard

```powershell
.venv/Scripts/python.exe -m air_quality.cli train
.venv/Scripts/python.exe -m air_quality.cli predict
.venv/Scripts/python.exe -m air_quality.cli dashboard
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT station_name,algorithm,n,mae,rmse FROM iceberg.live.model_metrics'
```

Train phải thành công trước predict. Model binaries/manifest được tạo trong Docker volume `model_data`, không tải từ Git. Code yêu cầu ít nhất 100 train và 30 validation/30 test samples mỗi sensor; gaps có thể khiến chưa đủ mẫu. Không nới điều kiện hoặc tune test để ép có kết quả.

Backfill kết thúc ở UTC midnight nên `predict` lúc này có thể báo stale/target expired và không phát hành operational; đây là kết quả đúng. Backtest/metrics vẫn có sau train. Để có forecast mới, làm bước live bên dưới rồi gọi predict lại.

Mở `http://localhost:18088/superset/dashboard/air-quality-hanoi/`. Đọc `SUPERSET_ADMIN_USERNAME`/`SUPERSET_ADMIN_PASSWORD` từ `.env` của chính máy bạn bằng editor. Khi chưa train, provision chỉ có 5 panel dữ liệu; sau train và provision lại có 8 panel gồm ML. Bảng operational có thể rỗng nếu nguồn chưa đủ mới; actual chưa tới là null.

`dashboard` tạo spec/native YAML và ZIP `output/playwright/dashboard-native.zip` local. Git có YAML export; ZIP được tạo lại khi provision. [Lab 05](../labs/05-dashboard.md) giải thích export/import; [Lab 06](../labs/06-forecasting.md) giải thích ML.

## 7. Vận hành live và chạy Spark jobs sau đó

```powershell
.venv/Scripts/python.exe -m air_quality.cli start --services collector processor --no-build
.venv/Scripts/python.exe -m air_quality.cli status
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT * FROM iceberg.live.freshness'
```

Chờ một chu kỳ Collector và microbatch processor; xem `last_measurement_at` và `last_ingested_at` theo sensor/resource. `/hours` có thể chậm hơn raw. Chỉ gọi forecast khi input giờ hợp lệ/các lags đã đủ; nếu stale thì giữ trạng thái đó, không đổi issued_at về quá khứ.

```powershell
# Dừng processor trước JVM Spark riêng, giữ checkpoint và Collector ghi Kafka.
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop processor
.venv/Scripts/python.exe -m air_quality.cli process
.venv/Scripts/python.exe -m air_quality.cli predict
# Sau job, mở processor lại kể cả khi job lỗi và đã kiểm tra nguyên nhân.
.venv/Scripts/python.exe -m air_quality.cli start --services processor --no-build
```

`process` thủ công dùng cùng checkpoint live và chỉ chạy khi continuous processor đã dừng. Lệnh train/test integration/benchmark cũng cần RAM cho JVM riêng; không chạy đồng thời. `predict` là lệnh theo lần gọi, actual được enrich mỗi lần; chưa có scheduler ML mặc định.

```powershell
.venv/Scripts/python.exe -m air_quality.cli stop
```

Stop giữ data/metadata/model/checkpoints. Resume bằng `start --no-build` khi image/config vẫn phù hợp; không sửa credentials hoặc xóa volumes để chạy lại.

## 8. Tài nguyên local, lỗi thường gặp và mức kiểm chứng

| Tài nguyên | Sau clone / cách tạo |
|---|---|
| `.env` / key/password | Không ở Git; copy template, tự cấp API key, `start` sinh credential còn trống |
| Raw/JSONL/metadata/source coverage mới | Không ở Git; backfill/profile ở bước 4 |
| Kafka log, catalog, MinIO tables, checkpoints | Tạo bằng core + drain/process; volumes local, không có dữ liệu mẫu đầy đủ trong Git |
| Models/manifest | `train` tạo trên model_data; không copy path/version của máy tác giả |
| Dashboard YAML / ZIP | YAML có trên Git, provision tái tạo; ZIP local do export tạo |
| Reports tracked | Bằng chứng lịch sử; một số CLI cập nhật reports nên phải xem `git diff` sau lab |
| JUnit/log/screenshot | Local ignored; tự chạy tests/UI để tạo bằng chứng máy mình |

| Triệu chứng | Kiểm tra / hành động |
|---|---|
| Docker daemon không kết nối | Mở/sửa Docker Desktop trên máy mình trước; không áp dụng thao tác socket máy tác giả một cách máy móc |
| Cổng đã dùng / checkout thứ hai | Kiểm `status` và service sở hữu cổng; dùng checkout đang vận hành, không start project trùng |
| Registry/Maven/APT build lỗi | Giữ log lỗi đầu tiên, kiểm mạng/tag/package pin; không tự thay `latest` hoặc bỏ checksum. Build cache trước đó không chứng minh download mới thành công |
| CLI báo thiếu key / HTTP429 | Điền key riêng qua editor, phối hợp các Collector dùng chung key, tôn trọng Retry-After; không log header |
| File lịch sử/model không có | Tạo đúng bước 4/6; Git chứa code/report, không chứa các artifacts lớn đó |
| Train thiếu mẫu / forecast stale | Kiểm source/hourly coverage, lags và freshness; không zero-fill hoặc giả thời gian issue |
| Exit137 / writer lock | Dừng processor trước Spark job riêng, giảm số JVM đồng thời; không xóa checkpoint/lock khi writer còn sống |
| Biểu đồ thiếu panel / lỗi dataset | Chờ process/train xong, chạy lại dashboard; xem Trino/chart API, không tự điền dữ liệu cho biểu đồ |

Mức kiểm chứng của lần onboarding này được ghi tại [báo cáo onboarding](../artifacts/reports/contributor-onboarding.md). Build/smoke/E2E trước đây đã chạy trên máy phát triển; chưa coi đó là kiểm chứng Docker từ trắng trên máy contributor. Không xóa volumes/images máy đang chạy để giả lập máy sạch. Phần kiểm chứng fresh Docker còn lại có tiêu chí tại [BACKLOG](BACKLOG.md).
