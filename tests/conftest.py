"""Không cho test offline vô tình đọc key hoặc gọi dịch vụ thật.

Lab live/integration phải được bật tường minh. Test unit dùng MockTransport
và SQLite trong thư mục pytest, không nạp .env của người dùng.
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-live", action="store_true", default=False, help="Cho phép test OpenAQ thật")
    parser.addoption("--run-integration", action="store_true", default=False, help="Cho phép test stack local")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        # item.keywords còn chứa tên thư mục "integration". Dùng marker thực
        # để một test live không bị skip chỉ vì nó nằm dưới tests/integration.
        if item.get_closest_marker("live") and not config.getoption("--run-live"):
            item.add_marker(pytest.mark.skip(reason="Cần --run-live và API key local"))
        if item.get_closest_marker("integration") and not config.getoption("--run-integration"):
            item.add_marker(pytest.mark.skip(reason="Cần --run-integration và stack local"))
