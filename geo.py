"""Small, dependency-free geographic helpers used by the coverage engine."""

import math


EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_degree(
    camera_lat: float, camera_lng: float, target_lat: float, target_lng: float
) -> float:
    lat1, lat2 = math.radians(camera_lat), math.radians(target_lat)
    delta_lng = math.radians(target_lng - camera_lng)
    x = math.sin(delta_lng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lng)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def angle_difference(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def sample_route(points: list[tuple[float, float]], interval_m: float = 10) -> list[tuple[float, float]]:
    """Interpolate a polyline so adjacent samples are at most interval_m apart."""
    if not points:
        return []
    if len(points) == 1 or interval_m <= 0:
        return list(points)

    samples = [points[0]]
    carry_distance = 0.0
    previous = points[0]
    for current in points[1:]:
        segment_distance = haversine_m(*previous, *current)
        if segment_distance == 0:
            previous = current
            continue
        distance_along_segment = interval_m - carry_distance
        while distance_along_segment < segment_distance:
            fraction = distance_along_segment / segment_distance
            samples.append(
                (
                    previous[0] + (current[0] - previous[0]) * fraction,
                    previous[1] + (current[1] - previous[1]) * fraction,
                )
            )
            distance_along_segment += interval_m
        carry_distance = (carry_distance + segment_distance) % interval_m
        previous = current
    if samples[-1] != points[-1]:
        samples.append(points[-1])
    return samples

