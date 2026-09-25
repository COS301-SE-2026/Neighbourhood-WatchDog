import pytest

from app.services.camera_coverage_grid import (
    CameraCoverageRecord,
    GridCell,
    calculate_cell_coverage,
    web_mercator_to_wgs84,
)
from app.services.incident_density_grid import (
    CELL_SIZE_METRES,
)


BASE_GRID_X = 3_142_700
BASE_GRID_Y = -2_963_800

CELL = GridCell(
    grid_x=BASE_GRID_X,
    grid_y=BASE_GRID_Y,
)


def coordinate_at(
    x: float,
    y: float,
) -> tuple[float, float]:
    return web_mercator_to_wgs84(x, y)


def make_coverage(
    *,
    x: float,
    y: float,
    enabled: bool = True,
    bearing: float = 0,
    angle: float = 180,
    range_metres: float = 200,
    property_coordinates: bool = True,
) -> CameraCoverageRecord:
    latitude, longitude = coordinate_at(x, y)

    return CameraCoverageRecord(
        enabled=enabled,
        property_latitude=(
            latitude
            if property_coordinates
            else None
        ),
        property_longitude=(
            longitude
            if property_coordinates
            else None
        ),
        origin_latitude=latitude,
        origin_longitude=longitude,
        coverage_bearing_degrees=bearing,
        coverage_angle_degrees=angle,
        coverage_range_metres=range_metres,
    )


def coverage_ratio(
    *coverages: CameraCoverageRecord,
) -> float:
    results = calculate_cell_coverage(
        [CELL],
        list(coverages),
    )

    return results[0].coverage_ratio


def test_uses_shared_100_metre_grid():
    assert CELL_SIZE_METRES == 100
    assert CELL.cell_id == (
        f"{BASE_GRID_X}:{BASE_GRID_Y}"
    )


def test_no_cameras_returns_zero_coverage():
    assert coverage_ratio() == 0.0


def test_sector_can_partially_cover_cell():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y,
        bearing=0,
        angle=60,
        range_metres=100,
    )

    ratio = coverage_ratio(camera)

    assert 0.0 < ratio < 1.0


def test_sector_can_fully_cover_cell():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y - 1,
        bearing=0,
        angle=180,
        range_metres=200,
    )

    assert coverage_ratio(camera) == pytest.approx(
        1.0,
        abs=0.01,
    )


def test_overlapping_sectors_are_not_double_counted():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y,
        bearing=0,
        angle=60,
        range_metres=100,
    )

    single_ratio = coverage_ratio(camera)
    overlapping_ratio = coverage_ratio(
        camera,
        camera,
    )

    assert overlapping_ratio == pytest.approx(
        single_ratio
    )
    assert overlapping_ratio <= 1.0


def test_disabled_camera_is_ignored():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y,
        enabled=False,
    )

    assert coverage_ratio(camera) == 0.0


def test_camera_without_property_coordinates_is_ignored():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y,
        property_coordinates=False,
    )

    assert coverage_ratio(camera) == 0.0


@pytest.mark.parametrize(
    (
        "bearing",
        "angle",
        "range_metres",
    ),
    [
        (-1, 60, 50),
        (360, 60, 50),
        (90, 0, 50),
        (90, 181, 50),
        (90, 60, 0),
        (90, 60, 201),
    ],
)
def test_invalid_configuration_is_ignored(
    bearing: float,
    angle: float,
    range_metres: float,
):
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y,
        bearing=bearing,
        angle=angle,
        range_metres=range_metres,
    )

    assert coverage_ratio(camera) == 0.0


def test_result_contains_centre_and_clamped_ratio():
    camera = make_coverage(
        x=BASE_GRID_X + 50,
        y=BASE_GRID_Y - 1,
    )

    result = calculate_cell_coverage(
        [CELL],
        [camera],
    )[0]

    expected_latitude, expected_longitude = (
        coordinate_at(
            BASE_GRID_X
            + CELL_SIZE_METRES / 2,
            BASE_GRID_Y
            + CELL_SIZE_METRES / 2,
        )
    )

    assert result.cell_id == CELL.cell_id
    assert result.latitude == pytest.approx(
        expected_latitude
    )
    assert result.longitude == pytest.approx(
        expected_longitude
    )
    assert 0.0 <= result.coverage_ratio <= 1.0
