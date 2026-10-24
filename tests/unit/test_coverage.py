"""Coverage phải dedup, xử lý biên và không che missing bằng số 0."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from air_quality.config.settings import SENSORS
from air_quality.contracts.events import iso_utc, make_event, utc_datetime
from air_quality.observability.coverage import profile_events


START = utc_datetime("2026-10-23T00:00:00Z")


def hourly(hour: int, value: float, observation: int = 0):
    finish = START + timedelta(hours=hour)
    raw = {"value": value, "parameter": {"units": "µg/m³"},
           "period": {"datetimeFrom": {"utc": iso_utc(finish - timedelta(hours=1))},
                      "datetimeTo": {"utc": iso_utc(finish)}}, "coverage": {"percentCoverage": 1200}}
    return make_event(SENSORS[0], "hours", raw, {}, f"job-{observation}", 1, 0,
                      START + timedelta(days=1, minutes=observation), "backfill", START, START + timedelta(days=1))


def test_dedup_correction_range_and_gaps():
    first, corrected = hourly(1, 20), hourly(1, 25, observation=1)
    # Border hour=0 bị loại; giữa giờ 1 và 3 thiếu một bin, không điền zero.
    report = profile_events([hourly(0, 0), first, corrected, hourly(3, 0)], START, START + timedelta(hours=4))
    row = report["series"][0]
    assert report["outside_range"] == 1 and report["duplicate_keys"] == 1
    assert row["unique_records"] == 2 and row["hourly_availability_percent"] == 50
    assert row["maximum_internal_gap_seconds"] == 7200
    assert row["minimum_valid_value"] == 0 and row["maximum_valid_value"] == 25
    assert row["source_coverage_above_100_records"] == 2


def test_invalid_and_flagged_are_reported_separately():
    event = hourly(1, -2)
    raw = json.loads(event["raw_payload"])
    raw["flagInfo"] = {"hasFlags": True}
    event["raw_payload"] = json.dumps(raw)
    row = profile_events([event], START, START + timedelta(hours=1))["series"][0]
    assert row["invalid_records"] == row["flagged_records"] == 1
    assert row["minimum_valid_value"] is None


def test_replay_not_mixed_with_source():
    event = hourly(1, 20)
    event["ingest_mode"] = "replay"
    with pytest.raises(ValueError, match="replay"):
        profile_events([event], START, START + timedelta(hours=2))


def test_captured_public_payloads_work_offline_without_api_key():
    """Mẫu schema thật được cố định, khác synthetic test và không gọi mạng."""
    samples = json.loads((Path(__file__).parents[1] / "fixtures/openaq-hourly-sample.json").read_text(encoding="utf-8"))
    events = []
    sensors = {sensor.sensor_id: sensor for sensor in SENSORS}
    for sample in samples["samples"]:
        events.append(make_event(sensors[sample["sensor_id"]], "hours", sample["row"], {}, "fixture", 1, 0,
                                 utc_datetime(sample["captured_at"]), "backfill", START, START + timedelta(days=1)))
    report = profile_events(events, START, START + timedelta(days=1))
    assert len(report["series"]) == 4
    assert all(row["unique_records"] == 1 and row["invalid_records"] == 0 for row in report["series"])
