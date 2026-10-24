# Lab 07 — Partition pruning, compaction và time travel

## Điều kiện và kiến thức

Gold/Silver thật đã có, core chạy, processor paused để dành RAM cho job Spark. Không writer nào chạm namespace experiment mới; live vẫn được giữ. Iceberg partition transform months(period_end) không đòi người dùng thêm cột month vào mỗi query.

```text
Silver snapshot → copy không nhân bản → 4 append nhỏ → đo trước
→ rewrite_data_files → đo sau → exceptAll hai chiều + time travel
```

[experiments.py](../src/air_quality/processing/experiments.py) chuẩn bị và compact; [benchmark.py](../src/air_quality/observability/benchmark.py) đo thêm Trino. Mỗi run tạo namespace experiment_timestamp riêng và giữ lại mọi snapshot.

## Chạy và kiểm

```powershell
docker compose --env-file .env -f infra/compose.yaml --profile pipeline stop processor
.venv/Scripts/python.exe -m air_quality.cli benchmark
.venv/Scripts/python.exe -m air_quality.cli start --services processor --no-build
```

Job copy Silver tại snapshot cố định, chia hash key thành bốn phần disjoint và append để chủ động tạo small files. Không nhân bản hàng, không gọi đây là tải lớn. Trước/sau mỗi phép đo có warmup một query, ba lần đo; không flush cache. Thời gian cả run đã quan sát khoảng2 phút, tùy máy.

[iceberg-benchmark.json](../artifacts/reports/iceberg-benchmark.json) giữ SQL, Spark/Trino plans, số files/bytes, scanned files, query stats và snapshot IDs. Bộ dữ liệu202.537 hàng thật được copy. Query tháng7 trước compaction đọc4/28 files, sau đọc1/7 files. Có predicate trong scan plan; các partition tháng khác không cần đọc.

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Data files | 28 | 7 |
| Data bytes | 10.515.307 | 9.327.132 |
| Files có hàng tháng7 | 4 | 1 |
| Trino physicalInputBytes (lần đo đầu) | 1.651.876 | 1.457.386 |
| Trino client median3 lần (giây) | 2,178 | 2,204 |

Không suy ra query nhanh hơn từ số files giảm: client thời gian ở run này không giảm, gồm overhead HTTP/polling. Đây là demo laptop/quy mô nhỏ, không kết luận hiệu năng cluster.

Compaction snapshot trước6771701738734041956, sau3857799040961249093; count202.537 ở cả hai qua Spark và Trino `FOR VERSION AS OF`. `exceptAll` hai chiều bằng0 chứng minh nguyên hàng không thay đổi, bao gồm duplicate multiplicity. Không expire snapshots, không xóa volume.

## Chi tiết khó và lỗi đã gặp

SUM(double) có thể lệch vài chữ số cuối khi rewrite thay thứ tự cộng. Validation tổng dùng decimal(25,8), và đối chiếu nguyên hàng exceptAll độc lập để không bỏ qua lỗi dữ liệu. Lần đầu assertion floating sum fail đã giữ nguyên namespace và log; rerun mới kiểm đầy đủ.

File metadata byte count là tổng data file hiện tại, không gồm metadata/snapshot cũ. Data file giảm không đồng nghĩa disk volume giảm vì time travel còn giữ files cũ. `_file` là metadata column Iceberg, đếm file có hàng khớp filter; kết hợp plan/partition và Trino physical scan stats để hiểu pruning.

Bài tập: đổi query filter tháng khác trong bản sao lab, so số files/scan bytes; giữ schema partition và source snapshot như cũ để phép so có ý nghĩa. Không chạy procedure lên bảng live đang có processor writer.

Tài liệu chính thức: [Iceberg1.9.2 procedures](https://iceberg.apache.org/docs/1.9.2/spark-procedures/), [Spark3.5.6 RF](https://spark.apache.org/docs/3.5.6/api/python/reference/api/pyspark.ml.regression.RandomForestRegressor.html).
