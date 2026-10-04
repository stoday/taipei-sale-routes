import math

from geo import (
    angle_difference,
    bearing_degree,
    haversine_m,
    sample_route,
    street_corner_checkpoints,
)


def test_haversine_returns_known_distance_between_taipei_landmarks():
    distance = haversine_m(25.0478, 121.5170, 25.0422, 121.5081)

    assert 1_050 <= distance <= 1_150


def test_bearing_points_east_and_wraps_angle_difference():
    assert 89 <= bearing_degree(25.0, 121.0, 25.0, 121.001) <= 91
    assert angle_difference(350, 10) == 20


def test_sample_route_creates_points_at_requested_interval():
    points = [(25.0, 121.0), (25.0, 121.0018)]

    samples = sample_route(points, interval_m=50)

    assert samples[0] == points[0]
    assert samples[-1] == points[-1]
    assert 4 <= len(samples) <= 6


def test_street_corner_checkpoints_include_endpoints_and_significant_turns():
    points = [
        (25.0, 121.0),
        (25.0, 121.001),
        (25.001, 121.001),
        (25.001, 121.002),
    ]

    checkpoints = street_corner_checkpoints(points)

    assert checkpoints == points


def test_street_corner_checkpoints_can_focus_only_on_turns():
    points = [
        (25.0, 121.0),
        (25.0, 121.001),
        (25.001, 121.001),
        (25.001, 121.002),
    ]

    checkpoints = street_corner_checkpoints(points, include_endpoints=False)

    assert checkpoints == points[1:3]
