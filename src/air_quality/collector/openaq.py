"""OpenAQ HTTP adapter, có bounded retry và lịch request được tiêm vào để test.

Adapter chỉ trả payload. Pagination/checkpoint thuộc service để HTTP có thể
mock mà không cần Kafka hay Spark. Không in header hoặc repr chứa API key.
"""

import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable

import httpx

from air_quality.config.settings import Settings


class OpenAQError(RuntimeError):
    """Lỗi API đã làm sạch; caller có thể báo path/status nhưng không key."""


def retry_delay(value: str | None, attempt: int, now: datetime | None = None) -> float:
    """Hiểu cả Retry-After số giây và HTTP-date; invalid dùng exponential backoff."""
    fallback = min(2 ** attempt, 60)
    if value is None:
        return float(fallback)
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            timestamp = parsedate_to_datetime(value)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return max(0.0, (timestamp - (now or datetime.now(timezone.utc))).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return float(fallback)


class OpenAQClient:
    """HTTP client context-managed; dùng transport giả khi kiểm thử offline."""

    def __init__(self, settings: Settings, reserve: Callable[[], None],
                 transport: httpx.BaseTransport | None = None,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        """Không gọi mạng khi khởi tạo; giữ secret trong header, không query string."""
        settings.require_api_key()
        self.settings, self.reserve, self.sleep = settings, reserve, sleep
        self.http = httpx.Client(
            base_url=settings.base_url + "/", timeout=settings.timeout_seconds,
            headers={"X-API-Key": settings.api_key, "User-Agent": "IT4931-Air-Quality/0.1"},
            transport=transport, follow_redirects=False,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET retry 429/408/5xx/transport; 401/403/422 fail ngay, không retry vô hạn.

        Không theo redirect: header secret chỉ gửi endpoint chính thức đã kiểm
        tra. Mỗi attempt kể cả retry phải xin ngân sách request trước khi gọi.
        """
        if path.startswith(("/", "http:" , "https:")) or ".." in path:
            raise ValueError("Chỉ nhận resource path tương đối của OpenAQ")
        for attempt in range(self.settings.max_attempts):
            self.reserve()
            try:
                response = self.http.get(path, params=params)
            except httpx.TransportError:
                if attempt + 1 == self.settings.max_attempts:
                    raise OpenAQError(f"OpenAQ transport thất bại sau {attempt + 1} lần: {path}") from None
                self.sleep(retry_delay(None, attempt))
                continue
            if response.status_code == 200:
                try:
                    body = response.json()
                except ValueError:
                    raise OpenAQError(f"OpenAQ trả JSON không hợp lệ: {path}") from None
                if not isinstance(body, dict) or not isinstance(body.get("results"), list):
                    raise OpenAQError(f"OpenAQ schema response không hợp lệ: {path}")
                return body
            transient = response.status_code in {408, 429} or response.status_code >= 500
            if not transient or attempt + 1 == self.settings.max_attempts:
                raise OpenAQError(f"OpenAQ HTTP {response.status_code}: {path}")
            self.sleep(retry_delay(response.headers.get("Retry-After"), attempt))
        raise AssertionError("max_attempts được Settings đảm bảo > 0")

    def close(self) -> None:
        """Giải phóng socket HTTP; checkpoint thuộc StateStore độc lập."""
        self.http.close()

    def __enter__(self) -> "OpenAQClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
