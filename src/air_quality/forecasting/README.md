# forecasting

features.py: exact-hour joins current/lag1/2/3/24, label+1h, chronological split/purge. model.py: Spark MLlib RF mỗi trạm, validation chọn depth, held-out test/persistence, model manifest/version, backtest/operational forecasts và actual enrichment.

Không impute gaps, không dùng target trong features; backtest final snapshot không giả availability quá khứ. Operational kiểm toàn bộ input ingested_at, model trained_at và target còn tương lai. predict là job theo lần gọi, chưa có scheduler nền.

[Lab06](../../../labs/06-forecasting.md), [ML tests](../../../tests/integration/test_forecasting.py).
