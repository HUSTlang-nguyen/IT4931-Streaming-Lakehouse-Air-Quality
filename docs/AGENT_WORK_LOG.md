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

## STEP-011 — 2026-10-24T16:45:35+07:00 — Stack Docker và Spark/Trino cùng catalog

- Nền Git c5ab9fa đã push; working tree triển khai P2/P4/dashboard chưa commit lúc ghi.
- Dựng Compose project air-quality-lakehouse: Kafka3.9.1, MinIO source build, REST catalog1.6.0 SQLite persist, PostgreSQL16.9 metadata Superset, Trino476, Superset4.1.2. Python3.11/Java17.0.20.1/Spark3.5.6/Iceberg1.9.2 runtime build thành công, lock Python/Java xuất từ image.
- Lỗi đã tìm/sửa: catalog image UID1000 không ghi được volume root; init volume owner1000, không xóa DB/volume hoặc chạy catalog root. Job trước fail DNS khi catalog restart, sau readiness check/owner fix smoke ghi thật và Trino đọc cùng hàng thành công.
- File: infra/compose.yaml, infra/spark/superset/trino, operations.py/session.py. Không dump env/credential vào log.
- Bằng chứng: spark-smoke.json, runtime-build.log; core-start86202/runtime-build17433/smoke12444 đều terminal0.

## STEP-012 — 2026-10-24T16:45:35+07:00 — Source→Kafka→Iceberg reconciliation và Spark quality tests

- Drain source giữ ingest_mode backfill và event_id, Kafka ACK202.041 records; session41893 terminal0. Host unit25pass ở lần gần nhất (Collector/drain/coverage/operations), 4 API live pass ở checkpoint trước.
- Structured Streaming availableNow session77874 terminal0, 11 micro-batches. Bronze=Silver=202.041; từng sensor/resource khớp source. Gold17.280 hourly bins, 1.184 missing null; daily724, freshness8. Reconciliation đã gắn snapshot IDs cụ thể và Trino time travel count để không nhầm với bảng live đang tăng.
- Sáu integration tests Spark/Iceberg thật pass: duplicate/correction, late/gap/daily, invalid correction, quarantine missing period, UTC/unit, replay isolation. Lần đầu fixture offset monotonic bị Catalyst coi nondeterministic; sửa fixture thành offset input cố định như Kafka, không nới assertions.
- File: processing/transforms/tables/jobs, collector/archive, tests/integration/test_lakehouse.py. Bằng chứng reports/lakehouse-history-reconciliation.json và local/tests-spark.xml. Test58712/reconciliation92754 terminal0.

## STEP-013 — 2026-10-24T16:45:35+07:00 — Dashboard thật, native export/import và continuous pipeline

- Python API provision database/datasets/5charts/layout idempotent. Snapshot Playwright xác nhận charts render, data APIs200, giờVN, nhãn tiếng Việt, số format rõ, gaps null. Sửa rolling range tới now vì Last7days mặc định chỉ ngày đã kết thúc.
- Native export11YAML files sạch secret trong dashboards/export; ZIP ignored. import_native chạy OK, giữ UUID. Browser session airquality Chrome16680 đang mở để kiểm chứng; auth state/cookies chỉ ở output/playwright ignored, không in/log token.
- Collector/processor continuous đã khởi động qua Compose, start45521 terminal0 nhưng containers là services đang sống. Collector checkpoint/limiter volume collector_state Linux riêng; không chạy manual heavy Collector host song song cùng key. Processor resume checkpoints/spark/live và heartbeat30s. Source mới đã vào freshness (PM2.5/PM10 có mốc riêng).
- Runtime locked rebuild37744 đang export image ở quan sát gần nhất; cần poll đúng handle trước khi restart/bắt đầu ML. Thêm NumPy1.26.4 cho ML, Java/JAR SHA256 pin, dependency layers cache. Chưa train ML.
- Bước tiếp: cập nhật docs/labs, verify restart persistence, commit/push stack; sau đó RF/persistence+metrics+prediction/dashboard, pruning/compaction, lab06/07 và presentation guide. Goal vẫn active đầy đủ.

## STEP-014 — 2026-10-24T16:58:47+07:00 — Restart persistence và ML thật

- Nền c5ab9fa, nhánh feat/air-quality-lakehouse; checkpoint stack/ML working tree chưa commit.
- Runtime locked rebuild37744 terminal0, lock Python xuất lại có NumPy1.26.4. Restart19324 terminal0: stop core/start giữ volumes, trước/sau Bronze214381/Silver202537/hourly17316/daily724/freshness8 bằng nhau; sau processor resume vẫn bằng nhau, Silver duplicate keys0. Report restart-persistence.json.
- ML feature tests84764 terminal0:5pass exact-hour lag/gap/availability/label/purge/metrics. Train34402 terminal0 trên Gold snapshot5061425689190597954: RF version rf-f0077526710fd81e, seed42,numTrees30, depth8 chọn bằng validation cho cả2 trạm, test giữ lại. Model binary ở model_data, manifest/predictions/metrics thật.
- ĐHBK train/val/test2317/513/555: RF MAE11.3942 RMSE16.6638; persistence MAE11.7468 RMSE15.0972. Nhân Chính2559/648/649: RF MAE6.7809 RMSE9.4208; persistence MAE5.7281 RMSE7.2831. Không tuyên bố thắng baseline; đây là retrospective snapshot backtest. Report ml-evaluation.json.
- README/architecture/dictionary/labs index/module README đã cập nhật theo implementation; labs06/07/demo/presentation còn đang viết. CLI train/predict/benchmark đã code, predict chưa chạy. Dashboard ML panels code đã bổ sung nhưng chưa provision/visual QA.
- Benchmark52090 fail assertion sum(double) trước/sau rewrite vì thứ tự cộng floating point; không xóa namespace cũ. Sửa SUM decimal xác định và thêm exceptAll hai chiều kiểm nguyên hàng. Rerun9598 đang sống, log artifacts/local/benchmark-second.log.
- Processor/Collector hiện paused để giữ RAM cho Spark jobs; core healthy. Cần resume Collector/processor sau ML/benchmark, predict khi hours đủ mới; test6 ML mới thêm forecast retry/actual enrichment còn chưa chạy.
- Bước tiếp: poll benchmark9598, test ML bổ sung, operational forecast+ML dashboard, hoàn thiện docs/snippets/links/secret; commit/push và cập nhật PR#1. Goal active.

## STEP-015 — 2026-10-24T17:10:35+07:00 — ML operational, benchmark và lỗi concurrency catalog

- Nền c5ab9fa, working tree chưa commit. Benchmark9598 terminal0: bản sao202537 hàng thật,28→7files,10515307→9327132bytes; tháng7 chạm4/28 trước và1/7 sau. exceptAll hai chiều0, Spark/Trino time travel cùng202537. Client median2.178→2.204s, không claim tăng tốc. Report iceberg-benchmark.json, namespace experiment_20261024_095728 giữ snapshots.
- Test ML39114 fail ở forecast_actual commit khi dashboard đọc cùng lúc: catalog log xác nhận SQLITE_BUSY. Bật JDBC URI journal_mode=WAL & busy_timeout30000 trên DB cũ, restart catalog giữ bảng/count. Test72743 terminal0:6pass gồm retry giữ forecast đầu và actual correction. Không xóa dữ liệu failed test, không retry commit Unknown mù.
- Trino476 view API gọi REST1.6.0 trả lỗi load view. Đối chiếu source476 có property view-endpoints-enabled, tắt đúng property và restart riêng Trino65245 terminal0. Bảng Iceberg không đổi; Superset virtual datasets tiếp tục SQL. New virtual dataset cần refresh metadata cả lần tạo, đã sửa provision.
- Ingest/predict84146 terminal0: dữ liệu giờ10:00UTC, issue10:06:41UTC, target11:00UTC,2trạm operational. Report operational-forecast.json; forecast_actual actual chưa có giữ null. Model thật load lại từ volume.
- Dashboard8charts/native17YAML đã provision, requests994..1001 chart APIs đều200, screenshot dashboard-final.png đã xem đủ curves/metrics/operational2rows. Đang bổ sung format2dec và Gold-left-grid cho null gaps backtest, cần chụp lại cuối. Browser riêng airquality, auth ignored.
- Full unit+Spark integration86924 đang chạy; logs artifacts/local/tests-full.log. Collector sống, processor paused cho Spark jobs; phải resume cuối. Labs06/07/demo/walkthrough/script trích6snippets đã viết, links/status/secret/diff còn kiểm trước commit/push.

## STEP-016 — 2026-10-24T17:25:37+07:00 — Nghiệm thu cuối và Git base đã thay đổi

- Code checkpoint b7a544a và fix ba600f8 đã commit local, chưa push. Unit25pass, Spark13pass+4live skip ở tests-final76872 terminal0;4API live đã pass riêng trước đó. Test mới thêm nullable Bronze schema migration, original_ingested_at replay, stale suppress/model-after-issue guard, null metric guard.
- Replay47400 terminal0:168 public hourly events → Kafka topic riêng → Bronze/Silver168, Gold grid672, original_ingested_at168 được bảo toàn; report replay-isolation.json. Forecast retry61695 terminal0:2operational predictions giữ issued_at/value đầu tiên, report forecast-idempotency.json.
- Native import HTTP200 trước đó vẫn làm16layoutnodes dù chỉ8charts. Xem source Superset4.1.2 phát hiện meta.uuid bị thiếu: bổ sung chart_uuids đọc native export chính thức, layout giữ UUID. Provision/import82773 terminal0 và assert8nodes/8uniqueIDs/8UUID; chartrequests1393..1400 đều200. Screenshot cuối dashboard-final.png, không giữ bản lặp làm proof cuối.
- Processor69207 resume terminal0, Collector đang sống. Live status xác nhận7nativehealthchecks+catalogHTTP200,8daemons running, init exit0, Silver duplicate0; live-final-status.json.
- verify_repository: syntax/TOML/links/diff và credential thực tế scan sạch; source fingerprint/JUnit/UI trong final-verification.json. Script trích6snippets đã chạy lại đúng source; labs01–07/demo/architecture/dictionary/walkthrough hoàn thiện.
- GitHub PR#1 đã được merge bên ngoài tác vụ lúc09:08:15UTC vào main78fffbb; fetch xác nhận tree main bằng c5ab9fa (không có thay đổi cần mất). Không reopen/merge/forcepush. Sau commit docs sẽ tạo nhánh feat/lakehouse-ml-completion từ main và cherry-pick các commit local mới để mở draft PR tiếp theo; giữ nhánh cũ.
- Bước tiếp: commit docs/evidence, chuyển base sạch như trên, push/new draft PR/attach, đồng bộ context Git cuối. Goal chưa đánh complete trước khi bàn giao Git xong.

## STEP-017 — 2026-10-24T17:29:28+07:00 — Draft PR#2 và guard MERGE null trước bàn giao

- PR#1 merged main78fffbb có tree giống c5ab9fa. Đã giữ nhánh cũ, tạo feat/lakehouse-ml-completion từ main và cherry-pick b7a544a→10347f8, ba600f8→89594df,99d2ceb→d9a2bcf. Source fingerprint không đổi256c3f101f8f17ef133ab4b807fe9d77adb48f017560879182f26277fc6c422e. Không rewrite/forcepush/deletebranch.
- Đã push nhánh mới và tạo/attach draft PR#2: https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/2, base main/head đúng, OPEN+draft. PR#1 giữ nguyên đã merge.
- Rà code cuối phát hiện2edge cases MERGE: null series_kind không được coi key hợp lệ; ingested_at null cũ không match điều kiện > nên correction hợp lệ không phục hồi. Bổ sung kiểm mọi thành phần SILVER_KEYS và null-safe ordering, test quarantine/idempotency/recovery. Không liên quan nguồn thật hiện đã tải (đều valid), nhưng cần invariant khi có dữ liệu lỗi.
- Processor tạm pause lần nữa cho test20601, log artifacts/local/tests-final-null-guards.log; Collector/core vẫn chạy. Sau test phải resume processor, cập nhật reports/source fingerprint/snippets, commit/push fix+metadata, chốt Goal nếu đủ bằng chứng. Context/README/AGENTS/Goal prompt cập nhật PR#2.

## STEP-018 — 2026-10-24T17:35:01+07:00 — Kiểm chứng toàn bộ và bàn giao draft PR#2

- Code checkpoint e18e0b0 (fix null keys/timestamp correction) trên feat/lakehouse-ml-completion. New test20601 lần đầu bắt rejected duplicate do MERGE source chưa dedup; đã sửa latest_per_key(event_id) trước quarantine. Rerun26515 terminal0:25unit+14Spark pass,4API live skip;4API live đã pass riêng trước đó. Giữ failure log để trace, không đổi assertion.
- Processor12624 resume terminal0, continuous checkpoint tiếp tục; Collector/core sống. Toàn bộ criteria P1–P6 có proof: source/history reconciliation, duplicate/correction/late/gaps/restart/null guards, ML leakage/baseline/operational+retry/actual,8charts native import UUID, pruning/compaction/time travel. Source code fingerprint cập nhật trong final-verification.json;6snippets đã regenerate.
- PR#2 OPEN+draft đã attach; Git delivery dùng nhánh mới từ main78fffbb, không sửa PR#1 merged hay lịch sử đã push. Checklist và context được đồng bộ, final docs/evidence chuẩn bị commit/push cuối; sau xác nhận remote đồng bộ và tree sạch mới mark Goal complete.
- Giới hạn bàn giao: RF không thắng persistence nhất quán; predict theo lần gọi; backtest không giả historical availability; raw physical interval chưa rõ, dùng source/hours;2station/local small scale, không claim compaction làm query nhanh hơn.
- Tiếp tục sau bàn giao: dùng README/docs/demo/labs, không tự tạo Goal lại cho cùng công việc. Khi người dùng yêu cầu mở rộng, kiểm Git/PR/toolGoal hiện tại trước; không tự merge PR hoặc xóa volume.
