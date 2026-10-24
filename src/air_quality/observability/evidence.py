"""Metadata bằng chứng nhỏ, không đọc key hoặc cấu hình môi trường bí mật."""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from air_quality.contracts.events import iso_utc


def evidence_context(source: Path | None = None) -> dict[str, Any]:
    """Gắn thời gian/code base/dirty state; container không có Git ghi rõ unknown.

    Không khẳng định commit mô tả toàn bộ code nếu working tree dirty. Container
    sau này có thể truyền AIR_QUALITY_CODE_REVISION khi build mà không copy .git.
    """
    revision = os.getenv("AIR_QUALITY_CODE_REVISION")
    dirty: bool | None = {"true": True, "false": False}.get(os.getenv("AIR_QUALITY_CODE_DIRTY", ""))
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True,
                                           stderr=subprocess.DEVNULL, timeout=5).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True,
                                              stderr=subprocess.DEVNULL, timeout=5).strip())
    except (OSError, subprocess.SubprocessError):
        # Không có Git trong runtime là trường hợp hợp lệ, không giả clean.
        # Lỗi Git không được dùng để bỏ qua lỗi pipeline; đây chỉ là provenance.
        # Giữ dirty flag nếu job launcher đã truyền tường minh từ Git host.
        # Không có bằng chứng từ launcher thì vẫn None, không giả clean.
        pass
    result: dict[str, Any] = {"generated_at": iso_utc(datetime.now(timezone.utc)),
                              "code_revision": revision, "working_tree_dirty": dirty}
    if source is not None:
        result.update({"source_path": str(source), "source_file_bytes": source.stat().st_size})
    return result
