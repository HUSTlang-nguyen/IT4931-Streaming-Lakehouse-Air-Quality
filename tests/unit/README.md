# Unit tests

**Đã có:** test_collector.py và test_coverage.py, hoàn toàn offline.

Kiểm hành vi production: cửa sổ/UTC, HTTP retry, checkpoint ACK/crash/restart, raw archive retry, file/Kafka checkpoint tách, replay và profile dedup/correction/gap. Spark normalization và ML leakage sẽ được bổ sung cùng code tương ứng. Không mirror từng dòng implementation hoặc dùng fixtures như bằng chứng live.
