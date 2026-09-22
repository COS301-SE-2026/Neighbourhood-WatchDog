import sys
from pathlib import Path
import pytest
import os

os.environ.setdefault("TESTING", "true")


backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))


integration_root = (Path(__file__).parent / "integration").resolve()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run backend integration tests against the configured test database"

    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip integration tests unless explicitly enabled."""

    run_integration = config.getoption(
        "--run-integration",
        default=False,
    )

    if run_integration:
        return

    skip_integration = pytest.mark.skip(
        reason="Integration tests require --run-integration"
    )

    for item in items:
        test_file = Path(str(item.fspath)).resolve()

        if integration_root in test_file.parents:
            item.add_marker(skip_integration)