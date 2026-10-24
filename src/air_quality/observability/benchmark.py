"""Điều phối benchmark Spark + Trino, báo cáo measurements không hứa tăng tốc."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from air_quality.collector.service import atomic_json
from air_quality.operations import ROOT, query_trino, run_spark_job


def trino_measure(table: str) -> dict:
    """Một warmup và ba query; stats là số thực Trino trả về, không ước lượng."""
    sql = f"SELECT sensor_id,count(*) n,CAST(sum(CAST(value AS DECIMAL(25,8))) AS DOUBLE) total FROM {table} WHERE period_end>=TIMESTAMP '2026-07-01' AND period_end<TIMESTAMP '2026-08-01' GROUP BY sensor_id ORDER BY sensor_id"
    runs = []
    for index in range(4):
        start = time.perf_counter()
        response = query_trino(sql)
        if index:
            runs.append({"wall_seconds": time.perf_counter() - start, "stats": response["stats"], "query_id": response["id"]})
    plan = query_trino("EXPLAIN (TYPE DISTRIBUTED) " + sql)["data"]
    return {"sql": sql, "result": response["data"], "runs": runs, "plan": plan}


def run(env_file: Path) -> dict:
    """Mỗi lần giữ namespace riêng, không drop bảng/snapshot/volume sau đo."""
    namespace = "experiment_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_spark_job(env_file, "benchmark-prepare", ["--namespace", namespace])
    prepared = json.loads((ROOT / "artifacts/local/benchmark-prepare.json").read_text())
    table = f"iceberg.{namespace}.observations"
    before = trino_measure(table)
    run_spark_job(env_file, "benchmark-compact", ["--namespace", namespace])
    compacted = json.loads((ROOT / "artifacts/local/benchmark-compact.json").read_text())
    after = trino_measure(table)
    assert before["result"] == after["result"]
    snapshots = [compacted[phase]["snapshot"] for phase in ("before", "after")]
    travel = {str(snapshot): query_trino(f"SELECT count(*) FROM {table} FOR VERSION AS OF {snapshot}")["data"][0][0] for snapshot in snapshots}
    assert len(set(travel.values())) == 1
    report = {"prepared": prepared, "compacted": compacted, "trino_before": before, "trino_after": after,
              "trino_time_travel_counts": travel, "limitations": "Small local dataset; intentionally fragmented files. Timing is measured, no general speedup claim; caches are not flushed."}
    atomic_json(ROOT / "artifacts/reports/iceberg-benchmark.json", report)
    return {"report": "artifacts/reports/iceberg-benchmark.json", "namespace": namespace, "time_travel": travel}
