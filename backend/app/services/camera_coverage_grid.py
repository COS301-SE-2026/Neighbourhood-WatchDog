from dataclasses import dataclass
from math import atan, degrees, isfinite, log, pi, radians, sinh, tan

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from app.core.camera_coverage import (
    MAX_CAMERA_COVERAGE_RANGE_METRES,
    MAX_CAMERA_ORIGIN_DISTANCE_METRES,
    coverage_polygon,
    haversine_distance_metres,
)
from app.services.incident_density_grid import CELL_SIZE_METRES


WEB_MERCATOR_RADIUS_METRES = 6_378_137.0
WEB_MERCATOR_MAX_LATITUDE = 85.05112878
SECTOR_ARC_SEGMENTS = 36


@dataclass(frozen=True)
class GridCell:
    """A cell from the shared EPSG:3857 incident-density grid."""

    grid_x: int
    grid_y: int

    @property
    def cell_id(self) -> str:
        return f"{self.grid_x}:{self.grid_y}"


@dataclass(frozen=True)
class CameraCoverageRecord:
    """Database-independent camera coverage input."""

    enabled: bool
    property_latitude: float | None
    property_longitude: float | None
    origin_latitude: float
    origin_longitude: float
    coverage_bearing_degrees: float
    coverage_angle_degrees: float
    coverage_range_metres: float


@dataclass(frozen=True)
class CellCoverage:
    cell_id: str
    grid_x: int
    grid_y: int
    latitude: float
    longitude: float
    coverage_ratio: float


def wgs84_to_web_mercator(
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """Project WGS84 coordinates into the grid's EPSG:3857 space."""
    bounded_latitude = max(
        -WEB_MERCATOR_MAX_LATITUDE,
        min(WEB_MERCATOR_MAX_LATITUDE, latitude),
    )

    x = WEB_MERCATOR_RADIUS_METRES * radians(longitude)
    y = WEB_MERCATOR_RADIUS_METRES * log(
        tan(pi / 4 + radians(bounded_latitude) / 2)
    )

    return x, y


def web_mercator_to_wgs84(
    x: float,
    y: float,
) -> tuple[float, float]:
    """Convert an EPSG:3857 coordinate to latitude and longitude."""
    longitude = degrees(x / WEB_MERCATOR_RADIUS_METRES)
    latitude = degrees(
        atan(sinh(y / WEB_MERCATOR_RADIUS_METRES))
    )

    return latitude, longitude


def _coordinate_is_valid(
    latitude: float,
    longitude: float,
) -> bool:
    return (
        isfinite(latitude)
        and isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def camera_coverage_is_valid(
    record: CameraCoverageRecord,
) -> bool:
    if not record.enabled:
        return False

    if (
        record.property_latitude is None
        or record.property_longitude is None
    ):
        return False

    if not _coordinate_is_valid(
        record.property_latitude,
        record.property_longitude,
    ):
        return False

    if not _coordinate_is_valid(
        record.origin_latitude,
        record.origin_longitude,
    ):
        return False

    numeric_values = (
        record.coverage_bearing_degrees,
        record.coverage_angle_degrees,
        record.coverage_range_metres,
    )

    if not all(isfinite(value) for value in numeric_values):
        return False

    if not 0 <= record.coverage_bearing_degrees < 360:
        return False

    if not 1 <= record.coverage_angle_degrees <= 180:
        return False

    if not (
        1
        <= record.coverage_range_metres
        <= MAX_CAMERA_COVERAGE_RANGE_METRES
    ):
        return False

    origin_distance = haversine_distance_metres(
        record.property_latitude,
        record.property_longitude,
        record.origin_latitude,
        record.origin_longitude,
    )

    return (
        origin_distance
        <= MAX_CAMERA_ORIGIN_DISTANCE_METRES
    )


def _projected_sector(
    record: CameraCoverageRecord,
) -> Polygon:
    geographic_points = coverage_polygon(
        origin_latitude=record.origin_latitude,
        origin_longitude=record.origin_longitude,
        bearing_degrees=record.coverage_bearing_degrees,
        angle_degrees=record.coverage_angle_degrees,
        range_metres=record.coverage_range_metres,
    )

    return Polygon(
        [
            wgs84_to_web_mercator(
                latitude,
                longitude,
            )
            for latitude, longitude in geographic_points
        ]
    )


def calculate_cell_coverage(
    cells: list[GridCell],
    camera_coverages: list[CameraCoverageRecord],
) -> list[CellCoverage]:
    """Calculate unioned coverage for each requested grid cell."""
    valid_sectors = [
        _projected_sector(record)
        for record in camera_coverages
        if camera_coverage_is_valid(record)
    ]

    combined_coverage = (
        unary_union(valid_sectors)
        if valid_sectors
        else None
    )

    cell_area = float(CELL_SIZE_METRES**2)
    results: list[CellCoverage] = []

    for cell in cells:
        cell_geometry = box(
            cell.grid_x,
            cell.grid_y,
            cell.grid_x + CELL_SIZE_METRES,
            cell.grid_y + CELL_SIZE_METRES,
        )

        covered_area = (
            combined_coverage.intersection(
                cell_geometry
            ).area
            if combined_coverage is not None
            else 0.0
        )

        coverage_ratio = max(
            0.0,
            min(1.0, covered_area / cell_area),
        )

        latitude, longitude = (
            web_mercator_to_wgs84(
                cell.grid_x + CELL_SIZE_METRES / 2,
                cell.grid_y + CELL_SIZE_METRES / 2,
            )
        )

        results.append(
            CellCoverage(
                cell_id=cell.cell_id,
                grid_x=cell.grid_x,
                grid_y=cell.grid_y,
                latitude=latitude,
                longitude=longitude,
                coverage_ratio=coverage_ratio,
            )
        )

    return results
