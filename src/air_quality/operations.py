"""Lệnh vận hành Docker project riêng và truy vấn Trino qua HTTP.

Không ghép shell command bằng string, không in compose config chứa credentials,
không down -v/prune và không tác động service ngoài project.
"""

import os
import secrets
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values, set_key


ROOT = Path(__file__).resolve().parents[2]
SERVICES = ("kafka", "minio", "catalog", "postgres", "trino", "superset", "collector", "processor")


def prepare_credentials(env_file: Path) -> None:
    """Chỉ bổ sung credential trống; giữ key/cấu hình người dùng và không print.

    Password ngẫu nhiên URL-safe để URI PostgreSQL không cần escape ký tự đặc
    biệt. Không ghi đè secret đang dùng vì sẽ làm mất quyền truy cập volume cũ.
    """
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.touch(exist_ok=True)
    existing = dotenv_values(env_file)
    defaults = {"MINIO_ROOT_USER": "airquality", "SUPERSET_ADMIN_USERNAME": "admin"}
    for key in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD", "SUPERSET_SECRET_KEY",
                "SUPERSET_ADMIN_USERNAME", "SUPERSET_ADMIN_PASSWORD"):
        if not existing.get(key) and not os.getenv(key):
            set_key(str(env_file), key, defaults.get(key, secrets.token_urlsafe(32)))
    if os.name != "nt":
        env_file.chmod(0o600)


def compose_args(env_file: Path, *arguments: str) -> list[str]:
    """Tạo argv không shell; absolute paths giữ đúng root dù đường dẫn có space."""
    return ["docker", "compose", "--project-name", "air-quality-lakehouse",
            "--env-file", str(env_file.resolve()), "-f", str(ROOT / "infra/compose.yaml"), *arguments]


def compose(env_file: Path, *arguments: str, environment: dict[str, str] | None = None) -> None:
    """Chạy lệnh project, truyền lỗi ra CLI; không nuốt exit code Docker."""
    result = subprocess.run(compose_args(env_file, *arguments), cwd=ROOT, env=environment)
    if result.returncode:
        raise RuntimeError(f"Docker Compose thất bại, exit={result.returncode}")


def start(env_file: Path, services: list[str] | None = None, build: bool = True) -> None:
    """Chuẩn bị secrets và khởi động core services; chưa tự xóa volume khi lỗi."""
    prepare_credentials(env_file)
    selected = services or list(SERVICES)
    if any(service not in SERVICES for service in selected):
        raise ValueError("Service không thuộc core stack dự án")
    if "collector" in selected and not (os.getenv("OPENAQ_API_KEY") or dotenv_values(env_file).get("OPENAQ_API_KEY")):
        raise ValueError("Thiếu OPENAQ_API_KEY cho Collector; có thể start các core services riêng khi chưa có key")
    from air_quality.observability.evidence import evidence_context
    context = evidence_context()
    environment = {**os.environ, "AIR_QUALITY_CODE_REVISION": context["code_revision"] or "unknown",
                   "AIR_QUALITY_CODE_DIRTY": str(context["working_tree_dirty"]).lower()}
    compose(env_file, "--profile", "pipeline", "up", "-d", "--wait", "--wait-timeout", "240",
            *(["--build"] if build else []), *selected, environment=environment)
    if "catalog" in selected:
        wait_for_http("http://localhost:18181/v1/config")


def stop(env_file: Path) -> None:
    """Dừng project nhưng giữ containers/volumes để kiểm tra resume và demo."""
    compose(env_file, "--profile", "pipeline", "stop")


def status(env_file: Path) -> None:
    """In trạng thái project, không print env hoặc inspect credential."""
    compose(env_file, "--profile", "pipeline", "ps", "--all")


def run_tests(env_file: Path, integration: bool = False, live: bool = False) -> None:
    """Chạy unit mặc định offline; integration vào Spark container, live phải opt in.

    Basetemp riêng mỗi lần để pytest không dọn nhầm dataset/checkpoint. Không
    cài Spark lên host và không coi module skip do thiếu pyspark là pass E2E.
    """
    import sys
    from uuid import uuid4

    run = uuid4().hex[:12]
    arguments = [sys.executable, "-m", "pytest", "tests/unit", "-q", "--tb=short",
                 f"--basetemp=artifacts/local/pytest-unit-{run}", "--junitxml=artifacts/local/tests-unit.xml"]
    if live:
        arguments += ["tests/integration/test_openaq_live.py", "--run-live"]
    result = subprocess.run(arguments, cwd=ROOT)
    if result.returncode:
        raise RuntimeError(f"Unit/live tests thất bại, exit={result.returncode}")
    if integration:
        compose(env_file, "run", "--rm", "--no-deps", "spark", "python", "-m", "pytest", "tests/integration",
                "--run-integration", "-q", "--tb=short", f"--basetemp=artifacts/local/pytest-spark-{run}",
                "--junitxml=artifacts/local/tests-spark.xml")


def run_spark_job(env_file: Path, action: str, arguments: list[str]) -> None:
    """Chạy một job Spark thật trong container runtime, mount code/data/checkpoint."""
    from air_quality.observability.evidence import evidence_context

    context = evidence_context()
    compose(env_file, "run", "--rm", "--no-deps", "-e", f"AIR_QUALITY_CODE_REVISION={context['code_revision'] or 'unknown'}",
            "-e", f"AIR_QUALITY_CODE_DIRTY={str(context['working_tree_dirty']).lower()}", "spark", "python", "-m",
            "air_quality.processing.jobs", action, *arguments)


def wait_for_http(endpoint: str, timeout: float = 90) -> None:
    """Bounded readiness cho dịch vụ không có curl trong image, không restart mù."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = httpx.get(endpoint, timeout=3)
            if response.status_code == 200:
                return
        except httpx.TransportError:
            # Connection refused là trạng thái boot tạm thời, không phải pass.
            pass
        time.sleep(2)
    raise RuntimeError(f"Service chưa sẵn sàng sau {timeout}s: {endpoint}")


def query_trino(sql: str, endpoint: str = "http://localhost:18080") -> dict:
    """Đọc toàn bộ pages của Trino REST protocol; chỉ trả rows khi query không lỗi.

    nextUri chứa host nội bộ trong vài deployment, vì vậy giữ path/query nhưng
    dùng lại endpoint đã cấu hình. Không gửi credential/provider API key.
    """
    headers = {"X-Trino-User": "airquality", "X-Trino-Catalog": "iceberg", "X-Trino-Schema": "live"}
    data: list = []
    columns: list = []
    with httpx.Client(timeout=120) as client:
        response = client.post(endpoint + "/v1/statement", content=sql.encode(), headers=headers)
        response.raise_for_status()
        for _ in range(10000):
            body = response.json()
            if "error" in body:
                raise RuntimeError("Trino query failed: " + body["error"].get("message", "unknown"))
            columns = body.get("columns", columns)
            data.extend(body.get("data", []))
            if not body.get("nextUri"):
                return {"columns": columns, "data": data, "stats": body.get("stats", {}), "id": body.get("id")}
            next_uri = urlsplit(body["nextUri"])
            response = client.get(endpoint + next_uri.path + ("?" + next_uri.query if next_uri.query else ""), headers=headers)
            response.raise_for_status()
    raise RuntimeError("Trino vượt giới hạn pages; chưa coi query hoàn thành")
