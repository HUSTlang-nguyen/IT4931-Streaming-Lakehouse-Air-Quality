"""Khởi tạo Superset có thể chạy lại; không bỏ qua lỗi migrate/init.

Tạo admin bằng API nội bộ để password không xuất hiện ở argv/process list.
Chỉ bind localhost qua Compose; đây là cấu hình demo local, không public host.
"""

import os
import subprocess


def boot() -> None:
    """Migrate → ensure admin → permissions init → exec web server một worker."""
    subprocess.run(["superset", "db", "upgrade"], check=True)
    from superset.app import create_app

    app = create_app()
    with app.app_context():
        manager = app.appbuilder.sm
        username = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
        if manager.find_user(username=username) is None:
            user = manager.add_user(username, "Air", "Quality", "admin@localhost.invalid",
                                    manager.find_role("Admin"), os.environ["SUPERSET_ADMIN_PASSWORD"])
            if not user:
                raise RuntimeError("Không tạo được admin Superset")
    subprocess.run(["superset", "init"], check=True)
    os.execvp("gunicorn", ["gunicorn", "--bind", "0.0.0.0:8088", "--workers", "1", "--threads", "4",
                           "--timeout", "120", "superset.app:create_app()"])


if __name__ == "__main__":
    boot()
