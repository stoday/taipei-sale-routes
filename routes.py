"""Google Routes API adapter and route data model."""

from dataclasses import dataclass
import os
from typing import Any, Callable


@dataclass
class RouteCandidate:
    route_id: str
    distance_m: float
    duration_sec: float
    encoded_polyline: str
    points: list[tuple[float, float]]
    coverage_ratio: float = 0.0
    longest_uncovered_gap_m: float = 0.0
    covered: bool = False


ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
FIELD_MASK = "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"


def _duration_seconds(value: str | None) -> float:
    if not value:
        return 0.0
    return float(value.rstrip("s"))


def get_routes(
    origin: dict[str, float],
    destination: dict[str, float],
    api_key: str | None = None,
    http_post: Callable[..., Any] | None = None,
) -> list[RouteCandidate]:
    """Fetch and decode candidate walking routes from Google Routes API."""
    if not api_key:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")
    if http_post is None:
        import requests

        http_post = requests.post

    payload = {
        "origin": {"location": {"latLng": {"latitude": origin["lat"], "longitude": origin["lng"]}}},
        "destination": {
            "location": {"latLng": {"latitude": destination["lat"], "longitude": destination["lng"]}}
        },
        "travelMode": "WALK",
        "computeAlternativeRoutes": True,
    }
    response = http_post(
        ROUTES_URL,
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK},
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Routes API request failed ({response.status_code})")
    body = response.json()
    try:
        import polyline
    except ImportError as exc:
        raise RuntimeError("polyline package is required to decode routes") from exc

    candidates = []
    for index, route in enumerate(body.get("routes", []), start=1):
        encoded = route.get("polyline", {}).get("encodedPolyline", "")
        candidates.append(
            RouteCandidate(
                route_id=f"route-{index}",
                distance_m=float(route.get("distanceMeters", 0)),
                duration_sec=_duration_seconds(route.get("duration")),
                encoded_polyline=encoded,
                points=polyline.decode(encoded) if encoded else [],
            )
        )
    return candidates

