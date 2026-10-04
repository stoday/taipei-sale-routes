from coverage import Camera, analyze_route_coverage, is_camera_covering_point, rank_routes
from routes import RouteCandidate


def test_camera_within_radius_covers_point():
    camera = Camera("CAM001", 25.0, 121.0, "UNKNOWN")

    assert is_camera_covering_point(camera, (25.0, 121.0004)) is True


def test_camera_outside_radius_does_not_cover_point():
    camera = Camera("CAM001", 25.0, 121.0, "UNKNOWN")

    assert is_camera_covering_point(camera, (25.0, 121.001)) is False


def test_directional_camera_only_covers_points_in_its_field_of_view():
    camera = Camera("CAM001", 25.0, 121.0, "E")

    assert is_camera_covering_point(camera, (25.0, 121.0004)) is True
    assert is_camera_covering_point(camera, (25.0004, 121.0)) is False


def test_unknown_direction_uses_distance_only():
    camera = Camera("CAM001", 25.0, 121.0, "UNKNOWN")

    assert is_camera_covering_point(camera, (25.0004, 121.0)) is True


def test_route_analysis_calculates_ratio_and_longest_uncovered_gap():
    cameras = [
        Camera("CAM001", 25.0, 121.0, "UNKNOWN"),
        Camera("CAM002", 25.0, 121.0012, "UNKNOWN"),
    ]
    route = RouteCandidate(
        route_id="route-1",
        distance_m=40,
        duration_sec=60,
        encoded_polyline="",
        points=[(25.0, 121.0), (25.0, 121.0012)],
    )

    result = analyze_route_coverage(route, cameras, interval_m=60)

    assert result.coverage_ratio == 0.75
    assert result.longest_uncovered_gap_m == 60
    assert result.covered is False


def test_rank_routes_prefers_qualifying_route_before_shorter_route():
    covered = RouteCandidate("covered", 1200, 1_500, "", [], 0.96, 10, True)
    fastest = RouteCandidate("fastest", 1000, 1_200, "", [], 0.90, 80, False)

    assert rank_routes([fastest, covered])[0].route_id == "covered"
