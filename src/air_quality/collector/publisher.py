"""Publisher có ACK toàn trang; Kafka và JSONL dùng cùng envelope production.

JSONL phục vụ kiểm tra nguồn khi Kafka chưa sẵn sàng, không chứng minh E2E.
Raw archive của service là nguồn replay; không log nội dung chứa metadata lớn.
"""

import json
import os
from pathlib import Path
from typing import Any, Protocol


class Publisher(Protocol):
    """Ranh giới I/O: chỉ return khi tất cả event đã được nhận bền vững."""

    destination: str

    def publish(self, events: list[dict[str, Any]]) -> int:
        """Trả số event ACK hoặc raise; caller không checkpoint khi có lỗi."""
        ...


class JsonlPublisher:
    """Sink file cục bộ cho khám phá/test, không thay thế Kafka khi nghiệm thu."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.destination = "jsonl:" + str(path.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)

    def publish(self, events: list[dict[str, Any]]) -> int:
        """Append và fsync trước ACK; downstream vẫn cần dedup nếu replay trang."""
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return len(events)


class KafkaPublisher:
    """Kafka producer idempotent; failure/timeout phải chặn tiến độ Collector."""

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        from confluent_kafka import Producer

        self.topic = topic
        self.destination = f"kafka:{bootstrap_servers}:{topic}"
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "compression.type": "zstd",
            "delivery.timeout.ms": 30000,
            "client.id": "air-quality-collector",
        })

    def publish(self, events: list[dict[str, Any]]) -> int:
        """Đợi broker ACK từng trang; Kafka offset không phải business key Silver.

        Một số message có thể ACK trước khi message khác lỗi. Khi retry, ID
        envelope ổn định + Bronze MERGE/Silver MERGE xử lý trường hợp đó.
        """
        errors: list[str] = []

        def delivered(error: object, message: object) -> None:
            if error is not None:
                errors.append(str(error))

        for event in events:
            payload = json.dumps(event, ensure_ascii=False, allow_nan=False).encode("utf-8")
            try:
                self.producer.produce(self.topic, key=str(event["sensor_id"]), value=payload, on_delivery=delivered)
            except BufferError:
                self.producer.poll(1)
                self.producer.produce(self.topic, key=str(event["sensor_id"]), value=payload, on_delivery=delivered)
            self.producer.poll(0)
        outstanding = self.producer.flush(35)
        if outstanding or errors:
            raise RuntimeError(f"Kafka chưa ACK toàn trang: pending={outstanding}, delivery_errors={len(errors)}")
        return len(events)
