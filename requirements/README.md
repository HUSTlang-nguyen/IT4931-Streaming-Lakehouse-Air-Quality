# Dependency snapshots

`dev-host-py313.lock` là freeze thực tế .venv Windows Python3.13 sau Collector tests; không dùng để khẳng định Spark/Python3.11 Linux tương thích. Runtime lock được tạo/kiểm chứng khi build container. Direct dependencies pin trong pyproject.
