"""CLI Python production; lab gọi cùng service, không tạo logic nghiệp vụ riêng.

Ví dụ: air-quality inspect --sensor 13502154 --resource hours --start ... --end ...
Lệnh backfill lưu mốc thời gian theo run-name; lệnh live có --once để demo hữu hạn.
"""

import argparse
import json
import sys
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from filelock import FileLock

from air_quality.collector.openaq import OpenAQClient, OpenAQError
from air_quality.collector.publisher import JsonlPublisher, KafkaPublisher
from air_quality.collector.service import Collector, atomic_json, replay_archives
from air_quality.collector.state import StateStore
from air_quality.config.settings import SENSORS, Settings
from air_quality.contracts.events import iso_utc, time_windows, utc_datetime
from air_quality.observability.coverage import jsonl_events, profile_events
from air_quality.observability.evidence import evidence_context


def parser() -> argparse.ArgumentParser:
    """Công bố Collector, stack, Spark/ML và kiểm chứng qua cùng entrypoint."""
    root = argparse.ArgumentParser(description="Air Quality Streaming Lakehouse — OpenAQ / Spark / ML")
    root.add_argument("--env-file", type=Path, default=Path(".env"))
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("inspect", "backfill", "live"):
        command = commands.add_parser(name)
        command.add_argument("--sensor", type=int, action="append", choices=[s.sensor_id for s in SENSORS])
        command.add_argument("--resource", action="append", choices=["measurements", "hours"])
        command.add_argument("--sink", choices=["kafka", "jsonl"], default="jsonl" if name == "inspect" else "kafka")
        command.add_argument("--output", type=Path, default=Path("data/collected.jsonl"))
        command.add_argument("--start", type=utc_datetime)
        command.add_argument("--end", type=utc_datetime)
        command.add_argument("--run-name", default="history-180d" if name == "backfill" else name)
        command.add_argument("--once", action="store_true", help="live: chỉ chạy một chu kỳ")
    replay = commands.add_parser("replay")
    replay.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    replay.add_argument("--topic", default="air-quality.replay.demo")
    profile = commands.add_parser("profile", help="Thống kê nguồn JSONL offline, không gọi API")
    profile.add_argument("--input", type=Path, required=True)
    profile.add_argument("--start", type=utc_datetime, required=True)
    profile.add_argument("--end", type=utc_datetime, required=True)
    profile.add_argument("--output", type=Path, default=Path("artifacts/reports/source-coverage.json"))
    for name in ("start", "stop", "status"):
        operation = commands.add_parser(name)
        if name == "start":
            operation.add_argument("--services", nargs="+", choices=["kafka", "minio", "catalog", "postgres", "trino", "superset", "collector", "processor"])
            operation.add_argument("--no-build", action="store_true")
    query = commands.add_parser("query", help="SQL qua Trino của stack local")
    query.add_argument("sql")
    drain = commands.add_parser("drain", help="Gửi bản thu JSONL thật qua Kafka, giữ mode backfill/live")
    drain.add_argument("--input", type=Path, required=True)
    drain.add_argument("--run-name", default="source-backfill")
    drain.add_argument("--batch-size", type=int, default=1000)
    commands.add_parser("smoke")
    commands.add_parser("dashboard")
    commands.add_parser("benchmark")
    for action in ("train", "predict"):
        ml = commands.add_parser(action)
        ml.add_argument("--namespace", default="live")
    tests = commands.add_parser("test")
    tests.add_argument("--integration", action="store_true")
    tests.add_argument("--live", action="store_true")
    process = commands.add_parser("process")
    process.add_argument("--namespace", default="live")
    process.add_argument("--topic", default="air-quality.live")
    process.add_argument("--checkpoint", default="checkpoints/spark/live")
    process.add_argument("--max-offsets", type=int, default=20000)
    process.add_argument("--continuous", action="store_true")
    return root


def run_collection(args: argparse.Namespace, settings: Settings) -> None:
    """Điều phối lịch và resource; print thống kê sạch, không settings/key."""
    settings.require_api_key()
    settings = replace(settings, ingest_mode="backfill" if args.command == "backfill" else "live")
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    # Một Collector vận hành tại một thời điểm; limiter SQLite dùng lại nếu
    # thao tác khám phá ở process khác cũng dùng cùng state_dir.
    with FileLock(settings.state_dir / "collector.lock", timeout=1):
        state = StateStore(settings.state_dir / "collector.sqlite")
        try:
            reserve = lambda: state.reserve_request(settings.request_interval, settings.hourly_request_limit)
            with OpenAQClient(settings, reserve) as client:
                publisher = (KafkaPublisher(settings.bootstrap_servers, settings.topic) if args.sink == "kafka"
                             else JsonlPublisher(args.output))
                collector = Collector(settings, client, state, publisher)
                sensors = [s for s in SENSORS if not args.sensor or s.sensor_id in args.sensor]
                resources = args.resource or ["measurements", "hours"]
                while True:
                    now = datetime.now(timezone.utc).replace(microsecond=0)
                    if args.command == "backfill":
                        key = "range:" + args.run_name
                        saved = state.get(key)
                        if saved:
                            bounds = json.loads(saved)
                            start, end = utc_datetime(bounds["start"]), utc_datetime(bounds["end"])
                            if (args.start and args.start != start) or (args.end and args.end != end):
                                raise ValueError("run-name đã có khoảng cố định; chọn run-name khác nếu đổi start/end")
                        else:
                            end = args.end or now
                            start = args.start or end - timedelta(days=settings.backfill_days)
                            if start >= end:
                                raise ValueError("Cần start < end")
                            state.put(key, json.dumps({"start": iso_utc(start), "end": iso_utc(end)}))
                    elif args.command == "inspect":
                        end = args.end or now
                        start = args.start or end - timedelta(hours=1)
                        reconcile = False
                    else:
                        end = args.end or now
                        last_reconcile = state.get("last_reconcile")
                        reconcile = (last_reconcile is None or
                                     now - utc_datetime(last_reconcile) >= timedelta(hours=settings.reconcile_hours))
                        history = timedelta(days=settings.reconcile_days) if reconcile else timedelta(hours=settings.overlap_hours)
                        start = args.start or end - history
                    results = []
                    # Endpoint hours là series chính thức; giữ resource trong
                    # envelope để không nhầm với raw và tránh double counting.
                    for sensor in sensors:
                        for resource in resources:
                            for lower, upper in time_windows(start, end):
                                result = collector.collect_window(sensor, resource, lower, upper,
                                                                  args.run_name + ":" + args.command)
                                results.append(result)
                                print(json.dumps(result), flush=True)
                    atomic_json(settings.data_dir / "reports" / f"{args.command}-latest.json", {
                        "command": args.command, "sink": args.sink, "as_of": iso_utc(now), "results": results,
                    })
                    if args.command == "live" and reconcile:
                        state.put("last_reconcile", iso_utc(now))
                    if args.command != "live" or args.once:
                        return
                    time.sleep(settings.poll_seconds)
        finally:
            state.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint; trả exit code rõ, Ctrl+C dừng mà không mất checkpoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        if args.command == "benchmark":
            from air_quality.observability.benchmark import run
            print(json.dumps(run(args.env_file)))
            return 0
        if args.command == "dashboard":
            from air_quality.dashboard import provision
            print(json.dumps(provision(args.env_file), ensure_ascii=False))
            return 0
        if args.command in {"start", "stop", "status", "query", "smoke", "process", "test", "train", "predict"}:
            from air_quality import operations
            if args.command == "start":
                operations.start(args.env_file, args.services, not args.no_build)
            elif args.command == "stop":
                operations.stop(args.env_file)
            elif args.command == "status":
                operations.status(args.env_file)
            elif args.command == "query":
                print(json.dumps(operations.query_trino(args.sql), ensure_ascii=False))
            elif args.command == "test":
                operations.run_tests(args.env_file, args.integration, args.live)
            else:
                job_args = []
                if args.command == "process":
                    job_args = ["--namespace", args.namespace, "--topic", args.topic, "--checkpoint", args.checkpoint,
                                "--max-offsets", str(args.max_offsets), *(["--continuous"] if args.continuous else [])]
                elif args.command in {"train", "predict"}:
                    job_args = ["--namespace", args.namespace]
                operations.run_spark_job(args.env_file, "ingest" if args.command == "process" else args.command, job_args)
            return 0
        if args.command == "profile":
            report = profile_events(jsonl_events(args.input), args.start, args.end)
            report["provenance"] = evidence_context(args.input)
            atomic_json(args.output, report)
            print(json.dumps({"output": str(args.output), "unique_records": report["unique_records"]}))
            return 0
        settings = Settings.from_env(args.env_file)
        if args.command == "drain":
            from air_quality.collector.archive import drain_jsonl
            state = StateStore(settings.state_dir / "collector.sqlite")
            try:
                print(json.dumps(drain_jsonl(args.input, KafkaPublisher(settings.bootstrap_servers, settings.topic),
                                             state, settings.state_dir, args.run_name, args.batch_size)))
            finally:
                state.close()
            return 0
        if args.command == "replay":
            configured = replace(settings, ingest_mode="replay", topic=args.topic)
            count = replay_archives(args.raw_dir, KafkaPublisher(configured.bootstrap_servers, configured.topic))
            print(json.dumps({"mode": "replay", "topic": configured.topic, "published": count}))
        else:
            run_collection(args, settings)
        return 0
    except (ValueError, OpenAQError, RuntimeError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Đã dừng; giữ nguyên checkpoint để resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
