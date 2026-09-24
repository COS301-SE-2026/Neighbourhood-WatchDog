from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.alert import IncidentDensityQuery
from app.schemas.neighbourhood import NeighbourhoodMapPropertyRes


def valid_density_query():
    return {
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 9, 23),
        "west": 28.20,
        "south": -25.80,
        "east": 28.30,
        "north": -25.70,
    }


def test_incident_density_query_accepts_valid_filters():
    query = IncidentDensityQuery(
        **valid_density_query(),
    )

    assert query.start_date == date(2026, 9, 1)
    assert query.end_date == date(2026, 9, 23)
    assert query.west < query.east
    assert query.south < query.north


def test_incident_density_query_rejects_reversed_dates():
    values = valid_density_query()
    values["start_date"] = date(2026, 9, 24)

    with pytest.raises(
        ValidationError,
        match="start_date must not be after end_date",
    ):
        IncidentDensityQuery(**values)


def test_incident_density_query_rejects_invalid_longitude_range():
    values = valid_density_query()
    values["west"] = values["east"]

    with pytest.raises(
        ValidationError,
        match="west must be less than east",
    ):
        IncidentDensityQuery(**values)


def test_incident_density_query_rejects_invalid_latitude_range():
    values = valid_density_query()
    values["south"] = values["north"]

    with pytest.raises(
        ValidationError,
        match="south must be less than north",
    ):
        IncidentDensityQuery(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("west", -181),
        ("east", 181),
        ("south", -91),
        ("north", 91),
    ],
)
def test_incident_density_query_rejects_out_of_bounds_viewport(
    field,
    value,
):
    values = valid_density_query()
    values[field] = value

    with pytest.raises(ValidationError):
        IncidentDensityQuery(**values)


def test_map_property_accepts_geocoded_coordinates():
    property_response = NeighbourhoodMapPropertyRes(
        id=uuid4(),
        address="12 Main Street",
        property_type="PRIVATE",
        latitude=-25.7479,
        longitude=28.2293,
    )

    assert property_response.latitude == -25.7479
    assert property_response.longitude == 28.2293


def test_map_property_accepts_ungeocoded_coordinates():
    property_response = NeighbourhoodMapPropertyRes(
        id=uuid4(),
        address="Unknown Location",
        property_type="PUBLIC",
        latitude=None,
        longitude=None,
    )

    assert property_response.latitude is None
    assert property_response.longitude is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", -91),
        ("latitude", 91),
        ("longitude", -181),
        ("longitude", 181),
    ],
)
def test_map_property_rejects_invalid_coordinates(
    field,
    value,
):
    values = {
        "id": uuid4(),
        "address": "12 Main Street",
        "property_type": "PRIVATE",
        "latitude": -25.7479,
        "longitude": 28.2293,
    }
    values[field] = value

    with pytest.raises(ValidationError):
        NeighbourhoodMapPropertyRes(**values)