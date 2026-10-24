"""Đưa bản thu thật đã lưu sang Kafka, giữ mode gốc; khác replay demo.

Không gọi lại API và không giả dữ liệu lịch sử là sensor live. Checkpoint
chỉ tiến sau publisher ACK, event_id giữ nguyên để retry downstream idempotent.
"""

from pathlib import Path

from filelock import FileLock

from air_quality.collector.publisher import Publisher
from air_quality.collector.state import StateStore
from air_quality.contracts.events import stable_hash
from air_quality.observability.coverage import jsonl_events


def drain_jsonl(source: Path, publisher: Publisher, state: StateStore, state_dir: Path,
                run_name: str = "source-backfill", batch_size: int = 1000) -> dict:
    """Gửi file bất biến theo lô, resume bằng số event ACK (không theo offset Kafka).

    Signature path/size/mtime_ns xác định file local của run; nếu file đổi trong
    lúc chạy, không đánh dấu done. Dùng run_name mới để chủ động gửi lại cùng
    event_id khi thực nghiệm duplicate; không sửa original ingested_at.
    """
    if batch_size <= 0 or not source.is_file():
        raise ValueError("Cần file nguồn tồn tại và batch_size dương")
    signature = (str(source.resolve()), source.stat().st_size, source.stat().st_mtime_ns)
    job_id = stable_hash(["drain", run_name, signature, publisher.destination])
    state_dir.mkdir(parents=True, exist_ok=True)
    with FileLock(state_dir / f"drain-{job_id}.lock", timeout=1):
        page, acknowledged, done = state.progress(job_id)
        if done:
            return {"job_id": job_id, "rows_acknowledged": acknowledged, "published_this_call": 0, "done": True}
        published = 0
        batch = []
        for index, event in enumerate(jsonl_events(source)):
            if index < acknowledged:
                continue
            if event.get("ingest_mode") not in {"live", "backfill"}:
                raise ValueError("drain chỉ nhận bản thu live/backfill gốc; replay phải dùng lệnh riêng")
            batch.append(event)
            if len(batch) == batch_size:
                if publisher.publish(batch) != len(batch):
                    raise RuntimeError("Drain chưa ACK toàn lô; giữ checkpoint trước lô")
                published += len(batch)
                # Không dùng acknowledged làm skip cursor đang đổi khi enumerate:
                # index là vị trí tuyệt đối, chỉ các lô đã ACK mới tiến state.
                acknowledged = index + 1
                page += 1
                state.acknowledge(job_id, page, acknowledged, False)
                batch = []
        if batch:
            if publisher.publish(batch) != len(batch):
                raise RuntimeError("Drain chưa ACK toàn lô cuối")
            published += len(batch)
            acknowledged += len(batch)
            page += 1
            state.acknowledge(job_id, page, acknowledged, False)
        current = (str(source.resolve()), source.stat().st_size, source.stat().st_mtime_ns)
        if current != signature:
            raise ValueError("File nguồn đã đổi khi drain; chưa coi job hoàn tất")
        state.acknowledge(job_id, page, acknowledged, True)
        return {"job_id": job_id, "rows_acknowledged": acknowledged, "published_this_call": published, "done": True}
