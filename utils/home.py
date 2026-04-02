from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

from utils.severe_thunderstorm_warning_counter import fetch_svr_warning_count_ytd
from utils.spc_outlooks import (
    get_day1_categorical_image_url,
    get_day2_categorical_image_url,
    get_day3_categorical_image_url,
    get_day4_8_prob_image_url,
)
from utils.tornado_warning_counter import fetch_tor_warning_count_ytd


@st.cache_data(ttl=900)
def tor_count_cached(y):
    try:
        return fetch_tor_warning_count_ytd(year=y)
    except (requests.RequestException, ValueError):
        return "Unavailable"


@st.cache_data(ttl=900)
def svr_count_cached(y):
    try:
        return fetch_svr_warning_count_ytd(year=y)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return "Unavailable"


def _render_spc_image(title: str, image_url: str | None, warning_text: str) -> None:
    st.markdown(f"**{title}**")
    if image_url:
        st.image(image_url, width="stretch")
    else:
        st.warning(warning_text)


def render(get_spc_location_percents):
    st.markdown(" # SPC Convective Outlooks")

    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)

    with ThreadPoolExecutor(max_workers=8) as executor:
        image_futures = {
            "day1": executor.submit(get_day1_categorical_image_url),
            "day2": executor.submit(get_day2_categorical_image_url),
            "day3": executor.submit(get_day3_categorical_image_url),
            "day4": executor.submit(get_day4_8_prob_image_url, 4),
            "day5": executor.submit(get_day4_8_prob_image_url, 5),
            "day6": executor.submit(get_day4_8_prob_image_url, 6),
            "day7": executor.submit(get_day4_8_prob_image_url, 7),
            "location": executor.submit(get_spc_location_percents, lat, lon),
        }

    row1 = st.columns(3, gap="small")
    with row1[0]:
        _render_spc_image(
            "Day 1 Categorical",
            image_futures["day1"].result(),
            "Could not load the latest SPC Day 1 categorical outlook image.",
        )
    with row1[1]:
        _render_spc_image(
            "Day 2 Categorical",
            image_futures["day2"].result(),
            "Could not load the latest SPC Day 2 categorical outlook image.",
        )
    with row1[2]:
        _render_spc_image(
            "Day 3 Categorical",
            image_futures["day3"].result(),
            "Could not load the latest SPC Day 3 categorical outlook image.",
        )

    st.divider()

    row2 = st.columns(4, gap="small")
    with row2[0]:
        _render_spc_image(
            "Day 4 Probability",
            image_futures["day4"].result(),
            "Could not load the SPC Day 4 probability outlook image.",
        )
    with row2[1]:
        _render_spc_image(
            "Day 5 Probability",
            image_futures["day5"].result(),
            "Could not load the SPC Day 5 probability outlook image.",
        )
    with row2[2]:
        _render_spc_image(
            "Day 6 Probability",
            image_futures["day6"].result(),
            "Could not load the SPC Day 6 probability outlook image.",
        )
    with row2[3]:
        _render_spc_image(
            "Day 7 Probability",
            image_futures["day7"].result(),
            "Could not load the SPC Day 7 probability outlook image.",
        )

    st.caption("Images are official SPC products. Day 4-8 is the experimental probabilistic suite; this view shows Day 4-7.")

    nums = image_futures["location"].result()

    def fmt_prob(x):
        return "0%" if x is None else f"{int(x)}%"

    def fmt_hazard(prob, cig):
        if prob is None and not cig:
            return "0%"
        if prob is None:
            return cig
        if cig:
            return f"{int(prob)}% {cig}"
        return f"{int(prob)}%"

    st.markdown(f"# SPC % for {st.session_state.city_key}")

    m1 = st.columns(3)
    m1[0].metric("D1 TOR", fmt_hazard(nums.get("d1_tor"), nums.get("d1_tor_cig")))
    m1[1].metric("D1 WIND", fmt_hazard(nums.get("d1_wind"), nums.get("d1_wind_cig")))
    m1[2].metric("D1 HAIL", fmt_hazard(nums.get("d1_hail"), nums.get("d1_hail_cig")))

    m2 = st.columns(3)
    m2[0].metric("D2 TOR", fmt_hazard(nums.get("d2_tor"), nums.get("d2_tor_cig")))
    m2[1].metric("D2 WIND", fmt_hazard(nums.get("d2_wind"), nums.get("d2_wind_cig")))
    m2[2].metric("D2 HAIL", fmt_hazard(nums.get("d2_hail"), nums.get("d2_hail_cig")))

    m3 = st.columns(3)
    m3[0].metric("D3 PROB", fmt_prob(nums.get("d3_prob")))
    m3[1].empty()
    m3[2].empty()

    st.caption("Day 1-2 hazard values now reflect SPC probability contours plus Conditional Intensity Groups (CIG1-CIG3) when your location is inside those overlays.")
