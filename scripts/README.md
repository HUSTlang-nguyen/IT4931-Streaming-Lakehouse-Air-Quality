# Scripts hỗ trợ

CLI vận hành ở src/air_quality/cli.py, không sao chép nghiệp vụ sang script. [export_presentation_snippets.py](export_presentation_snippets.py) trích AST/source thật thành docs/presentation-guide.md,10–25 dòng/đoạn và SHA256 để so context sau refactor.

```powershell
.venv/Scripts/python.exe scripts/export_presentation_snippets.py
```

Không cần Docker/API cho script trích code, không sửa slide cũ hoặc source nghiệp vụ.

`verify_repository.py` kiểm syntax/TOML, links, diff và secret local không lọt Git; chỉ báo tên file nếu lỗi, không in secret. Source fingerprint chuẩn hóa CRLF để đối chiếu code Windows/container sau đổi branch. Script cần Python3.11+.
