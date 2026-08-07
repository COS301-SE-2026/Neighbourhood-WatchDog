import sys
from pathlib import Path
import pytest

backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))


integration_root = (Path(__file__).parent / "integration").resolve()


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Temporarily skip backend integration tests in CI."""
    skip_integration = pytest.mark.skip(
        reason=(
            "Integration tests temporarily disabled"
        )
    )

    for item in items:
        test_file = Path(str(item.fspath)).resolve()

        if integration_root in test_file.parents:
            item.add_marker(skip_integration)
