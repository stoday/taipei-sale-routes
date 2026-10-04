"""Streamlit demo for comparing Taipei Main Station to Ximen walking routes."""

from pathlib import Path

import folium
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

from coverage import analyze_route_coverage, load_cameras, rank_routes
from geo import haversine_m
from routes import get_routes


TAIPEI_MAIN_STATION = {"lat": 25.0478, "lng": 121.5170}
XIMEN = {"lat": 25.0422, "lng": 121.5081}
DATA_PATH = Path(__file__).parent / "data" / "臺北市CCTV設備.csv"


def _minutes(seconds: float) -> int:
    return round(seconds / 60)


def _route_summary(route) -> str:
    return f"{_minutes(route.duration_sec)} 分鐘 · {route.distance_m / 1000:.2f} km"


def _run_analysis() -> None:
    """Run analysis in a button callback so results survive Streamlit reruns."""
    try:
        cameras = load_cameras(DATA_PATH)
        routes = get_routes(TAIPEI_MAIN_STATION, XIMEN)
        analyzed = rank_routes([analyze_route_coverage(route, cameras) for route in routes])
        st.session_state["analyzed_routes"] = analyzed
        st.session_state["cameras"] = cameras
        st.session_state["analysis_error"] = None
    except FileNotFoundError:
        st.session_state["analyzed_routes"] = []
        st.session_state["analysis_error"] = "找不到 CCTV 資料。"
    except Exception as exc:
        st.session_state["analyzed_routes"] = []
        st.session_state["analysis_error"] = f"無法取得路線，請確認 API key 與網路連線。\n{exc}"


def _route_map(routes, cameras):
    fmap = folium.Map(location=[25.045, 121.513], zoom_start=15, tiles="OpenStreetMap")
    folium.Marker([TAIPEI_MAIN_STATION["lat"], TAIPEI_MAIN_STATION["lng"]], tooltip="台北車站").add_to(fmap)
    folium.Marker([XIMEN["lat"], XIMEN["lng"]], tooltip="西門町").add_to(fmap)
    for index, route in enumerate(routes):
        if route.points:
            folium.PolyLine(
                route.points,
                color="#16803c" if index == 0 else "#777777",
                weight=6 if index == 0 else 4,
                opacity=0.9,
                tooltip=("推薦路線" if index == 0 else f"候選路線 {index + 1}"),
            ).add_to(fmap)
    route_points = [point for route in routes for point in route.points]
    nearby_cameras = []
    if route_points:
        for camera in cameras:
            if min(haversine_m(camera.lat, camera.lng, *point) for point in route_points) <= 100:
                nearby_cameras.append(camera)
    for camera in nearby_cameras:
        folium.CircleMarker(
            [camera.lat, camera.lng],
            radius=4,
            color="#8b5cf6",
            fill=True,
            fill_opacity=0.85,
            tooltip=f"CCTV {camera.camera_id} · 估計半徑 50m",
        ).add_to(fmap)
        folium.Circle(
            [camera.lat, camera.lng],
            radius=50,
            color="#8b5cf6",
            weight=1,
            fill=True,
            fill_opacity=0.04,
        ).add_to(fmap)
    return fmap


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Taipei Safe Route", page_icon="🛡", layout="wide")
    st.session_state.setdefault("analyzed_routes", None)
    st.session_state.setdefault("cameras", [])
    st.session_state.setdefault("analysis_error", None)
    st.title("Taipei Safe Route")
    st.write("台北車站 → 西門町")
    st.caption("以公開 CCTV 位置估算沿途監視覆蓋，協助比較步行路線。")

    analyzed = st.session_state["analyzed_routes"]
    cameras = st.session_state["cameras"]
    left, right = st.columns([0.42, 0.58], gap="medium")

    with left:
        with st.container(border=True):
            st.subheader("路線分析")
            st.button("分析路線", type="primary", on_click=_run_analysis, width="stretch")

            if st.session_state["analysis_error"]:
                st.error(st.session_state["analysis_error"])

            if analyzed is not None and not analyzed:
                st.info("目前沒有可比較的路線。")

            if analyzed:
                recommended = analyzed[0]
                st.success("推薦：攝影機覆蓋率最高的路線")
                metric_left, metric_right = st.columns(2)
                metric_left.metric("估計覆蓋率", f"{recommended.coverage_ratio:.0%}", border=True)
                metric_right.metric("步行時間", f"{_minutes(recommended.duration_sec)} 分鐘", border=True)
                st.metric("路線距離", f"{recommended.distance_m / 1000:.2f} km", border=True)
                st.caption(f"覆蓋連續性：最長未覆蓋區段 {recommended.longest_uncovered_gap_m:.0f}m")
                if len(analyzed) > 1:
                    with st.expander("查看其他候選路線"):
                        for route in analyzed[1:]:
                            st.write(f"**{route.route_id}** · {_route_summary(route)} · 覆蓋率 {route.coverage_ratio:.0%}")

            st.caption(
                "紫色標記為公開 CCTV，淡紫色圓圈為 50m 估計覆蓋範圍。結果僅供技術展示。"
            )

    with right:
        st.subheader("路線地圖")
        st.caption("綠線為推薦路線，灰線為其他候選路線；地圖可縮放與拖曳。")
        st_folium(_route_map(analyzed or [], cameras), width=700, height=600, key="route_map")


if __name__ == "__main__":
    main()
