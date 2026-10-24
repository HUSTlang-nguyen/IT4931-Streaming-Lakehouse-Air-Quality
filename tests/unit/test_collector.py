"""Lab kiểm thử hành vi Collector: hoàn toàn offline, không đọc key cục bộ.

MockTransport chỉ giả ranh giới HTTP. Service/checkpoint/envelope là production
code thật, nhờ đó test crash/ACK kiểm được tình huống có thể gây mất dữ liệu.
"""

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from air_quality.cli import parser
from air_quality.collector.openaq import OpenAQClient, OpenAQError, retry_delay
from air_quality.collector.publisher import JsonlPublisher
from air_quality.collector.service import Collector, replay_archives
from air_quality.collector.state import StateStore
from air_quality.config.settings import SENSORS, Settings
from air_quality.contracts.events import iso_utc, make_event, time_windows, utc_datetime


START = utc_datetime("2026-10-23T00:00:00Z")
END = START + timedelta(days=1)


def measurement(value: float, minutes: int) -> dict:
    """Payload synthetic: interval 1h nhưng event time có thể cách 5 phút."""
    return {"value": value, "parameter": {"name": "pm25", "units": "µg/m³"},
            "period": {"interval": "01:00:00", "datetimeFrom": {"utc": iso_utc(START - timedelta(hours=1) + timedelta(minutes=minutes))},
                       "datetimeTo": {"utc": iso_utc(START + timedelta(minutes=minutes))}},
            "flagInfo": {"hasFlags": False}}


class AcknowledgingPublisher:
    """Test double mô phỏng broker ACK hoặc lỗi; giữ lại đúng envelope đã gửi."""

    destination = "fake-broker:test"

    def __init__(self, fail_once: bool = False) -> None:
        self.fail_once = fail_once
        self.batches: list[list[dict]] = []

    def publish(self, events: list[dict]) -> int:
        self.batches.append(events)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("synthetic delivery timeout")
        return len(events)


def setup_collector(tmp_path: Path, publisher: AcknowledgingPublisher, pages: dict[int, list[dict]]):
    """Tạo adapter mock + SQLite thật và trả request log để đối chiếu pagination."""
    settings = Settings(api_key="synthetic-test-key", data_dir=tmp_path / "data",
                        state_dir=tmp_path / "state", page_size=2, request_interval=0)
    state = StateStore(tmp_path / "state" / "test.sqlite")
    requests: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if "locations" in request.url.path:
            rows = [{"id": SENSORS[0].location_id, "sensors": [
                {"id": SENSORS[0].sensor_id, "parameter": {"name": "pm25"}}
            ]}]
        else:
            rows = pages[int(request.url.params["page"])]
        return httpx.Response(200, json={"meta": {"found": ">2"}, "results": rows})

    client = OpenAQClient(settings, lambda: None, transport=httpx.MockTransport(handle))
    return Collector(settings, client, state, publisher), client, state, requests


def test_timezone_and_naive_rejection():
    assert utc_datetime("2026-10-23T07:00:00+07:00") == START
    assert iso_utc(START) == "2026-10-23T00:00:00Z"
    with pytest.raises(ValueError, match="timezone"):
        utc_datetime("2026-10-23T07:00:00")


def test_windows_fixed_and_exact_end():
    intervals = list(time_windows(START, START + timedelta(days=15)))
    assert len(intervals) == 3
    assert intervals[0][1] == intervals[1][0]
    assert intervals[-1][1] == START + timedelta(days=15)
    with pytest.raises(ValueError):
        list(time_windows(START, START))


def test_envelope_id_retry_and_resource_separation():
    arguments = dict(sensor=SENSORS[0], resource="measurements", raw=measurement(20.3, 5),
                     metadata={}, job_id="job", page=1, index=0, ingested_at=START,
                     ingest_mode="live", start=START, end=END)
    first = make_event(**arguments)
    arguments["ingested_at"] = END
    retry = make_event(**arguments)
    assert first["event_id"] == retry["event_id"]
    arguments["resource"] = "hours"
    assert make_event(**arguments)["event_id"] != first["event_id"]
    assert json.loads(first["raw_payload"])["value"] == 20.3


def test_pagination_handles_string_found_and_resume(tmp_path):
    publisher = AcknowledgingPublisher()
    collector, client, state, requests = setup_collector(tmp_path, publisher, {
        1: [measurement(1, 5), measurement(2, 10)], 2: [measurement(3, 15)]})
    try:
        first = collector.collect_window(SENSORS[0], "measurements", START, END, "test")
        retry = collector.collect_window(SENSORS[0], "measurements", START, END, "test")
        assert first["rows_acknowledged"] == 3
        assert retry["published_this_call"] == 0
        assert len(requests) == 3  # một metadata và hai trang, không query lại job xong.
        assert len(publisher.batches) == 2
    finally:
        client.close()
        state.close()


def test_crash_before_ack_reuses_archived_page(tmp_path):
    publisher = AcknowledgingPublisher(fail_once=True)
    collector, client, state, requests = setup_collector(tmp_path, publisher, {
        1: [measurement(1, 5), measurement(2, 10)], 2: [measurement(3, 15)]})
    try:
        with pytest.raises(RuntimeError, match="delivery timeout"):
            collector.collect_window(SENSORS[0], "measurements", START, END, "crash")
        archives = list((tmp_path / "data/raw").glob("*/page-000001.json"))
        assert len(archives) == 1
        job_id = archives[0].parent.name
        assert state.progress(job_id) == (1, 0, False)
        result = collector.collect_window(SENSORS[0], "measurements", START, END, "crash")
        assert result["rows_acknowledged"] == 3
        assert publisher.batches[0] == publisher.batches[1]
        assert sum("page=1" in request for request in requests) == 1
    finally:
        client.close()
        state.close()


def test_repeated_page_stops_instead_of_infinite_loop(tmp_path):
    rows = [measurement(1, 5), measurement(2, 10)]
    collector, client, state, _ = setup_collector(tmp_path, AcknowledgingPublisher(), {1: rows, 2: rows})
    try:
        with pytest.raises(RuntimeError, match="lặp trang"):
            collector.collect_window(SENSORS[0], "measurements", START, END, "duplicate-page")
    finally:
        client.close()
        state.close()


def test_file_sink_does_not_poison_kafka_checkpoint(tmp_path):
    collector, client, state, _ = setup_collector(tmp_path, AcknowledgingPublisher(), {1: [measurement(1, 5)]})
    try:
        collector.publisher = JsonlPublisher(tmp_path / "capture.jsonl")
        file_result = collector.collect_window(SENSORS[0], "measurements", START, END, "shared-name")
        collector.publisher = AcknowledgingPublisher()
        kafka_result = collector.collect_window(SENSORS[0], "measurements", START, END, "shared-name")
        assert file_result["job_id"] != kafka_result["job_id"]
        assert kafka_result["published_this_call"] == 1
    finally:
        client.close()
        state.close()


def test_replay_tags_and_preserves_source_archive(tmp_path):
    collector, client, state, _ = setup_collector(tmp_path, AcknowledgingPublisher(), {1: [measurement(1, 5)]})
    try:
        collector.collect_window(SENSORS[0], "measurements", START, END, "original")
        archive = next((tmp_path / "data/raw").glob("*/page-*.json"))
        original = archive.read_bytes()
        publisher = AcknowledgingPublisher()
        assert replay_archives(tmp_path / "data/raw", publisher) == 1
        event = publisher.batches[0][0]
        assert event["ingest_mode"] == "replay"
        assert "original_ingested_at" in event
        assert archive.read_bytes() == original
    finally:
        client.close()
        state.close()


@pytest.mark.parametrize("status", [401, 403, 422])
def test_auth_or_validation_not_retried_and_secret_hidden(status):
    calls = []
    settings = Settings(api_key="never-log-this-secret")
    assert "never-log-this-secret" not in repr(settings)
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    with OpenAQClient(settings, lambda: calls.append(1), transport) as client:
        with pytest.raises(OpenAQError) as error:
            client.get("sensors/1")
        assert "never-log-this-secret" not in str(error.value)
        assert calls == [1]


def test_rate_limit_retry_after_and_budget_each_attempt():
    sleeps, calls = [], []
    responses = iter([httpx.Response(429, headers={"Retry-After": "3"}),
                      httpx.Response(503), httpx.Response(200, json={"results": []})])
    with OpenAQClient(Settings(api_key="synthetic"), lambda: calls.append(1),
                      httpx.MockTransport(lambda request: next(responses)), sleep=sleeps.append) as client:
        assert client.get("sensors/1")["results"] == []
    assert sleeps == [3.0, 2.0]
    assert len(calls) == 3


def test_bounded_retry_on_transport_failure():
    calls, sleeps = [], []

    def timeout(request):
        raise httpx.ReadTimeout("synthetic timeout")

    with OpenAQClient(Settings(api_key="synthetic", max_attempts=2), lambda: calls.append(1),
                      httpx.MockTransport(timeout), sleep=sleeps.append) as client:
        with pytest.raises(OpenAQError, match="2 lần"):
            client.get("sensors/1")
    assert len(calls) == 2 and sleeps == [1.0]


def test_http_date_retry_after():
    assert retry_delay("Fri, 23 Oct 2026 00:00:10 GMT", 0, START) == 10
    assert retry_delay("invalid", 2, START) == 4


def test_persisted_budget_across_store_restart(tmp_path):
    clock = [0.0]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    path = tmp_path / "state.sqlite"
    first = StateStore(path)
    first.reserve_request(1, 2, lambda: clock[0], sleep)
    first.close()
    second = StateStore(path)
    try:
        second.reserve_request(1, 2, lambda: clock[0], sleep)
        second.reserve_request(1, 2, lambda: clock[0], sleep)
        assert sleeps[0] == 1
        assert clock[0] >= 3600
    finally:
        second.close()


def test_bad_replay_topic_and_key_destination_rejected():
    with pytest.raises(ValueError, match="Replay"):
        Settings(ingest_mode="replay")
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(base_url="https://other.example/v3")
    with pytest.raises(ValueError, match="Thiếu"):
        Settings().require_api_key()
    settings = replace(Settings(), ingest_mode="replay", topic="air-quality.replay.demo")
    assert settings.topic.endswith("demo")


def test_inspect_defaults_to_file_not_live_broker():
    arguments = parser().parse_args(["inspect"])
    assert arguments.sink == "jsonl"
