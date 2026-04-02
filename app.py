# app.py

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.spc import (
    get_spc_location_percents_cached as get_spc_location_percents,
)
import utils.home as home
from utils.observations import (
    render as render_observations,
    get_location_glance,
)
import utils.about as about
from utils.ui import (
    apply_global_ui,
    build_spc_day1_summary_glance_panel,
    build_statistics_glance_panel,
    build_temp_dew_glance_panel,
    mount_glance_clock,
    render_disclaimer_footer,
    render_global_hero,
    render_info_box_stack,
    render_nav_cards,
)
from utils.location import render_location_controls, sync_location_from_widget_state
from utils.ticker import render_severe_ticker
from utils.gallery import render_gallery
from utils.nws_alerts import get_severe_alerts
from utils.home import svr_count_cached, tor_count_cached
from utils.forecast import render as render_forecast

st.set_page_config(page_title=APP_TITLE, page_icon="assets/tornado-cartoon-animation-clip-art-tornado.jpg", layout="wide", initial_sidebar_state="expanded")

init_state()
apply_global_ui()

if "simulate_outbreak_mode" not in st.session_state:
    st.session_state.simulate_outbreak_mode = False
if "simulate_outbreak_scenario" not in st.session_state:
    st.session_state.simulate_outbreak_scenario = "Static"
if "mock_alert_step" not in st.session_state:
    st.session_state.mock_alert_step = 0

if st.session_state.simulate_outbreak_mode:
    scenario_mode = "dynamic" if st.session_state.simulate_outbreak_scenario == "Dynamic" else "static"
    simulated_alerts = get_severe_alerts(source="mock", mode=scenario_mode)
    render_severe_ticker(alerts=simulated_alerts)
else:
    render_severe_ticker()

sync_location_from_widget_state()

top_left, top_center, top_right = st.columns([1.2, 3.6, 1.2], gap="large")

current_year = datetime.utcnow().year
with ThreadPoolExecutor(max_workers=4) as executor:
    glance_future = executor.submit(
        get_location_glance,
        float(st.session_state.lat),
        float(st.session_state.lon),
    )
    tor_future = executor.submit(tor_count_cached, current_year)
    svr_future = executor.submit(svr_count_cached, current_year)
    spc_location_future = executor.submit(
        get_spc_location_percents,
        float(st.session_state.lat),
        float(st.session_state.lon),
    )

with top_left:
    temp_f, dew_f, _wind_text, _conditions_text = glance_future.result()
    temp_panel_html, local_id, zulu_id, tz_name = build_temp_dew_glance_panel(
        st.session_state.city_key,
        temp_f,
        dew_f,
        float(st.session_state.lat),
        float(st.session_state.lon),
    )
    stats_panel_html = build_statistics_glance_panel(
        current_year,
        tor_future.result(),
        svr_future.result(),
    )
    day1_summary = spc_location_future.result()
    day1_panel_html = build_spc_day1_summary_glance_panel(
        st.session_state.city_key,
        day1_summary.get("d1_tor"),
        day1_summary.get("d1_wind"),
        day1_summary.get("d1_hail"),
    )
    render_info_box_stack([
        temp_panel_html,
        stats_panel_html,
        day1_panel_html,
    ])
    mount_glance_clock(local_id, zulu_id, tz_name)

with top_center:
    render_global_hero(
        image_path="assets/banner.jpg",
        title=APP_TITLE,
        location=st.session_state.city_key,
        version="v4.1.0",
        logo_path="assets/logo.png",
    )

with top_right:
    st.empty()

render_location_controls()

nav = render_nav_cards(
    [
        "Home",
        "Observations",
        (f"Forecast for {st.session_state.city_key}", "Forecast"),
        "Photo Gallery",
        "About",
    ],
    key="nav",
)

if nav == "Home":
    home.render(get_spc_location_percents=get_spc_location_percents)

elif nav == "Observations":
    render_observations()

elif nav == "Forecast":
    render_forecast()

elif nav == "Photo Gallery":
    render_gallery()

elif nav == "About":
    about.render(
    )

render_disclaimer_footer()
