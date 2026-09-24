from sqlalchemy.dialects import postgresql

from app.models.alert import AlertStatus
from app.services.incident_density_grid import (
    CELL_SIZE_METRES,
    HISTORICAL_INCIDENT_STATUSES,
    incident_grid_expressions,
)


def test_cell_size_is_100_metres():
    assert CELL_SIZE_METRES == 100


def test_historical_statuses_include_confirmed_and_resolved():
    assert AlertStatus.CONFIRMED.value in (
        HISTORICAL_INCIDENT_STATUSES
    )
    assert AlertStatus.RESOLVED.value in (
        HISTORICAL_INCIDENT_STATUSES
    )


def test_historical_statuses_exclude_open_and_acknowledged():
    assert AlertStatus.OPEN.value not in (
        HISTORICAL_INCIDENT_STATUSES
    )
    assert AlertStatus.ACKNOWLEDGED.value not in (
        HISTORICAL_INCIDENT_STATUSES
    )


def test_grid_expression_returns_four_expressions():
    expressions = incident_grid_expressions()

    assert len(expressions) == 4
    assert all(expression is not None for expression in expressions)


def test_grid_expression_uses_projected_snapped_geometry():
    expressions = incident_grid_expressions()

    compiled = "\n".join(
        str(
            expression.compile(
                dialect=postgresql.dialect(),
            )
        )
        for expression in expressions
    ).lower()

    assert "st_makepoint" in compiled
    assert "st_transform" in compiled
    assert "st_snaptogrid" in compiled