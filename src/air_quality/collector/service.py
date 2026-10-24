"""Điều phối metadata → trang API → raw archive → publisher ACK → checkpoint.

Lab quan trọng: không commit checkpoint trước ACK. Raw page archive bất biến
giúp retry đúng envelope sau crash và cũng là input cho replay qua Kafka.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

from air_quality.collector.openaq import OpenAQClient
from air_quality.collector.publisher import Publisher
from air_quality.collector.state import StateStore
from air_quality.config.settings import Sensor, Settings
from air_quality.contracts.events import iso_utc, make_event, stable_hash


def atomic_json(path: Path, payload: Any) -> None:
    """Ghi file tạm rồi replace để crash không để lại JSON nửa trang.

    Caller phải bảo vệ cùng path bằng job lock. Không đưa credentials vào
    payload; file archive chỉ chứa measurements và provenance công khai.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class Collector:
    """Service không tự tạo thread/daemon; CLI quyết định lịch chạy và dừng."""

    def __init__(self, settings: Settings, client: OpenAQClient, state: StateStore,
                 publisher: Publisher) -> None:
        self.settings, self.client, self.state, self.publisher = settings, client, state, publisher

    def location_metadata(self, sensor: Sensor) -> dict[str, Any]:
        """Lấy vị trí/provider/sensor cho provenance; cache 5 phút trong file.

        Kiểm tra parameter từ metadata để không ghép sai sensor khi nguồn đổi.
        Cache không chứa header key. Thất bại metadata không bị nuốt âm thầm.
        """
        path = self.settings.data_dir / "metadata" / f"{sensor.location_id}.json"
        now = datetime.now(timezone.utc).timestamp()
        if path.exists() and now - path.stat().st_mtime < 300:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        else:
            rows = self.client.get(f"locations/{sensor.location_id}")["results"]
            if len(rows) != 1 or rows[0].get("id") != sensor.location_id:
                raise ValueError(f"Metadata location không khớp: {sensor.location_id}")
            metadata = rows[0]
            atomic_json(path, metadata)
        matching = [row for row in metadata.get("sensors", []) if row.get("id") == sensor.sensor_id]
        if len(matching) != 1 or matching[0].get("parameter", {}).get("name") != sensor.parameter:
            raise ValueError(f"Sensor/parameter không còn khớp metadata: {sensor.sensor_id}")
        return metadata

    def collect_window(self, sensor: Sensor, resource: str, start: datetime,
                       end: datetime, run_name: str) -> dict[str, Any]:
        """Thu một sensor/khoảng, resume trang chưa ACK; trả thống kê có nguồn.

        meta.found có thể là chuỗi '>1000', vì vậy không ép int để phân trang.
        Trang ngắn/kết quả rỗng mới kết thúc; trang lặp bất thường fail rõ.
        """
        if resource not in {"measurements", "hours"}:
            raise ValueError("resource phải là measurements/hours")
        if start >= end:
            raise ValueError("Cần start < end")
        job_id = stable_hash([run_name, sensor.sensor_id, resource, iso_utc(start), iso_utc(end),
                              self.settings.topic, self.publisher.destination])
        lock = self.settings.state_dir / f"{job_id}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        # Khóa OS tự nhả khi process chết, không để stale PID file chặn resume.
        with FileLock(lock, timeout=1):
            page, total, done = self.state.progress(job_id)
            published = 0
            metadata = self.location_metadata(sensor) if not done else {}
            previous_hash: str | None = None
            while not done:
                archive = self.settings.data_dir / "raw" / job_id / f"page-{page:06d}.json"
                if archive.exists():
                    envelope = json.loads(archive.read_text(encoding="utf-8"))
                else:
                    response = self.client.get(f"sensors/{sensor.sensor_id}/{resource}", {
                        "datetime_from": iso_utc(start), "datetime_to": iso_utc(end),
                        "limit": self.settings.page_size, "page": page,
                    })
                    observed_at = datetime.now(timezone.utc)
                    events = [make_event(sensor, resource, row, metadata, job_id, page, index,
                                         observed_at, self.settings.ingest_mode, start, end)
                              for index, row in enumerate(response["results"])]
                    envelope = {"meta": response.get("meta", {}), "events": events}
                    atomic_json(archive, envelope)
                events = envelope["events"]
                page_hash = stable_hash([event["raw_payload"] for event in events])
                if events and page_hash == previous_hash:
                    raise RuntimeError(f"OpenAQ lặp trang {page}; không tăng checkpoint để tránh vòng lặp")
                previous_hash = page_hash
                acknowledged = self.publisher.publish(events) if events else 0
                if acknowledged != len(events):
                    raise RuntimeError("Publisher trả ACK thiếu, giữ nguyên checkpoint")
                published += acknowledged
                total += acknowledged
                done = len(events) < self.settings.page_size
                # Tại đây raw đã có và toàn trang đã ACK. Crash trước commit
                # này chỉ gây retry có ID giống nhau, không làm mất trang.
                self.state.acknowledge(job_id, page + 1, total, done)
                page += 1
            return {"job_id": job_id, "sensor_id": sensor.sensor_id, "resource": resource,
                    "from": iso_utc(start), "to": iso_utc(end), "rows_acknowledged": total,
                    "published_this_call": published, "done": done}


def replay_archives(raw_dir: Path, publisher: Publisher) -> int:
    """Phát lại archive với ingest_mode=replay; publisher phải dùng topic riêng.

    Không sửa source archive hay ingested_at lịch sử. Replay có timestamp hiện
    tại và ID riêng; không gọi API và không được hiểu là sensor đang đo mới.
    """
    if not raw_dir.is_dir():
        raise ValueError("Thư mục raw archive không tồn tại")
    count = 0
    for path in sorted(raw_dir.glob("*/page-*.json")):
        source = json.loads(path.read_text(encoding="utf-8"))["events"]
        events = []
        for original in source:
            event = dict(original)
            event["ingest_mode"] = "replay"
            event["original_ingested_at"] = original["ingested_at"]
            event["ingested_at"] = iso_utc(datetime.now(timezone.utc))
            event["event_id"] = stable_hash(["replay", original["event_id"]])
            events.append(event)
        count += publisher.publish(events) if events else 0
    return count
