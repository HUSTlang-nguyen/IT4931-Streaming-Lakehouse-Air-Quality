"""Kiểm chứng live hợp đồng /hours; không khẳng định tính chính xác cảm biến.

Chỉ chạy với --run-live. Giữ raw interval bất thường là phát hiện riêng;
target ML được định nghĩa là chuỗi giờ do OpenAQ tính, không tự bình quân raw.
"""

from datetime import datetime, timedelta, timezone
from math import floor, log10

import pytest

from air_quality.collector.openaq import OpenAQClient
from air_quality.collector.state import StateStore
from air_quality.collector.service import atomic_json
from air_quality.config.settings import SENSORS, Settings
from air_quality.contracts.events import iso_utc, utc_datetime


@pytest.mark.live
@pytest.mark.parametrize("sensor", SENSORS, ids=lambda s: str(s.sensor_id))
def test_provider_hourly_series_contract(sensor):
    """Xác minh ID/parameter, một hàng mỗi giờ và value khớp summary.avg nguồn."""
    settings = Settings.from_env()
    state = StateStore(settings.state_dir / "collector.sqlite")
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        reserve = lambda: state.reserve_request(settings.request_interval, settings.hourly_request_limit)
        with OpenAQClient(settings, reserve) as client:
            metadata = client.get(f"sensors/{sensor.sensor_id}")["results"][0]
            assert metadata["id"] == sensor.sensor_id
            assert metadata["parameter"]["name"] == sensor.parameter
            rows = client.get(f"sensors/{sensor.sensor_id}/hours", {
                "datetime_from": iso_utc(end - timedelta(days=1)), "datetime_to": iso_utc(end), "limit": 1000,
            })["results"]
            atomic_json(settings.data_dir / "discovery" / f"hourly-contract-{sensor.sensor_id}.json", {
                "queried_at": iso_utc(datetime.now(timezone.utc)), "rows": rows,
            })
            assert rows, "Không có chuỗi giờ trong ngày kiểm tra; chưa đủ bằng chứng ML"
            targets = []
            for row in rows:
                start = utc_datetime(row["period"]["datetimeFrom"]["utc"])
                finish = utc_datetime(row["period"]["datetimeTo"]["utc"])
                assert finish - start == timedelta(hours=1)
                assert finish.minute == finish.second == 0
                assert row["parameter"]["name"] == sensor.parameter
                if row.get("summary") and row["summary"].get("avg") is not None:
                    # API đang hiển thị value theo 3 chữ số có nghĩa, không
                    # phải cố định hai số thập phân: 26.98 → 27, 7.788 → 7.79.
                    # Đây là hợp đồng quan sát được, cần phát hiện nếu nguồn đổi.
                    mean = row["summary"]["avg"]
                    # Nửa đơn vị chữ số cuối cho phép cả hai quy tắc làm tròn
                    # ở điểm giữa (82.05 → 82.0/82.1), không nới sai số cố định.
                    step = 10 ** (floor(log10(abs(mean))) - 2) if mean else 0
                    assert row["value"] == pytest.approx(mean, abs=step / 2 + 1e-9, rel=0)
                targets.append(finish)
            assert len(targets) == len(set(targets))
    finally:
        state.close()
