"""Trích đúng code hiện hành vào Markdown thuyết trình, không nhân bản nghiệp vụ.

Chạy lại sau refactor. AST kiểm tên hàm còn tồn tại; needle xác định đoạn cần
đưa lên slide. SHA256 source giúp nhận biết tài liệu trích từ phiên bản nào.
"""

import ast
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    ("Crawl và lưu trang trước ACK", "collector/service.py", "collect_window", "            while not done:", 22,
     "Input: sensor/khoảng UTC/trang; output: raw archive và envelope có provenance.",
     "Một khoảng thời gian có thể có nhiều trang API. Code giữ từng trang thành archive bất biến trước khi gửi Kafka. Khi process chết, lần tiếp đọc lại chính archive để giữ event ID và thời điểm thu. Chỉ ACK đủ trang mới tăng checkpoint; downstream MERGE xử lý trường hợp broker đã nhận nhưng checkpoint chưa ghi. Đây là cơ chế tránh mất trang, không phải giả định mạng luôn thành công. Test crash-before-ACK và source reconciliation cung cấp bằng chứng."),
    ("Chuẩn hóa measurement", "processing/transforms.py", "normalize", "    df = frame.withColumn", 20,
     "Input: envelope raw JSON; output: period UTC/value/unit/provider và flags trong Silver.",
     "Một dòng chỉ đo một chỉ số của một sensor. Code parse hai đầu khoảng đo, giữ interval nguồn và metadata liên kết ID. Chỉ chuẩn hóa hai ký tự micro giống nghĩa, không tự đổi mg sang microgram. Các điều kiện phía dưới gắn flags cho giá trị âm, sai unit, sai khoảng hoặc metadata. Bản invalid còn raw để truy vết, Gold giữ null thay vì zero; đây là cách tránh đồ thị nhìn đẹp nhưng sai dữ liệu."),
    ("MERGE chống trùng và correction", "processing/tables.py", "merge_silver", None, 25,
     "Input: normalized rows; output: một hàng mỗi sensor/series/khoảng đo.",
     "Khóa Silver gồm sensor, series_kind và cả đầu/cuối khoảng đo. Raw và hours không bị gộp nhầm. Trong batch chọn observation mới nhất, sau đó MERGE chỉ cho observation mới hơn sửa hàng hiện có; event_id là tie-break xác định. Chạy lại cùng trang không nhân đôi khóa, observation cũ không ghi đè correction. Tests gửi original, correction và original lần nữa; count vẫn một và giá trị cuối đúng correction."),
    ("Dữ liệu đến muộn và Gold", "processing/tables.py", "refresh_gold", None, 24,
     "Input: Silver sau MERGE; output: snapshots hourly/daily/freshness mới.",
     "Watermark không dùng để bỏ vĩnh viễn số đo cũ. Late record đi vào Silver như các bản khác rồi Gold được tính lại. Với hai trạm, full refresh đơn giản và dễ kiểm hơn incremental phức tạp. Overwrite commit một snapshot từng bảng, tránh lộ bảng rỗng. Nếu crash sau Silver trước Gold, Kafka checkpoint chưa tiến nên batch retry phục hồi. Test gap ở giờ2 rồi nhận giờ2 muộn chứng minh null được lấp và daily count/mean cập nhật."),
    ("Features causal theo giờ thật", "forecasting/features.py", "feature_rows", "    valid = hourly.filter", 22,
     "Input: Gold snapshot PM2.5; output: current/lag1/2/3/24/hour và max availability.",
     "Lag một giờ phải là số đo đúng timestamp t trừ một giờ. Code dịch timestamp bảng tra cứu rồi inner join, không dùng hàng trước trong file. Thiếu một giờ thì mẫu bị loại thay vì kéo một số đo cách xa làm lag. Operational còn lọc ingested_at trước issued_at cho mọi input. Nhãn giờ kế tiếp được join ở hàm riêng và không có trong vector. Test có gap và input đến muộn kiểm hai ranh giới này; split purge loại target chạm validation/test."),
    ("Đánh giá RF và persistence cùng mẫu", "forecasting/model.py", "regression_metrics", None, 25,
     "Input: cùng scored test rows, cột prediction hoặc current_value; output: n/MAE/RMSE.",
     "MAE là trung bình trị tuyệt đối sai số, RMSE nhạy hơn với sai số lớn. Helper tính cả count để chứng minh RF và persistence được đo cùng số mẫu. Trong train, model chỉ fit train, depth được chọn bằng validation; helper này đánh giá test sau khi đã chọn. Kết quả thật RF chưa thắng persistence nhất quán: ĐHBK MAE gần nhau nhưng RMSE RF cao hơn, Nhân Chính baseline tốt hơn. Backtest snapshot không chứng minh forecast đã phát hành trong quá khứ."),
]


def extract(relative: str, name: str, needle: str | None, maximum: int) -> tuple[str, int, str]:
    """Tìm hàm bằng AST, lấy tối đa25 dòng nguyên bản và hash cả source file."""
    path = ROOT / "src/air_quality" / relative
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    matches = [node for node in ast.walk(ast.parse(source)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"Tên hàm không duy nhất/không tồn tại: {relative}:{name}")
    function = matches[0]
    start = function.lineno - 1
    if needle:
        start = next(index for index in range(start, function.end_lineno) if lines[index].startswith(needle))
    code = "\n".join(lines[start:min(start + maximum, function.end_lineno)])
    if not 10 <= len(code.splitlines()) <= 25:
        raise ValueError(f"Snippet phải10–25 dòng: {name}")
    return code, start + 1, hashlib.sha256(source.encode()).hexdigest()


def main() -> None:
    """Ghi hướng dẫn thuyết trình; không sửa slide cũ hay sửa source code."""
    parts = ["# Sáu đoạn code thật cho thuyết trình\n\nSinh bằng `scripts/export_presentation_snippets.py`; chạy lại sau thay đổi source. Mỗi đoạn10–25 dòng nguyên bản, lời dẫn khoảng30–60 giây. Hash là SHA256 cả source file, không giả hash commit chứa chính tài liệu. Chỉ trình bày kết quả kiểm chứng trong reports; không tự sửa slide cũ.\n"]
    for index, (title, relative, name, needle, maximum, io, speech) in enumerate(SECTIONS, 1):
        code, line, digest = extract(relative, name, needle, maximum)
        parts.append(f"## {index}. {title}\n\nSource: [{name}](../src/air_quality/{relative}#L{line}), bắt đầu dòng{line}. SHA256 `{digest}`.\n\n{io}\n\n```python\n{code}\n```\n\nLời dẫn: {speech}\n")
    parts.append("## Bằng chứng đi cùng\n\n[Collector](../tests/unit/test_collector.py), [Spark quality](../tests/integration/test_lakehouse.py), [ML leakage/retry](../tests/integration/test_forecasting.py), [source coverage](../artifacts/reports/source-coverage.json), [reconciliation](../artifacts/reports/lakehouse-history-reconciliation.json), [restart](../artifacts/reports/restart-persistence.json), [ML metrics](../artifacts/reports/ml-evaluation.json), [Iceberg experiment](../artifacts/reports/iceberg-benchmark.json).\n")
    (ROOT / "docs/presentation-guide.md").write_text("\n".join(parts), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
