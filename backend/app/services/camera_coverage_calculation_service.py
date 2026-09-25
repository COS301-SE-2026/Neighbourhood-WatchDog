from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.camera_coverage import CameraCoverage
from app.models.property import Property
from app.services.camera_coverage_grid import (
    CameraCoverageRecord,
    CellCoverage,
    GridCell,
    calculate_cell_coverage,
)


async def load_neighbourhood_camera_coverages(
    neighbourhood_id: UUID,
    db: AsyncSession,
) -> list[CameraCoverageRecord]:
    """Load valid candidate camera configurations for a neighbourhood."""
    statement = (
        select(
            Camera.enabled.label("enabled"),
            Property.latitude.label("property_latitude"),
            Property.longitude.label("property_longitude"),
            CameraCoverage.origin_latitude.label(
                "origin_latitude"
            ),
            CameraCoverage.origin_longitude.label(
                "origin_longitude"
            ),
            CameraCoverage.coverage_bearing_degrees.label(
                "coverage_bearing_degrees"
            ),
            CameraCoverage.coverage_angle_degrees.label(
                "coverage_angle_degrees"
            ),
            CameraCoverage.coverage_range_metres.label(
                "coverage_range_metres"
            ),
        )
        .select_from(Camera)
        .join(
            Property,
            Property.id == Camera.property_id,
        )
        .join(
            CameraCoverage,
            CameraCoverage.camera_id == Camera.id,
        )
        .where(
            Property.neighbourhood_id == neighbourhood_id,
            Camera.enabled.is_(True),
            Property.latitude.is_not(None),
            Property.longitude.is_not(None),
        )
    )

    result = await db.execute(statement)
    rows = result.mappings().all()

    return [
        CameraCoverageRecord(
            enabled=bool(row["enabled"]),
            property_latitude=float(
                row["property_latitude"]
            ),
            property_longitude=float(
                row["property_longitude"]
            ),
            origin_latitude=float(
                row["origin_latitude"]
            ),
            origin_longitude=float(
                row["origin_longitude"]
            ),
            coverage_bearing_degrees=float(
                row["coverage_bearing_degrees"]
            ),
            coverage_angle_degrees=float(
                row["coverage_angle_degrees"]
            ),
            coverage_range_metres=float(
                row["coverage_range_metres"]
            ),
        )
        for row in rows
    ]


async def calculate_neighbourhood_cell_coverage(
    neighbourhood_id: UUID,
    cells: list[GridCell],
    db: AsyncSession,
) -> list[CellCoverage]:
    """Calculate camera coverage for the requested neighbourhood cells."""
    camera_coverages = (
        await load_neighbourhood_camera_coverages(
            neighbourhood_id=neighbourhood_id,
            db=db,
        )
    )

    return calculate_cell_coverage(
        cells=cells,
        camera_coverages=camera_coverages,
    )
