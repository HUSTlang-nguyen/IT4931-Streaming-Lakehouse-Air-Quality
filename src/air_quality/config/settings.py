"""Nạp cấu hình Collector; tách secret khỏi biểu diễn/log cấu hình.

Lab: môi trường thực ưu tiên hơn .env. Không đọc key từ code hoặc tự tìm
credential ở thư mục người dùng. Việc thiếu key chỉ chặn lệnh cần OpenAQ.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Sensor:
    """Một kênh đo đã chọn; station_id liên kết metadata và measurements."""

    location_id: int
    sensor_id: int
    parameter: str
    station_name: str


SENSORS = (
    Sensor(4946813, 13502154, "pm25", "ĐHBK"),
    Sensor(4946813, 13502152, "pm10", "ĐHBK"),
    Sensor(4946812, 13502151, "pm25", "Công viên Nhân Chính"),
    Sensor(4946812, 13502153, "pm10", "Công viên Nhân Chính"),
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Cấu hình đã kiểm tra; api_key không xuất hiện trong repr dataclass.

    Paths đều thuộc workspace hiện tại mặc định. Chưa gắn endpoint Docker
    vào code để cùng Collector có thể chạy trên host và bên trong container.
    """

    api_key: str = field(default="", repr=False)
    base_url: str = "https://api.openaq.org/v3"
    bootstrap_servers: str = "localhost:19092"
    topic: str = "air-quality.live"
    ingest_mode: str = "live"
    state_dir: Path = Path("checkpoints")
    data_dir: Path = Path("data")
    display_timezone: str = "Asia/Ho_Chi_Minh"
    backfill_days: int = 180
    poll_seconds: int = 300
    overlap_hours: int = 24
    reconcile_days: int = 7
    reconcile_hours: int = 24
    request_interval: float = 2.1
    hourly_request_limit: int = 1800
    page_size: int = 1000
    timeout_seconds: float = 30.0
    max_attempts: int = 5

    def __post_init__(self) -> None:
        """Từ chối cấu hình nguy hiểm/sai trước khi gọi mạng hoặc ghi dữ liệu."""
        ZoneInfo(self.display_timezone)
        if self.base_url != "https://api.openaq.org/v3":
            raise ValueError("Chỉ gửi API key tới endpoint HTTPS chính thức OpenAQ v3")
        if self.ingest_mode not in {"live", "backfill", "replay"}:
            raise ValueError("ingest_mode phải là live/backfill/replay")
        if self.topic.startswith("air-quality.replay") and self.ingest_mode != "replay":
            raise ValueError("Topic replay chỉ dành cho ingest_mode=replay")
        if self.ingest_mode == "replay" and not self.topic.startswith("air-quality.replay"):
            raise ValueError("Replay bắt buộc dùng topic air-quality.replay riêng")
        positive = (self.backfill_days, self.poll_seconds, self.overlap_hours,
                    self.reconcile_days, self.reconcile_hours, self.max_attempts,
                    self.hourly_request_limit, self.timeout_seconds)
        if any(value <= 0 for value in positive) or self.request_interval < 0:
            raise ValueError("Khoảng thời gian/hạn mức phải dương; request_interval >= 0")
        if not 1 <= self.page_size <= 1000:
            raise ValueError("page_size phải nằm trong 1..1000")

    @classmethod
    def from_env(cls, env_file: Path = Path(".env")) -> "Settings":
        """Đọc file được chỉ định, không ghi đè env có sẵn; lỗi số được báo rõ."""
        load_dotenv(env_file, override=False)
        return cls(
            api_key=os.getenv("OPENAQ_API_KEY", ""),
            base_url=os.getenv("OPENAQ_BASE_URL", "https://api.openaq.org/v3"),
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
            topic=os.getenv("AIR_QUALITY_TOPIC", "air-quality.live"),
            ingest_mode=os.getenv("AIR_QUALITY_INGEST_MODE", "live"),
            state_dir=Path(os.getenv("AIR_QUALITY_STATE_DIR", "checkpoints")),
            data_dir=Path(os.getenv("AIR_QUALITY_DATA_DIR", "data")),
            display_timezone=os.getenv("AIR_QUALITY_DISPLAY_TIMEZONE", "Asia/Ho_Chi_Minh"),
            backfill_days=int(os.getenv("AIR_QUALITY_BACKFILL_DAYS", "180")),
            poll_seconds=int(os.getenv("AIR_QUALITY_POLL_INTERVAL_SECONDS", "300")),
            overlap_hours=int(os.getenv("AIR_QUALITY_OVERLAP_HOURS", "24")),
            reconcile_days=int(os.getenv("AIR_QUALITY_RECONCILE_DAYS", "7")),
            reconcile_hours=int(os.getenv("AIR_QUALITY_RECONCILE_INTERVAL_HOURS", "24")),
            request_interval=float(os.getenv("OPENAQ_REQUEST_INTERVAL_SECONDS", "2.1")),
            hourly_request_limit=int(os.getenv("OPENAQ_HOURLY_REQUEST_LIMIT", "1800")),
            page_size=int(os.getenv("OPENAQ_PAGE_SIZE", "1000")),
        )

    def require_api_key(self) -> None:
        """Chỉ gọi từ thao tác API; thiếu key không chặn help/test/replay."""
        if not self.api_key.strip():
            raise ValueError("Thiếu OPENAQ_API_KEY; cung cấp trong env hoặc .env bị gitignore")
