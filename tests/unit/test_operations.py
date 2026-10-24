"""Chứng minh khởi động không đổi credential đang bảo vệ volume đã có."""

from dotenv import dotenv_values

from air_quality.operations import compose_args, prepare_credentials


def test_prepare_keeps_existing_password_and_api_key(tmp_path, monkeypatch):
    for name in ["MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD", "SUPERSET_SECRET_KEY",
                 "SUPERSET_ADMIN_USERNAME", "SUPERSET_ADMIN_PASSWORD"]:
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / ".env"
    path.write_text("OPENAQ_API_KEY=synthetic-key\nMINIO_ROOT_PASSWORD=keep-this-existing-password\n")
    prepare_credentials(path)
    first = path.read_bytes()
    values = dotenv_values(path)
    assert values["OPENAQ_API_KEY"] == "synthetic-key"
    assert values["MINIO_ROOT_PASSWORD"] == "keep-this-existing-password"
    assert len(values["POSTGRES_PASSWORD"]) >= 32
    prepare_credentials(path)
    assert path.read_bytes() == first


def test_compose_argv_keeps_space_paths_and_project_scope(tmp_path):
    path = tmp_path / "with spaces" / ".env"
    args = compose_args(path, "--profile", "pipeline", "stop")
    assert args[args.index("--env-file") + 1] == str(path.resolve())
    assert args[args.index("--project-name") + 1] == "air-quality-lakehouse"
    assert args[-1] == "stop" and "-v" not in args and "prune" not in args


def test_first_test_run_creates_artifact_parent_before_pytest(tmp_path, monkeypatch):
    """Clone mới chưa có cache/log; pytest phải nhận basetemp có parent tồn tại."""
    from types import SimpleNamespace
    from air_quality import operations

    assert not (tmp_path / "artifacts/local").exists()
    monkeypatch.setattr(operations, "ROOT", tmp_path)
    invocations = []

    def invoke(argv, cwd):
        assert cwd == tmp_path and (cwd / "artifacts/local").is_dir()
        assert any(arg.startswith("--basetemp=artifacts/local/") for arg in argv)
        invocations.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(operations.subprocess, "run", invoke)
    operations.run_tests(tmp_path / ".env")
    assert len(invocations) == 1
