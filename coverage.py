"""Estimated CCTV coverage calculations."""

from dataclasses import dataclass
import csv
from pathlib import Path

from geo import angle_difference, bearing_degree, haversine_m, sample_route
from routes import RouteCandidate


CAMERA_RADIUS_M = 50
CAMERA_FOV_HALF_ANGLE = 45
ROUTE_SAMPLE_INTERVAL_M = 10
MIN_COVERAGE_RATIO = 0.95
MAX_UNCOVERED_GAP_M = 20


@dataclass(frozen=True)
class Camera:
    camera_id: str
    lat: float
    lng: float
    direction: str = "UNKNOWN"


def _normalise_direction(direction: str | None) -> str:
    value = (direction or "UNKNOWN").strip().upper()
    return value if value in {"N", "NE", "E", "SE", "S", "SW", "W", "NW"} else "UNKNOWN"


def load_cameras(path: str | Path) -> list[Camera]:
    """Load either the PRD's normalized CSV or the official WGSX/WGSY export."""
    cameras = []
    try:
        csv_file = open(path, "r", encoding="utf-8-sig", newline="")
        csv_file.read(1)
        csv_file.seek(0)
    except UnicodeDecodeError:
        csv_file = open(path, "r", encoding="big5", newline="")
    with csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            lat_value = row.get("lat") or row.get("latitude") or row.get("WGSY")
            lng_value = row.get("lng") or row.get("longitude") or row.get("WGSX")
            if not lat_value or not lng_value:
                continue
            camera_id = row.get("id") or row.get("編號") or f"CAM{index:03d}"
            cameras.append(
                Camera(
                    camera_id=str(camera_id),
                    lat=float(lat_value),
                    lng=float(lng_value),
                    direction=_normalise_direction(row.get("direction")),
                )
            )
    return cameras


def is_camera_covering_point(camera: Camera, point: tuple[float, float]) -> bool:
    if haversine_m(camera.lat, camera.lng, point[0], point[1]) > CAMERA_RADIUS_M:
        return False
    if camera.direction == "UNKNOWN":
        return True
    directions = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
    target_bearing = bearing_degree(camera.lat, camera.lng, point[0], point[1])
    return angle_difference(directions[camera.direction], target_bearing) <= CAMERA_FOV_HALF_ANGLE


def calculate_longest_gap(coverage_flags: list[bool], sample_interval_m: float) -> float:
    longest = current = 0
    for covered in coverage_flags:
        current = 0 if covered else current + 1
        longest = max(longest, current)
    return longest * sample_interval_m


def analyze_route_coverage(
    route: RouteCandidate, cameras: list[Camera], interval_m: float = ROUTE_SAMPLE_INTERVAL_M
) -> RouteCandidate:
    samples = sample_route(route.points, interval_m)
    flags = [any(is_camera_covering_point(camera, point) for camera in cameras) for point in samples]
    route.coverage_ratio = sum(flags) / len(flags) if flags else 0.0
    route.longest_uncovered_gap_m = calculate_longest_gap(flags, interval_m)
    route.covered = (
        route.coverage_ratio >= MIN_COVERAGE_RATIO
        and route.longest_uncovered_gap_m <= MAX_UNCOVERED_GAP_M
    )
    return route


def rank_routes(routes: list[RouteCandidate]) -> list[RouteCandidate]:
    return sorted(
        routes,
        key=lambda route: (
            not route.covered,
            -route.coverage_ratio,
            route.longest_uncovered_gap_m,
            route.duration_sec,
        ),
    )
