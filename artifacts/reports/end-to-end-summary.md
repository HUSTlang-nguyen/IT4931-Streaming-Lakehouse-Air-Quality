# Nghiệm thu Air Quality Lakehouse

Code checkpoint e18e0b0, nhánh feat/lakehouse-ml-completion, [draft PR#2](https://github.com/HUSTlang-nguyen/IT4931-Streaming-Lakehouse-Air-Quality/pull/2). PR#1 đã được merge bên ngoài tác vụ; không rewrite lịch sử, không xóa branch/volume. Source fingerprint và revision/dirty tại từng lần đo nằm trong JSON reports.

| Tiêu chí | Bằng chứng thực tế |
|---|---|
| Nguồn |180 ngày cố định,202.041 unique raw/hourly,4sensor; coverage thực91,597–93,981%, hourly gap87h |
| E2E | Kafka ACK202.041 → Structured Streaming11batches → Bronze/Silver202.041 tại historical snapshots → Trino/Superset |
| Chất lượng | Grid17280hourly bins,1184missing null; correction/late/invalid/quarantine/replay/schema/null-key guards đã kiểm |
| Restart | Counts trước/sau/resume bằng nhau, Silver duplicate0; giữ named volumes/checkpoint |
| Kiểm thử |25 unit +14 Spark/Iceberg pass;4API live pass riêng;4live skip đúng chủ đích ở run offline cuối |
| ML |2RF MLlib models,30trees seed42/depth8 chọn bằng validation, chronological70/15/15 có purge; persistence cùng test mẫu |
| Forecast |2operational issue17:06VN target18:00VN, retry giữ forecast đầu; actual chưa có null, cập nhật khi gọi predict sau đó |
| Dashboard |8charts,8unique UUID layout nodes sau import,17nativeYAML, chart APIs200 và visual QA |
| Iceberg |202537 hàng thật copy riêng;28→7files, nguyên hàng exceptAll0, tháng7chạm4→1files, Spark/Trino time travel cùng count |
| Tài liệu |Labs01–07, architecture/dictionary/walkthrough/demo,6source snippets10–25dòng, context và log STEP nối tiếp |

RF MAE/RMSE ĐHBK11,394/16,664 vs persistence11,747/15,097 (n555); Nhân Chính6,781/9,421 vs5,728/7,283 (n649), µg/m³. RF chưa thắng baseline nhất quán. Client median benchmark2,178→2,204giây, không suy ra tăng tốc chung từ file count giảm.

Gold/ML dùng mean nguồn /hours đã kiểm contract; physical semantics raw interval1h/cadence5min chưa được giải thích. Backtest là hồi cứu snapshot hiện tại, không giả availability trong quá khứ. Hai trạm không đại diện toàn Hà Nội. Local single-node không HA; forecast chạy bằng lệnh predict, chưa có scheduler ML nền. Raw/model/auth/secrets/log lớn không vào Git.

[Chỉ mục reports](../README.md), [final checks](final-verification.json), [ML](ml-evaluation.json), [benchmark](iceberg-benchmark.json), [restart](restart-persistence.json), [replay](replay-isolation.json), [forecast retry](forecast-idempotency.json), [demo](../../docs/demo.md).
