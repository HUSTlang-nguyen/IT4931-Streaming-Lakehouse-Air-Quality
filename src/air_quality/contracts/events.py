"""Envelope Kafka v1 và công cụ thời gian dùng chung cho live/backfill/replay.

Giữ raw payload JSON riêng; Silver sẽ quyết định hợp lệ, không xóa raw vì
giá trị âm/null. series_kind phân biệt measurements với hourly nguồn OpenAQ.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from air_quality.config.settings import Sensor


def utc_datetime(value: str | datetime) -> datetime:
    """Parse ISO aware thành UTC; từ chối naive để tránh lệch bảy giờ âm thầm."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp bắt buộc có timezone hoặc Z")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    """Chuẩn hóa ISO UTC cho URL/checkpoint, độc lập timezone host."""
    return utc_datetime(value).isoformat().replace("+00:00", "Z")


def time_windows(start: datetime, end: datetime, days: int = 7) -> Iterator[tuple[datetime, datetime]]:
    """Chia khoảng dài thành cửa sổ có mốc cố định để pagination và resume.

    API có thể lặp biên giữa hai cửa sổ. Không tùy tiện xóa bản ghi biên;
    Silver sẽ chống trùng theo sensor/resource/khoảng đo thay vì row offset.
    """
    cursor, end = utc_datetime(start), utc_datetime(end)
    if cursor >= end or days <= 0:
        raise ValueError("Cần start < end và days > 0")
    while cursor < end:
        boundary = min(cursor + timedelta(days=days), end)
        yield cursor, boundary
        cursor = boundary


def stable_hash(value: Any) -> str:
    """Hash JSON canonical để ID không phụ thuộc thứ tự key trong payload."""
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def make_event(sensor: Sensor, resource: str, raw: dict[str, Any], metadata: dict[str, Any],
               job_id: str, page: int, index: int, ingested_at: datetime,
               ingest_mode: str, start: datetime, end: datetime) -> dict[str, Any]:
    """Bao một số đo với provenance, giữ ID ổn định nếu retry cùng trang/job.

    event_id là định danh lần quan sát, khác khóa business Silver. Retry sau
    crash không tạo thêm Bronze logic; lần thu thập overlap khác vẫn truy vết
    được, còn correction được giải quyết ở Silver theo thời điểm quan sát.
    """
    if resource not in {"measurements", "hours"}:
        raise ValueError("resource phải là measurements/hours")
    identity = [job_id, page, index, sensor.sensor_id, resource, raw]
    return {
        "schema_version": 1,
        "event_id": stable_hash(identity),
        "job_id": job_id,
        "location_id": sensor.location_id,
        "sensor_id": sensor.sensor_id,
        "station_name": sensor.station_name,
        "parameter_name": sensor.parameter,
        "series_kind": resource,
        "ingest_mode": ingest_mode,
        "ingested_at": iso_utc(ingested_at),
        "request_from": iso_utc(start),
        "request_to": iso_utc(end),
        "raw_payload": json.dumps(raw, ensure_ascii=False, sort_keys=True, allow_nan=False),
        "location_metadata": json.dumps(metadata, ensure_ascii=False, sort_keys=True),
    }
