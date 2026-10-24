"""Thống kê dữ liệu nguồn đã tải, không thay cho bảng Gold hoặc sensor QA.

Đọc envelope production theo dòng để không nạp JSONL lớn vào RAM một lần.
Dedup bằng khóa logic và giới hạn cửa sổ trước khi tính tỷ lệ availability.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Iterator

from air_quality.contracts.events import iso_utc, utc_datetime


def jsonl_events(path: Path) -> Iterator[dict[str, Any]]:
    """Đọc JSONL đã lưu, fail rõ dòng sai; không in nội dung để tránh log raw lớn."""
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except ValueError:
                raise ValueError(f"JSONL không hợp lệ tại dòng {number}") from None


def profile_events(events: Iterable[dict[str, Any]], start: datetime, end: datetime) -> dict[str, Any]:
    """Tính unique/count/gap cho (start,end], giờ nguồn cần hai biên tròn giờ.

    Latest observation được chọn theo ingested_at, event_id làm tie-break ổn
    định. Giữ nguyên raw interval; không gắn raw cadence 5 phút thành expected
    coverage. Hour availability là số bin giờ có nguồn, không sensor accuracy.
    """
    start, end = utc_datetime(start), utc_datetime(end)
    if start >= end or any(dt.minute or dt.second or dt.microsecond for dt in (start, end)):
        raise ValueError("Profile cần start < end và biên UTC tròn giờ")
    latest: dict[tuple, tuple] = {}
    received, outside, duplicates = 0, 0, 0
    for event in events:
        if event["ingest_mode"] == "replay":
            raise ValueError("Profile nguồn không được trộn dữ liệu replay")
        received += 1
        raw = json.loads(event["raw_payload"])
        begin = utc_datetime(raw["period"]["datetimeFrom"]["utc"])
        finish = utc_datetime(raw["period"]["datetimeTo"]["utc"])
        if not start < finish <= end:
            outside += 1
            continue
        key = (event["sensor_id"], event["series_kind"], begin, finish)
        observation = (utc_datetime(event["ingested_at"]), event["event_id"])
        if key in latest:
            duplicates += 1
        if key not in latest or observation > latest[key][0]:
            latest[key] = (observation, raw, event["location_id"], event["parameter_name"])
    groups: dict[tuple, list] = defaultdict(list)
    for key, payload in latest.items():
        groups[key[:2]].append((key[2], key[3], payload[1], payload[2], payload[3]))
    result = []
    for (sensor_id, kind), rows in sorted(groups.items()):
        rows.sort(key=lambda row: row[1])
        ends = sorted({row[1] for row in rows})
        deltas = [(right - left).total_seconds() for left, right in zip(ends, ends[1:])]
        cadence = Counter(deltas).most_common(1)[0][0] if deltas else None
        invalid, flagged, overcoverage, valid_values = 0, 0, 0, []
        for begin, finish, raw, _, _ in rows:
            value = raw.get("value")
            valid = isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) and value >= 0
            unit = (raw.get("parameter", {}).get("units") or "").replace("μ", "µ")
            valid = valid and unit == "µg/m³" and begin < finish
            if kind == "hours":
                valid = valid and (finish - begin).total_seconds() == 3600 and finish.minute == finish.second == 0
            flagged += int(bool((raw.get("flagInfo") or {}).get("hasFlags")))
            invalid += int(not valid)
            coverage = raw.get("coverage") or {}
            overcoverage += int((coverage.get("percentCoverage") or 0) > 100)
            if valid:
                valid_values.append(value)
        expected = int((end - start).total_seconds() / 3600) if kind == "hours" else None
        result.append({
            "sensor_id": sensor_id, "location_id": rows[0][3], "parameter": rows[0][4],
            "series_kind": kind, "unique_records": len(rows), "distinct_end_times": len(ends),
            "expected_hourly_bins": expected,
            "hourly_availability_percent": round(len(ends) / expected * 100, 3) if expected else None,
            "observed_modal_gap_seconds": cadence, "maximum_internal_gap_seconds": max(deltas, default=0),
            "first_end": iso_utc(ends[0]), "last_end": iso_utc(ends[-1]),
            "invalid_records": invalid, "flagged_records": flagged,
            "source_coverage_above_100_records": overcoverage,
            "minimum_valid_value": min(valid_values, default=None), "maximum_valid_value": max(valid_values, default=None),
        })
    return {"range_start_exclusive": iso_utc(start), "range_end_inclusive": iso_utc(end),
            "events_read": received, "outside_range": outside, "duplicate_keys": duplicates,
            "unique_records": len(latest), "series": result,
            "interpretation": "Availability của dữ liệu nguồn, không chứng nhận độ chính xác cảm biến; không suy diễn raw interval/cadence."}
