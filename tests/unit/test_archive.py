"""Drain phải giữ provenance, không gửi lại phần đã ACK khi resume và không trộn replay."""

import json

import pytest

from air_quality.collector.archive import drain_jsonl
from air_quality.collector.state import StateStore


class Publisher:
    destination = "fake:kafka:source"

    def __init__(self, fail_call=None):
        self.calls = 0
        self.events = []
        self.fail_call = fail_call

    def publish(self, events):
        self.calls += 1
        if self.calls == self.fail_call:
            raise RuntimeError("synthetic ACK failure")
        self.events.extend(events)
        return len(events)


def test_drain_crash_resume_and_completed_rerun(tmp_path):
    rows = [{"event_id": str(i), "ingest_mode": "backfill", "ingested_at": "original"} for i in range(5)]
    source = tmp_path / "source.jsonl"
    source.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    state = StateStore(tmp_path / "state.sqlite")
    publisher = Publisher(fail_call=2)
    try:
        with pytest.raises(RuntimeError, match="ACK"):
            drain_jsonl(source, publisher, state, tmp_path, batch_size=2)
        publisher.fail_call = None
        result = drain_jsonl(source, publisher, state, tmp_path, batch_size=2)
        assert result["published_this_call"] == 3
        assert publisher.events == rows
        assert drain_jsonl(source, publisher, state, tmp_path, batch_size=2)["published_this_call"] == 0
    finally:
        state.close()


def test_drain_rejects_replay(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text(json.dumps({"event_id": "1", "ingest_mode": "replay"}) + "\n")
    state = StateStore(tmp_path / "state.sqlite")
    try:
        with pytest.raises(ValueError, match="replay"):
            drain_jsonl(source, Publisher(), state, tmp_path)
    finally:
        state.close()
