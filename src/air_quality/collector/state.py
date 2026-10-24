"""SQLite lưu checkpoint và ngân sách request bền vững, không lưu API key.

Lab: checkpoint chỉ tiến sau Kafka delivery ACK. Nếu tiến trình chết giữa ACK
và commit SQLite, trang được gửi lại; event_id ổn định giúp downstream dedup.
"""

import sqlite3
import time
from pathlib import Path
from typing import Callable


class StateStore:
    """Đọc/ghi tiến độ và lịch request; một file DB cho cả live và backfill."""

    def __init__(self, path: Path) -> None:
        """Tạo DB nếu chưa có; WAL cho phép đọc trạng thái khi Collector chạy."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS progress (
                job_id TEXT PRIMARY KEY, next_page INTEGER NOT NULL DEFAULT 1,
                rows_acknowledged INTEGER NOT NULL DEFAULT 0, done INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS requests (at REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS requests_at ON requests(at);
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.connection.commit()

    def progress(self, job_id: str) -> tuple[int, int, bool]:
        """Trả (trang tiếp, số dòng ACK, hoàn tất); job mới bắt đầu trang 1."""
        row = self.connection.execute(
            "SELECT next_page, rows_acknowledged, done FROM progress WHERE job_id=?", (job_id,)
        ).fetchone()
        return (row[0], row[1], bool(row[2])) if row else (1, 0, False)

    def acknowledge(self, job_id: str, next_page: int, rows: int, done: bool) -> None:
        """Lưu tổng lũy kế sau khi publisher xác nhận toàn trang, không trước đó."""
        with self.connection:
            self.connection.execute(
                "INSERT INTO progress VALUES (?, ?, ?, ?) ON CONFLICT(job_id) DO UPDATE SET "
                "next_page=excluded.next_page, rows_acknowledged=excluded.rows_acknowledged, done=excluded.done",
                (job_id, next_page, rows, int(done)),
            )

    def get(self, key: str) -> str | None:
        """Đọc mốc backfill/reconciliation cố định, không dịch cửa sổ khi resume."""
        row = self.connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, value: str) -> None:
        """Lưu metadata job nhỏ dạng string; không dùng để chứa secret."""
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", (key, value))

    def reserve_request(self, minimum_interval: float, hourly_limit: int,
                        clock: Callable[[], float] = time.time,
                        sleep: Callable[[float], None] = time.sleep) -> None:
        """Chờ ngân sách sliding-hour và spacing dùng chung giữa các tiến trình.

        BEGIN IMMEDIATE bảo vệ bước kiểm tra + đặt chỗ. Không giữ DB lock lúc
        ngủ; process khác vẫn đọc tiến độ được. Ngân sách bảo thủ 1.800/h,
        khoảng 2,1s mặc định để thấp hơn cả 60/phút và 2.000/giờ của OpenAQ.
        """
        while True:
            now = clock()
            try:
                self.connection.execute("BEGIN IMMEDIATE")
                self.connection.execute("DELETE FROM requests WHERE at <= ?", (now - 3600,))
                count, oldest, latest = self.connection.execute(
                    "SELECT COUNT(*), MIN(at), MAX(at) FROM requests"
                ).fetchone()
                wait = max(0.0, (latest + minimum_interval - now) if latest is not None else 0.0)
                if count >= hourly_limit:
                    wait = max(wait, oldest + 3600 - now + 0.01)
                if wait == 0:
                    self.connection.execute("INSERT INTO requests VALUES (?)", (now,))
                self.connection.commit()
            except sqlite3.Error:
                self.connection.rollback()
                raise
            if wait == 0:
                return
            sleep(wait)

    def close(self) -> None:
        """Đóng DB khi job kết thúc; checkpoint đã commit không bị mất."""
        self.connection.close()
