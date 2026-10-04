from routes import get_routes


class FakeResponse:
    status_code = 200

    def json(self):
        return {
            "routes": [
                {
                    "distanceMeters": 1200,
                    "duration": "900s",
                    "polyline": {"encodedPolyline": "_p~iF~ps|U_ulLnnqC_mqNvxq`@"},
                }
            ]
        }


def test_get_routes_builds_walking_request_and_returns_decoded_candidate():
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    routes = get_routes(
        {"lat": 25.0478, "lng": 121.5170},
        {"lat": 25.0422, "lng": 121.5081},
        api_key="test-key",
        http_post=fake_post,
    )

    assert routes[0].distance_m == 1200
    assert routes[0].duration_sec == 900
    assert routes[0].points[0] == (38.5, -120.2)
    assert calls[0][0].endswith("computeRoutes")
    assert calls[0][1]["headers"]["X-Goog-FieldMask"] == (
        "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
    )
    assert calls[0][1]["json"]["travelMode"] == "WALK"

