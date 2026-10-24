"""Kiểm repo trước commit: syntax/TOML, links và secret thực tế không lọt Git.

Không gọi API/Docker, không in secret hoặc đọc credential ngoài .env dự án.
Đây là kiểm cấu trúc bàn giao, không thay unit/integration/E2E tests.
"""

import ast
import hashlib
import re
import subprocess
import tomllib
from pathlib import Path

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]


def verify() -> dict:
    """Kiểm mọi file tracked/untracked không ignored, lỗi chỉ ghi tên đường dẫn."""
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    values = dotenv_values(ROOT / ".env")
    secrets = [value.encode() for key, value in values.items() if value and any(word in key for word in ("KEY", "PASSWORD", "SECRET"))]
    leaks, links = [], []
    checked = 0
    fingerprint = hashlib.sha256()
    for name in filter(None, files):
        path = ROOT / name
        if not path.is_file():
            continue
        checked += 1
        if any(secret in path.read_bytes() for secret in secrets):
            leaks.append(name)
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=name)
            if name.startswith("src/"):
                # Chuẩn hóa CRLF để cùng code Windows/container có cùng hash.
                fingerprint.update(name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
        if path.suffix == ".md":
            source = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
            for target in re.findall(r"\]\(([^)]+)\)", source):
                target = target.strip("<>").split("#")[0]
                if target and ":" not in target and not (path.parent / target).exists():
                    links.append((name, target))
    with (ROOT / "pyproject.toml").open("rb") as stream:
        tomllib.load(stream)
    if leaks or links:
        raise ValueError({"secret_match_files": leaks, "broken_links": links})
    result = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise ValueError(result.stdout.decode("utf-8", "replace"))
    return {"candidate_files_checked": checked, "secret_match_files": [], "broken_links": [],
            "python_syntax": "pass", "pyproject_toml": "pass", "diff_check": "pass",
            "application_source_sha256": fingerprint.hexdigest()}


if __name__ == "__main__":
    print(verify())
