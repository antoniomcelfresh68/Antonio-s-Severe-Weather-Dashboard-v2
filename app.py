# app.py

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import streamlit as st
from utils.config import APP_TITLE
from utils.state import init_state
from utils.spc import (
    get_spc_day1_national_summary_cached,
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
    render_disclaimer_footer,
    render_global_hero,
    render_nav_cards,
    render_spc_day1_summary_glance,
    render_statistics_glance,
    render_temp_dew_glance,
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
    spc_day1_future = executor.submit(get_spc_day1_national_summary_cached)

with top_left:
    temp_f, dew_f, _wind_text, _conditions_text = glance_future.result()
    render_temp_dew_glance(
        st.session_state.city_key,
        temp_f,
        dew_f,
        float(st.session_state.lat),
        float(st.session_state.lon),
    )
    render_statistics_glance(
        current_year,
        tor_future.result(),
        svr_future.result(),
    )
    day1_summary = spc_day1_future.result()
    render_spc_day1_summary_glance(
        day1_summary.get("category", "NONE"),
        day1_summary.get("tornado"),
        day1_summary.get("wind"),
        day1_summary.get("hail"),
    )

with top_center:
    render_global_hero(
        image_path="assets/banner.jpg",
        title=APP_TITLE,
        location=st.session_state.city_key,
        version="v4.0.0",
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
