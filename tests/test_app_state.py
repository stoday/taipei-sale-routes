from streamlit.testing.v1 import AppTest
from pathlib import Path

from coverage import Camera
from routes import RouteCandidate


def test_analysis_result_survives_a_streamlit_rerun():
    route = RouteCandidate(
        route_id="route-1",
        distance_m=1200,
        duration_sec=900,
        encoded_polyline="",
        points=[(25.0478, 121.5170), (25.0422, 121.5081)],
        coverage_ratio=0.98,
        longest_uncovered_gap_m=10,
        covered=True,
    )
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
    app.session_state["analyzed_routes"] = [route]
    app.session_state["cameras"] = [Camera("CAM001", 25.045, 121.513, "UNKNOWN")]

    app.run()
    assert app.metric[0].value == "98%"

    app.run()
    assert app.metric[0].value == "98%"
    assert not app.exception
