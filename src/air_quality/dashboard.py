"""Provision Superset qua API bằng Python, cấu hình hiển thị lưu trong repository.

Credentials chỉ đọc env local và chỉ gửi Superset localhost. IDs dashboard/chart
được tìm theo tên riêng, nên chạy lại không sinh bản sao. Chart params/source SQL
không chứa secret và có thể xuất/import native dashboard để tái tạo.
"""

import json
import os
import io
import zipfile
import re
from uuid import UUID
from pathlib import Path, PurePosixPath
from typing import Any

import httpx
from dotenv import load_dotenv

from air_quality.operations import ROOT


class SupersetClient:
    """Session HTTP giữ JWT + CSRF cookie, không log request body đăng nhập."""

    def __init__(self, env_file: Path, endpoint: str = "http://localhost:18088") -> None:
        if endpoint != "http://localhost:18088":
            raise ValueError("Provision chỉ gửi admin credential tới Superset local đã chọn")
        load_dotenv(env_file, override=False)
        self.http = httpx.Client(base_url=endpoint, timeout=90)
        password = os.environ.get("SUPERSET_ADMIN_PASSWORD")
        if not password:
            raise ValueError("Thiếu SUPERSET_ADMIN_PASSWORD local; chạy start trước")
        response = self.http.post("/api/v1/security/login", json={
            "username": os.getenv("SUPERSET_ADMIN_USERNAME", "admin"), "password": password,
            "provider": "db", "refresh": True,
        })
        if response.status_code != 200:
            self.http.close()
            raise RuntimeError(f"Superset login HTTP {response.status_code}; kiểm tra credential local")
        self.http.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        csrf = self.http.get("/api/v1/security/csrf_token/")
        csrf.raise_for_status()
        self.http.headers["X-CSRFToken"] = csrf.json()["result"]
        self.http.headers["Referer"] = endpoint + "/"

    def request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Trả JSON hoặc lỗi API đã lược thông tin; không print JWT/secret."""
        response = self.http.request(method, path, **kwargs)
        if response.is_error:
            # Các API ở đây chỉ gửi source/chart config, login được xử lý riêng.
            message = response.json().get("message", "API error") if "json" in response.headers.get("content-type", "") else "API error"
            raise RuntimeError(f"Superset {method} {path}: HTTP {response.status_code}: {message}")
        return response.json()

    def find(self, resource: str, field: str, value: str) -> dict | None:
        """Tìm theo tên ở project dedicated; phân trang có giới hạn rõ ràng."""
        for page in range(100):
            result = self.request("GET", f"/api/v1/{resource}/", params={"q": f"(page:{page},page_size:100)"})
            rows = result["result"]
            for row in rows:
                if row.get(field) == value:
                    return row
            if len(rows) < 100:
                return None
        raise RuntimeError("Superset list vượt giới hạn100pages; chưa kết luận không tồn tại")

    def close(self) -> None:
        self.http.close()


def sql_metric(expression: str, label: str) -> dict:
    """Metric SQL có tên rõ để tooltip/legend dễ hiểu, không đưa internals vào UI."""
    return {"expressionType": "SQL", "sqlExpression": expression, "label": label,
            "hasCustomLabel": True, "optionName": label}


def dashboard_spec() -> dict:
    """Cấu hình source độc lập IDs, format giờ Việt Nam ngay trong SQL.

    local_time là nhãn chuỗi sắp xếp ISO: không phụ thuộc timezone browser hoặc
    cộng UTC+7 lần hai. Value null của grid giữ nguyên để đường biểu đồ có gap.
    """
    hourly_sql = """SELECT *, format_datetime(period_end AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'yyyy-MM-dd HH:mm') AS local_time FROM iceberg.live.hourly"""
    freshness_sql = """SELECT *, format_datetime(last_measurement_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'yyyy-MM-dd HH:mm') AS last_measurement_local, date_diff('minute', last_measurement_at,
        CAST(current_timestamp AT TIME ZONE 'UTC' AS timestamp)) AS age_minutes
        FROM iceberg.live.freshness"""
    # Dùng Gold grid làm phía trái để RF thiếu features vẫn có hàng null,
    # tránh nối đường qua giờ không có backtest prediction.
    forecast_sql = """SELECT h.sensor_id,h.station_name,h.period_end AS target_time,
        format_datetime(h.period_end AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'yyyy-MM-dd HH:mm') AS local_time,u.curve,u.chart_value
        FROM iceberg.live.hourly h LEFT JOIN iceberg.live.forecast_actual f
          ON h.sensor_id=f.sensor_id AND h.period_end=f.target_time AND f.mode='backtest'
          AND f.issued_at=(SELECT max(issued_at) FROM iceberg.live.forecast_actual WHERE mode='backtest')
        CROSS JOIN UNNEST(ARRAY['Thực tế','Random Forest','Persistence'],
          ARRAY[h.value,f.predicted_value,f.baseline_value]) AS u(curve,chart_value)
        WHERE h.parameter_name='pm25'"""
    operational_sql = """SELECT *, format_datetime(target_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'yyyy-MM-dd HH:mm') AS target_local, format_datetime(issued_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'yyyy-MM-dd HH:mm:ss') AS issued_local FROM iceberg.live.forecast_actual WHERE mode='operational'"""
    return {
        "title": "Chất lượng không khí Hà Nội", "slug": "air-quality-hanoi",
        "datasets": {
            "hourly_local": {"table_name": "hourly_local", "schema": "live", "sql": hourly_sql},
            "daily": {"table_name": "daily", "schema": "live"},
            "freshness_status": {"table_name": "freshness_status", "schema": "live", "sql": freshness_sql},
            "forecast_comparison": {"table_name": "forecast_comparison", "schema": "live", "sql": forecast_sql},
            "operational_forecasts": {"table_name": "operational_forecasts", "schema": "live", "sql": operational_sql},
            "model_metrics": {"table_name": "model_metrics", "schema": "live"},
        },
        "charts": [
            {"name": "AQ • PM2.5 theo giờ Việt Nam", "dataset": "hourly_local", "type": "echarts_timeseries_line", "parameter": "pm25"},
            {"name": "AQ • PM10 theo giờ Việt Nam", "dataset": "hourly_local", "type": "echarts_timeseries_line", "parameter": "pm10"},
            {"name": "AQ • Độ phủ giờ theo trạm", "dataset": "hourly_local", "type": "table", "coverage": True},
            {"name": "AQ • Độ mới từng sensor", "dataset": "freshness_status", "type": "table",
             "columns": ["station_name", "parameter_name", "series_kind", "last_measurement_local", "age_minutes", "records"]},
            {"name": "AQ • Tổng hợp ngày Việt Nam", "dataset": "daily", "type": "table",
             "columns": ["local_date", "station_name", "parameter_name", "mean_value", "valid_hours", "expected_hours", "coverage_percent"]},
            {"name": "AQ • Backtest PM2.5 — thực tế và dự báo", "dataset": "forecast_comparison", "type": "echarts_timeseries_line", "forecast": True},
            {"name": "AQ • Đánh giá RF và persistence — tập test", "dataset": "model_metrics", "type": "table",
             "columns": ["station_name", "algorithm", "n", "mae", "rmse", "model_version"]},
            {"name": "AQ • Dự báo đã phát hành", "dataset": "operational_forecasts", "type": "table",
             "columns": ["station_name", "issued_local", "target_local", "predicted_value", "baseline_value", "actual_value", "error", "model_version"]},
        ],
    }


def form_data(chart: dict, dataset_id: int) -> dict:
    """Chuyển spec thành formData Superset chuẩn, nguồn để frontend build query."""
    form: dict = {"datasource": f"{dataset_id}__table", "viz_type": chart["type"], "time_range": "No filter",
                  "row_limit": 10000, "adhoc_filters": [], "annotation_layers": [],
                  "page_length": 20, "table_timestamp_format": "%d/%m/%Y", "number_format": ",.2f",
                  "column_config": {"mean_value": {"d3NumberFormat": ",.2f"}, "coverage_percent": {"d3NumberFormat": ".1f"},
                                    "Giờ có dữ liệu": {"d3NumberFormat": ",.0f"}, "Giờ trong cửa sổ": {"d3NumberFormat": ",.0f"},
                                    "Độ phủ (%)": {"d3NumberFormat": ".1f"},
                                    **{name: {"d3NumberFormat": ",.2f"} for name in
                                       ["mae", "rmse", "predicted_value", "baseline_value", "actual_value", "error"]},
                                    "n": {"d3NumberFormat": ",.0f"}}}
    if chart.get("parameter") or chart.get("forecast"):
        form.update({"x_axis": "local_time", "groupby": ["station_name"],
                     "time_range": 'DATEADD(DATETIME("now"), -7, day) : DATETIME("now")', "granularity_sqla": "period_end",
                     "metrics": [sql_metric("AVG(value)", "µg/m³")], "time_grain_sqla": None,
                     "show_legend": True, "rich_tooltip": True, "legendType": "scroll", "seriesType": "line",
                     "show_markers": False, "connect_nulls": False, "x_axis_sort_asc": True,
                     "x_axis_title": "Giờ Việt Nam (UTC+7)", "y_axis_title": "µg/m³",
                     "adhoc_filters": []})
        if chart.get("parameter"):
            form["adhoc_filters"] = [{"expressionType": "SIMPLE", "subject": "parameter_name", "operator": "==",
                                      "comparator": chart["parameter"], "clause": "WHERE", "filterOptionName": chart["parameter"]}]
        else:
            form.update({"groupby": ["station_name", "curve"], "metrics": [sql_metric("AVG(chart_value)", "µg/m³")],
                         "granularity_sqla": "target_time"})
    elif chart.get("coverage"):
        form.update({"query_mode": "aggregate", "groupby": ["station_name", "parameter_name"],
                     "metrics": [sql_metric("COUNT(value)", "Giờ có dữ liệu"), sql_metric("COUNT(*)", "Giờ trong cửa sổ"),
                                 sql_metric("100.0 * COUNT(value) / COUNT(*)", "Độ phủ (%)")], "all_columns": []})
    else:
        form.update({"query_mode": "raw", "all_columns": chart["columns"], "metrics": [], "groupby": []})
        if chart["dataset"] == "daily":
            form["order_by_cols"] = [json.dumps(["local_date", False])]
        elif chart["dataset"] == "operational_forecasts":
            form["order_by_cols"] = [json.dumps(["target_time", False])]
    return form


def export_native(client: SupersetClient, dashboard_id: int, destination: Path) -> list[str]:
    """Xuất ZIP native và YAML readable, kiểm path/secret trước khi ghi repository.

    ZIP private giữ trong output/playwright (ignored); YAML chứa UUID/config
    Trino không password để import sang stack mới. Không extract tùy tiện path
    từ archive và không đưa JWT/admin/MinIO/API credentials vào export.
    """
    response = client.http.get("/api/v1/dashboard/export/", params={"q": f"!({dashboard_id})"})
    if response.status_code != 200:
        raise RuntimeError(f"Superset native export HTTP {response.status_code}")
    secrets = [os.getenv(key) for key in ("OPENAQ_API_KEY", "MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD", "SUPERSET_SECRET_KEY", "SUPERSET_ADMIN_PASSWORD")]
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    files = []
    pending = []
    for entry in archive.infolist():
        if entry.is_dir():
            continue
        parts = PurePosixPath(entry.filename)
        if parts.is_absolute() or ".." in parts.parts or len(parts.parts) < 2:
            raise ValueError("Unsafe export archive path")
        relative = Path(*parts.parts[1:])
        if relative.suffix not in {".yaml", ".yml"}:
            raise ValueError("Native export chỉ được ghi YAML cấu hình")
        content = archive.read(entry).decode("utf-8")
        if any(secret and secret in content for secret in secrets):
            raise ValueError("Export chứa credential local; chưa ghi file hoặc log nội dung")
        target = destination / relative
        if not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError("Export path vượt thư mục đích")
        pending.append((target, content))
        files.append(str(relative))
    for target, content in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    private_archive = ROOT / "output/playwright/dashboard-native.zip"
    private_archive.parent.mkdir(parents=True, exist_ok=True)
    private_archive.write_bytes(response.content)
    return files


def import_native(env_file: Path, archive: Path) -> dict:
    """Import native export vào Superset local; giữ UUID, không tạo dashboard trùng."""
    client = SupersetClient(env_file)
    try:
        with archive.open("rb") as stream:
            result = client.request("POST", "/api/v1/dashboard/import/", data={"overwrite": "true"},
                                    files={"formData": (archive.name, stream, "application/zip")})
        return {"imported": True, "result": result}
    finally:
        client.close()


def chart_uuids(client: SupersetClient, chart_ids: list[int]) -> dict[int, str]:
    """Lấy UUID từ native export vì REST chart GET4.1.2 không trả field này.

    Native importer cần meta.uuid trong mỗi layout node để ánh xạ chartId. Nếu
    thiếu, import vẫn HTTP200 nhưng tự thêm một node nữa cho mỗi chart. Chỉ đọc
    hai trường format export đã biết (filename ID / UUID top-level), không parse
    YAML tùy ý hay ghi ZIP ra filesystem.
    """
    response = client.http.get("/api/v1/chart/export/", params={"q": "!(" + ",".join(map(str, chart_ids)) + ")"})
    response.raise_for_status()
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    result = {}
    for entry in archive.infolist():
        parts = PurePosixPath(entry.filename)
        match = re.search(r"_(\d+)\.yaml$", parts.name)
        if parts.parent.name != "charts" or not match:
            continue
        identifier = int(match[1])
        raw = archive.read(entry).decode("utf-8")
        field = re.search(r"^uuid:\s*([0-9a-fA-F-]+)\s*$", raw, re.MULTILINE)
        if identifier in chart_ids and field:
            result[identifier] = str(UUID(field[1]))
    if set(result) != set(chart_ids):
        raise ValueError("Native chart export thiếu UUID; chưa ghi layout không tái tạo được")
    return result


def provision(env_file: Path) -> dict:
    """Tạo/update database→datasets→charts→layout; export spec không chứa credentials."""
    spec = dashboard_spec()
    from air_quality.operations import query_trino
    tables = {row[0] for row in query_trino("SHOW TABLES FROM iceberg.live")["data"]}
    if not {"forecast_actual", "model_metrics"}.issubset(tables):
        spec["datasets"] = {key: value for key, value in spec["datasets"].items()
                            if key not in {"forecast_comparison", "operational_forecasts", "model_metrics"}}
        spec["charts"] = [chart for chart in spec["charts"] if chart["dataset"] in spec["datasets"]]
    client = SupersetClient(env_file)
    try:
        database = client.find("database", "database_name", "Air Quality Lakehouse")
        if database is None:
            database = client.request("POST", "/api/v1/database/", json={
                "database_name": "Air Quality Lakehouse", "sqlalchemy_uri": "trino://airquality@trino:8080/iceberg/live",
                "expose_in_sqllab": True, "allow_run_async": False,
            })
        db_id = database["id"]
        dataset_ids = {}
        for key, source in spec["datasets"].items():
            dataset = client.find("dataset", "table_name", source["table_name"])
            if dataset is None:
                dataset = client.request("POST", "/api/v1/dataset/", json={"database": db_id, **source})
            elif source.get("sql"):
                client.request("PUT", f"/api/v1/dataset/{dataset['id']}", json={"sql": source["sql"]})
            # Dataset virtual mới/đang rỗng cũng cần metadata trước tạo charts.
            client.request("PUT", f"/api/v1/dataset/{dataset['id']}/refresh")
            labels = {"station_name": "Trạm", "parameter_name": "Chỉ số", "series_kind": "Chuỗi nguồn",
                      "last_measurement_local": "Số đo cuối (giờ VN)", "age_minutes": "Độ trễ (phút)", "records": "Bản ghi",
                      "local_date": "Ngày Việt Nam", "mean_value": "Trung bình (µg/m³)", "valid_hours": "Giờ hợp lệ",
                      "expected_hours": "Giờ kỳ vọng", "coverage_percent": "Độ phủ (%)",
                      "algorithm": "Phương pháp", "n": "Số mẫu test", "mae": "MAE (µg/m³)", "rmse": "RMSE (µg/m³)",
                      "model_version": "Phiên bản model", "issued_local": "Phát hành (giờ VN)", "target_local": "Giờ dự báo (VN)",
                      "predicted_value": "RF (µg/m³)", "baseline_value": "Persistence (µg/m³)",
                      "actual_value": "Thực tế (µg/m³)", "error": "Sai số RF (µg/m³)"}
            detail = client.request("GET", f"/api/v1/dataset/{dataset['id']}")["result"]
            columns = [{"id": col["id"], "column_name": col["column_name"],
                        "verbose_name": labels.get(col["column_name"], col.get("verbose_name")),
                        "type": col["type"], "is_dttm": col["is_dttm"]} for col in detail["columns"]]
            client.request("PUT", f"/api/v1/dataset/{dataset['id']}", json={"columns": columns})
            dataset_ids[key] = dataset["id"]
        dashboard = client.find("dashboard", "slug", spec["slug"])
        if dashboard is None:
            dashboard = client.request("POST", "/api/v1/dashboard/", json={
                "dashboard_title": spec["title"], "slug": spec["slug"], "published": True,
            })
        dashboard_id = dashboard["id"]
        chart_ids = []
        for chart in spec["charts"]:
            dataset_id = dataset_ids[chart["dataset"]]
            payload = {"slice_name": chart["name"], "viz_type": chart["type"], "datasource_id": dataset_id,
                       "datasource_type": "table", "params": json.dumps(form_data(chart, dataset_id), ensure_ascii=False),
                       "dashboards": [dashboard_id]}
            saved = client.find("chart", "slice_name", chart["name"])
            if saved is None:
                saved = client.request("POST", "/api/v1/chart/", json=payload)
            else:
                client.request("PUT", f"/api/v1/chart/{saved['id']}", json=payload)
            chart_ids.append(saved["id"])
        identities = chart_uuids(client, chart_ids)
        layout: dict = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
                        "GRID_ID": {"id": "GRID_ID", "type": "GRID", "children": ["SOURCE-NOTE"], "parents": ["ROOT_ID"]},
                        "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": spec["title"]}}}
        layout["SOURCE-NOTE"] = {"id": "SOURCE-NOTE", "type": "MARKDOWN", "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                                 "meta": {"width": 12, "height": 15, "code": "**ĐHBK · Công viên Nhân Chính** — Nguồn: OpenAQ / Hanoi AQ Monitoring Network. Đơn vị µg/m³, giờ VN (UTC+7). Biểu đồ 7 ngày tới hiện tại; khoảng trống là thiếu dữ liệu. Ngày hiện tại chưa đủ 24 giờ. **Backtest** là đánh giá hồi cứu trên snapshot, không phải dự báo đã phát hành trong quá khứ; bảng **Dự báo đã phát hành** ghi operational. RF chưa thắng persistence nhất quán, xem MAE/RMSE trên cùng mẫu test.", "background": "BACKGROUND_TRANSPARENT"}}
        for index, chart_id in enumerate(chart_ids):
            row_id = f"ROW-{index // 2}" if index < 4 else f"ROW-FULL-{index}"
            chart_key = f"CHART-{chart_id}"
            if row_id not in layout:
                layout["GRID_ID"]["children"].append(row_id)
                layout[row_id] = {"id": row_id, "type": "ROW", "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                                  "meta": {"background": "BACKGROUND_TRANSPARENT"}}
            layout[row_id]["children"].append(chart_key)
            layout[chart_key] = {"id": chart_key, "type": "CHART", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id],
                                 "meta": {"chartId": chart_id, "width": 6 if index < 4 else 12, "height": 55,
                                          "sliceName": spec["charts"][index]["name"], "uuid": identities[chart_id]}}
        client.request("PUT", f"/api/v1/dashboard/{dashboard_id}", json={"position_json": json.dumps(layout),
                       "json_metadata": json.dumps({"refresh_frequency": 60, "color_scheme": "supersetColors"})})
        exported = export_native(client, dashboard_id, ROOT / "dashboards/export")
        (ROOT / "dashboards/air-quality-spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = {"dashboard_id": dashboard_id, "chart_ids": chart_ids, "dataset_ids": dataset_ids,
                  "url": f"http://localhost:18088/superset/dashboard/{spec['slug']}/", "native_export_files": exported}
        (ROOT / "artifacts/local/dashboard-provision.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    finally:
        client.close()
