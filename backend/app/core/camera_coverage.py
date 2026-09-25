from math import asin, atan2, cos, degrees, radians, sin

EARTH_RADIUS_METRES = 6_371_000.0
MAX_CAMERA_ORIGIN_DISTANCE_METRES = 100.0
MAX_CAMERA_COVERAGE_RANGE_METRES = 200.0


def haversine_distance_metres(
    latitude_one: float,
    longitude_one: float,
    latitude_two: float,
    longitude_two: float,
) -> float:
    """Return the great-circle distance between two WGS84 coordinates."""
    latitude_one_radians = radians(latitude_one)
    latitude_two_radians = radians(latitude_two)
    delta_latitude = radians(latitude_two - latitude_one)
    delta_longitude = radians(longitude_two - longitude_one)

    a = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_one_radians)
        * cos(latitude_two_radians)
        * sin(delta_longitude / 2) ** 2
    )

    return 2 * EARTH_RADIUS_METRES * asin(min(1.0, a**0.5))


def destination_point(
    latitude: float,
    longitude: float,
    bearing_degrees: float,
    distance_metres: float,
) -> tuple[float, float]:
    """Return a coordinate reached by travelling from a point on a bearing."""
    latitude_radians = radians(latitude)
    longitude_radians = radians(longitude)
    bearing_radians = radians(bearing_degrees)
    angular_distance = distance_metres / EARTH_RADIUS_METRES

    destination_latitude = asin(
        sin(latitude_radians) * cos(angular_distance)
        + cos(latitude_radians)
        * sin(angular_distance)
        * cos(bearing_radians)
    )

    destination_longitude = longitude_radians + atan2(
        sin(bearing_radians) * sin(angular_distance) * cos(latitude_radians),
        cos(angular_distance)
        - sin(latitude_radians) * sin(destination_latitude),
    )

    return (
        degrees(destination_latitude),
        (degrees(destination_longitude) + 540) % 360 - 180,
    )


def coverage_polygon(
    origin_latitude: float,
    origin_longitude: float,
    bearing_degrees: float,
    angle_degrees: float,
    range_metres: float,
) -> list[list[float]]:
    """Build a triangular geographic POV polygon in [latitude, longitude] order."""
    left_endpoint = destination_point(
        origin_latitude,
        origin_longitude,
        bearing_degrees - angle_degrees / 2,
        range_metres,
    )
    right_endpoint = destination_point(
        origin_latitude,
        origin_longitude,
        bearing_degrees + angle_degrees / 2,
        range_metres,
    )

    return [
        [origin_latitude, origin_longitude],
        [left_endpoint[0], left_endpoint[1]],
        [right_endpoint[0], right_endpoint[1]],
    ]