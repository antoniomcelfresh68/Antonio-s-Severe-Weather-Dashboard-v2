from concurrent.futures import ThreadPoolExecutor
import html

import requests
import streamlit as st

from utils.severe_thunderstorm_warning_counter import fetch_svr_warning_count_ytd
from utils.spc import get_day1_location_risk_summary
from utils.spc_outlooks import (
    get_day1_3_detail_payload,
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


def _inject_spc_outlook_css() -> None:
    st.markdown(
        """
        <style>
        .spc-outlooks-caption {
            max-width: 900px;
            margin: -0.45rem 0 0.5rem;
            color: rgba(255, 236, 226, 0.74);
            font-size: 0.98rem;
        }

        .spc-section-heading {
            margin: 0.15rem 0 0.2rem;
            font-size: 1.22rem;
            font-weight: 700;
            color: rgba(255, 245, 241, 0.96);
            letter-spacing: 0.02em;
        }

        .spc-section-caption {
            margin: 0 0 0.85rem;
            color: rgba(255, 232, 221, 0.66);
            font-size: 0.92rem;
        }

        .spc-divider {
            margin: 1.1rem 0 0.65rem;
            border-top: 1px solid rgba(255, 176, 132, 0.16);
        }

        div[data-testid="stHorizontalBlock"]:has(.spc-outlook-card-anchor) {
            gap: 0.95rem;
            align-items: stretch;
            margin-bottom: 0.2rem;
        }

        div[data-testid="column"]:has(.spc-outlook-card-anchor) {
            display: flex;
            align-self: stretch;
        }

        div[data-testid="column"]:has(.spc-outlook-card-anchor) > div[data-testid="stVerticalBlock"] {
            width: 100%;
            height: 100%;
        }

        .spc-outlook-card-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.spc-outlook-card-anchor) {
            height: 100%;
            padding: 0.95rem 0.95rem 0.85rem;
            border-radius: 24px;
            border: 1px solid rgba(255, 180, 140, 0.16);
            background:
                radial-gradient(circle at top left, rgba(255, 159, 92, 0.14), transparent 34%),
                linear-gradient(180deg, rgba(18, 22, 31, 0.98), rgba(9, 12, 19, 0.96));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                0 16px 32px rgba(0, 0, 0, 0.22);
        }

        div[data-testid="stVerticalBlock"]:has(.spc-outlook-card-anchor.spc-card-secondary) {
            padding: 0.8rem 0.8rem 0.75rem;
            border-radius: 20px;
            border-color: rgba(170, 193, 214, 0.14);
            background:
                radial-gradient(circle at top left, rgba(110, 147, 183, 0.12), transparent 34%),
                linear-gradient(180deg, rgba(16, 21, 30, 0.95), rgba(9, 12, 18, 0.94));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.03),
                0 12px 24px rgba(0, 0, 0, 0.18);
        }

        .spc-card-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 183, 131, 0.28);
            background: rgba(255, 142, 87, 0.1);
            color: rgba(255, 222, 202, 0.82);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .spc-card-secondary-label {
            border-color: rgba(157, 191, 219, 0.22);
            background: rgba(101, 137, 168, 0.1);
            color: rgba(220, 235, 248, 0.76);
        }

        .spc-card-title {
            margin: 0.6rem 0 0.2rem;
            color: rgba(255, 246, 240, 0.98);
            font-size: 1.12rem;
            font-weight: 700;
            line-height: 1.25;
        }

        .spc-card-title.secondary {
            font-size: 1rem;
        }

        .spc-card-subtitle {
            margin: 0 0 0.8rem;
            color: rgba(255, 231, 220, 0.68);
            font-size: 0.9rem;
            line-height: 1.45;
        }

        div.stButton > button:has(+ .spc-outlook-dialog-anchor) {
            width: 100%;
            min-height: 2.55rem;
            margin-top: 0.25rem;
            border-radius: 14px;
            border: 1px solid rgba(255, 181, 138, 0.18) !important;
            background:
                linear-gradient(180deg, rgba(34, 40, 52, 0.98), rgba(21, 26, 36, 0.96)) !important;
            color: rgba(255, 241, 234, 0.88) !important;
            font-size: 0.88rem;
            font-weight: 600;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        div.stButton > button:has(+ .spc-outlook-dialog-anchor):hover {
            border-color: rgba(255, 191, 151, 0.32) !important;
            background:
                linear-gradient(180deg, rgba(42, 49, 62, 1), rgba(25, 31, 42, 0.98)) !important;
        }

        .spc-outlook-dialog-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.spc-outlook-card-anchor) [data-testid="stImage"] img {
            width: 100%;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: rgba(255, 255, 255, 0.02);
        }

        div[data-testid="stVerticalBlock"]:has(.spc-outlook-card-anchor.spc-card-secondary) [data-testid="stImage"] img {
            border-radius: 14px;
        }

        div[data-testid="stVerticalBlock"]:has(.spc-outlook-card-anchor) [data-testid="stAlert"] {
            margin-top: 0.35rem;
            border-radius: 14px;
        }

        .spc-location-risk-box {
            margin-top: 0.58rem;
            padding: 0.8rem 0.88rem 0.76rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 180, 140, 0.1);
            background:
                radial-gradient(circle at top left, rgba(255, 162, 104, 0.06), transparent 32%),
                linear-gradient(180deg, rgba(16, 20, 29, 0.96), rgba(10, 13, 20, 0.94));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.025),
                0 10px 20px rgba(0, 0, 0, 0.14);
        }

        .spc-location-risk-title {
            margin: 0 0 0.2rem;
            font-size: 0.94rem;
            font-weight: 700;
            line-height: 1.25;
            color: rgba(255, 244, 238, 0.95);
        }

        .spc-location-risk-subtitle {
            margin: 0 0 0.55rem;
            font-size: 0.8rem;
            color: rgba(255, 232, 221, 0.58);
            line-height: 1.35;
        }

        .spc-location-risk-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.42rem;
        }

        .spc-location-risk-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 179, 130, 0.15);
            background: rgba(255, 158, 96, 0.08);
            color: rgba(255, 241, 234, 0.84);
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }

        .spc-location-risk-message {
            margin: 0;
            font-size: 0.82rem;
            color: rgba(255, 236, 226, 0.72);
            line-height: 1.4;
        }

        div[data-testid="stHorizontalBlock"]:has(.spc-metric-card-anchor) {
            gap: 0.7rem;
            align-items: stretch;
            margin-bottom: 0.12rem;
        }

        div[data-testid="column"]:has(.spc-metric-card-anchor) {
            display: flex;
            align-self: stretch;
        }

        div[data-testid="column"]:has(.spc-metric-card-anchor) > div[data-testid="stVerticalBlock"] {
            width: 100%;
            height: 100%;
        }

        .spc-metric-card-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.spc-metric-card-anchor) {
            height: 100%;
            min-height: 104px;
            padding: 0.72rem 0.82rem 0.7rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(20, 25, 35, 0.95), rgba(13, 17, 25, 0.94));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.02),
                0 8px 16px rgba(0, 0, 0, 0.12);
        }

        .spc-metric-label {
            margin: 0 0 0.42rem;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255, 227, 214, 0.56);
        }

        .spc-metric-value {
            display: flex;
            align-items: baseline;
            gap: 0.38rem;
            flex-wrap: wrap;
            margin: 0;
            line-height: 1.05;
        }

        .spc-metric-value-main {
            font-size: 1.58rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: rgba(255, 244, 239, 0.96);
        }

        .spc-metric-value-cig {
            display: inline-flex;
            align-items: center;
            padding: 0.18rem 0.42rem;
            border-radius: 999px;
            background: rgba(255, 161, 103, 0.08);
            border: 1px solid rgba(255, 179, 130, 0.15);
            color: rgba(255, 223, 204, 0.72);
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .spc-location-footnote {
            margin-top: 0.35rem;
            font-size: 0.82rem;
            line-height: 1.45;
            color: rgba(255, 231, 220, 0.58);
        }

        .spc-dialog-caption {
            margin: -0.2rem 0 0.85rem;
            font-size: 0.92rem;
            line-height: 1.45;
            color: rgba(255, 232, 221, 0.7);
        }

        .spc-dialog-section {
            margin: 0.2rem 0 0.5rem;
            font-size: 1rem;
            font-weight: 700;
            color: rgba(255, 244, 238, 0.94);
        }

        .spc-dialog-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0 0 0.8rem;
        }

        .spc-dialog-meta-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.56rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 179, 132, 0.16);
            background: rgba(255, 154, 93, 0.08);
            color: rgba(255, 230, 218, 0.74);
            font-size: 0.76rem;
            font-weight: 600;
        }

        .spc-dialog-map-frame {
            padding: 0.8rem;
            border-radius: 22px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(20, 25, 35, 0.96), rgba(12, 15, 23, 0.95));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.03),
                0 10px 20px rgba(0, 0, 0, 0.14);
            margin-bottom: 0.25rem;
        }

        .spc-dialog-map-label {
            margin: 0 0 0.55rem;
            font-size: 0.92rem;
            font-weight: 700;
            color: rgba(255, 242, 237, 0.92);
        }

        .spc-dialog-note {
            margin: 0.2rem 0 0.8rem;
            font-size: 0.84rem;
            line-height: 1.45;
            color: rgba(255, 229, 217, 0.6);
        }

        .spc-dialog-summary {
            padding: 0.85rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 176, 128, 0.12);
            background:
                linear-gradient(180deg, rgba(18, 23, 32, 0.95), rgba(11, 14, 21, 0.94));
            margin-bottom: 0.2rem;
        }

        .spc-dialog-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.6rem;
            margin-top: 0.65rem;
        }

        .spc-dialog-summary-label {
            margin: 0 0 0.16rem;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255, 226, 212, 0.54);
        }

        .spc-dialog-summary-value {
            font-size: 1rem;
            font-weight: 700;
            color: rgba(255, 244, 238, 0.92);
        }

        .spc-discussion-box {
            padding: 0.9rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background:
                linear-gradient(180deg, rgba(16, 20, 29, 0.95), rgba(10, 13, 19, 0.94));
            color: rgba(255, 240, 233, 0.86);
            font-size: 0.88rem;
            line-height: 1.55;
            white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_spc_image(image_url: str | None, warning_text: str) -> None:
    if image_url:
        st.image(image_url, width="stretch")
    else:
        st.warning(warning_text)


def _render_outlook_card(
    *,
    title: str,
    subtitle: str,
    image_url: str | None,
    warning_text: str,
    secondary: bool = False,
    detail_day: int | None = None,
) -> None:
    anchor_class = "spc-outlook-card-anchor spc-card-secondary" if secondary else "spc-outlook-card-anchor"
    label_class = "spc-card-kicker spc-card-secondary-label" if secondary else "spc-card-kicker"
    title_class = "spc-card-title secondary" if secondary else "spc-card-title"
    kicker = "Extended Range" if secondary else "Primary Outlook"

    st.markdown(f'<div class="{anchor_class}"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{label_class}">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{title_class}">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="spc-card-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    _render_spc_image(image_url, warning_text)
    if detail_day is not None:
        if st.button(f"Open Day {detail_day} Details", key=f"spc-open-detail-{detail_day}", use_container_width=True):
            st.session_state["spc_open_detail_day"] = detail_day
        st.markdown('<div class="spc-outlook-dialog-anchor"></div>', unsafe_allow_html=True)


def _render_outlook_group(
    *,
    heading: str,
    caption: str,
    columns_count: int,
    cards: list[dict],
    secondary: bool = False,
) -> None:
    st.markdown(f'<div class="spc-section-heading">{heading}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="spc-section-caption">{caption}</div>', unsafe_allow_html=True)

    columns = st.columns(columns_count, gap="medium")
    for column, card in zip(columns, cards):
        with column:
            _render_outlook_card(
                title=card["title"],
                subtitle=card["subtitle"],
                image_url=card["image_url"],
                warning_text=card["warning_text"],
                secondary=secondary,
                detail_day=card.get("detail_day"),
            )


def _split_metric_value(value: str) -> tuple[str, str | None]:
    if " " not in value:
        return value, None
    main, detail = value.split(" ", 1)
    return main, detail


def _render_spc_metric_card(label: str, value: str) -> None:
    value_main, value_detail = _split_metric_value(value)
    st.markdown('<div class="spc-metric-card-anchor"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="spc-metric-label">{label}</div>', unsafe_allow_html=True)

    if value_detail:
        st.markdown(
            (
                '<div class="spc-metric-value">'
                f'<span class="spc-metric-value-main">{value_main}</span>'
                f'<span class="spc-metric-value-cig">{value_detail}</span>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            (
                '<div class="spc-metric-value">'
                f'<span class="spc-metric-value-main">{value_main}</span>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def _render_location_risk_box(city_key: str, nums: dict) -> None:
    risk_summary = get_day1_location_risk_summary(nums)

    st.markdown('<div class="spc-location-risk-box">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="spc-location-risk-title">Risk at {html.escape(city_key)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="spc-location-risk-subtitle">Day 1 qualitative hazard summary for your selected location.</div>',
        unsafe_allow_html=True,
    )

    if risk_summary["hazards"]:
        pills = "".join(
            f'<span class="spc-location-risk-pill">{html.escape(label)}</span>'
            for label in risk_summary["hazards"]
        )
        st.markdown(f'<div class="spc-location-risk-pills">{pills}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="spc-location-risk-message">{html.escape(risk_summary["message"])}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _format_day_location_summary(day: int, nums: dict) -> list[tuple[str, str]]:
    def fmt_prob(value):
        return "0%" if value is None else f"{int(value)}%"

    def fmt_hazard(prob, cig):
        if prob is None and not cig:
            return "0%"
        if prob is None:
            return cig
        if cig:
            return f"{int(prob)}% {cig}"
        return f"{int(prob)}%"

    if day == 1:
        return [
            ("D1 TOR", fmt_hazard(nums.get("d1_tor"), nums.get("d1_tor_cig"))),
            ("D1 WIND", fmt_hazard(nums.get("d1_wind"), nums.get("d1_wind_cig"))),
            ("D1 HAIL", fmt_hazard(nums.get("d1_hail"), nums.get("d1_hail_cig"))),
        ]
    if day == 2:
        return [
            ("D2 TOR", fmt_hazard(nums.get("d2_tor"), nums.get("d2_tor_cig"))),
            ("D2 WIND", fmt_hazard(nums.get("d2_wind"), nums.get("d2_wind_cig"))),
            ("D2 HAIL", fmt_hazard(nums.get("d2_hail"), nums.get("d2_hail_cig"))),
        ]
    return [("D3 PROB", fmt_prob(nums.get("d3_prob")))]


def _render_dialog_meta(payload: dict) -> None:
    meta_bits: list[str] = []
    if payload.get("valid_period"):
        meta_bits.append(f'<span class="spc-dialog-meta-pill">Valid: {html.escape(payload["valid_period"])}</span>')
    if payload.get("updated"):
        meta_bits.append(f'<span class="spc-dialog-meta-pill">Updated: {html.escape(payload["updated"])}</span>')
    if meta_bits:
        st.markdown(f'<div class="spc-dialog-meta">{"".join(meta_bits)}</div>', unsafe_allow_html=True)


def _render_spc_detail_maps(payload: dict) -> None:
    maps = payload.get("maps") or []
    primary_map = next((item for item in maps if item.get("primary")), None)
    hazard_maps = [item for item in maps if not item.get("primary")]

    if primary_map:
        st.markdown('<div class="spc-dialog-section">Main Outlook Map</div>', unsafe_allow_html=True)
        st.markdown('<div class="spc-dialog-map-frame">', unsafe_allow_html=True)
        st.markdown(f'<div class="spc-dialog-map-label">{html.escape(primary_map["label"])}</div>', unsafe_allow_html=True)
        st.image(primary_map["url"], width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="spc-dialog-section">Hazard And Probability Maps</div>', unsafe_allow_html=True)
    if not hazard_maps:
        st.markdown(
            '<div class="spc-dialog-note">Additional hazard maps are not available for this outlook at the moment.</div>',
            unsafe_allow_html=True,
        )
        return

    columns = st.columns(2, gap="medium")
    for index, map_item in enumerate(hazard_maps):
        with columns[index % 2]:
            st.markdown('<div class="spc-dialog-map-frame">', unsafe_allow_html=True)
            st.markdown(f'<div class="spc-dialog-map-label">{html.escape(map_item["label"])}</div>', unsafe_allow_html=True)
            st.image(map_item["url"], width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)


def _render_spc_discussion(payload: dict) -> None:
    st.markdown('<div class="spc-dialog-section">Forecast Discussion</div>', unsafe_allow_html=True)
    discussion = payload.get("discussion")
    if not discussion:
        st.markdown(
            '<div class="spc-dialog-note">Forecast discussion text is not available for this outlook yet, but the modal is structured so it can be added cleanly when present.</div>',
            unsafe_allow_html=True,
        )
        return
    st.markdown(f'<div class="spc-discussion-box">{html.escape(discussion)}</div>', unsafe_allow_html=True)


def _render_spc_detail_location_summary(day: int, city_key: str, nums: dict) -> None:
    summary_items = _format_day_location_summary(day, nums)
    st.markdown('<div class="spc-dialog-section">Location Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="spc-dialog-summary"><div class="spc-dialog-note">Current point-based SPC values for {html.escape(city_key)}.</div><div class="spc-dialog-summary-grid">'
        + "".join(
            (
                '<div>'
                f'<div class="spc-dialog-summary-label">{html.escape(label)}</div>'
                f'<div class="spc-dialog-summary-value">{html.escape(value)}</div>'
                "</div>"
            )
            for label, value in summary_items
        )
        + "</div></div>",
        unsafe_allow_html=True,
    )


def _show_spc_detail_dialog(day: int, city_key: str, nums: dict) -> None:
    dialog_api = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog_api is None:
        return

    try:
        decorator = dialog_api(f"Day {day} Severe Weather Details", width="large")
    except TypeError:
        decorator = dialog_api(f"Day {day} Severe Weather Details")

    @decorator
    def _render_dialog() -> None:
        try:
            payload = get_day1_3_detail_payload(day)
        except requests.RequestException:
            st.warning("Could not load the latest SPC detail products for this outlook.")
            return

        st.markdown(
            '<div class="spc-dialog-caption">Detailed SPC outlook imagery and forecast context for the selected primary outlook day.</div>',
            unsafe_allow_html=True,
        )
        _render_dialog_meta(payload)
        _render_spc_detail_maps(payload)
        st.divider()
        _render_spc_detail_location_summary(day, city_key, nums)
        st.divider()
        _render_spc_discussion(payload)
        st.caption(
            f"Official SPC source: [{payload.get('page_url', 'SPC outlook page')}]({payload.get('page_url', '#')})"
        )

    _render_dialog()


def render(get_spc_location_percents):
    _inject_spc_outlook_css()
    if "spc_open_detail_day" not in st.session_state:
        st.session_state["spc_open_detail_day"] = None

    st.markdown("# SPC Convective Outlooks")
    st.markdown(
        '<div class="spc-outlooks-caption">Latest Storm Prediction Center categorical and probabilistic outlooks, arranged to keep the near-term severe weather signal front and center.</div>',
        unsafe_allow_html=True,
    )

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
            "day8": executor.submit(get_day4_8_prob_image_url, 8),
            "location": executor.submit(get_spc_location_percents, lat, lon),
        }

    nums = image_futures["location"].result()

    primary_cards = [
        {
            "title": "Day 1 Categorical",
            "subtitle": "Current-day severe thunderstorm risk areas and categorical highlights.",
            "image_url": image_futures["day1"].result(),
            "warning_text": "Could not load the latest SPC Day 1 categorical outlook image.",
            "detail_day": 1,
        },
        {
            "title": "Day 2 Categorical",
            "subtitle": "Tomorrow's organized severe potential with updated corridor placement.",
            "image_url": image_futures["day2"].result(),
            "warning_text": "Could not load the latest SPC Day 2 categorical outlook image.",
            "detail_day": 2,
        },
        {
            "title": "Day 3 Categorical",
            "subtitle": "Short-range extended outlook for evolving severe weather setup confidence.",
            "image_url": image_futures["day3"].result(),
            "warning_text": "Could not load the latest SPC Day 3 categorical outlook image.",
            "detail_day": 3,
        },
    ]
    _render_outlook_group(
        heading="Day 1–3 Outlooks",
        caption="Near-term categorical outlooks with the strongest operational signal and highest day-to-day decision value.",
        columns_count=3,
        cards=primary_cards,
    )

    st.markdown('<div class="spc-divider"></div>', unsafe_allow_html=True)

    secondary_cards = [
        {
            "title": "Day 4 Probability",
            "subtitle": "Longer-range probability guidance for emerging severe risk.",
            "image_url": image_futures["day4"].result(),
            "warning_text": "Could not load the SPC Day 4 probability outlook image.",
        },
        {
            "title": "Day 5 Probability",
            "subtitle": "Early look at possible severe corridors and broad pattern support.",
            "image_url": image_futures["day5"].result(),
            "warning_text": "Could not load the SPC Day 5 probability outlook image.",
        },
        {
            "title": "Day 6 Probability",
            "subtitle": "Experimental probabilistic signal as forecast spread begins to widen.",
            "image_url": image_futures["day6"].result(),
            "warning_text": "Could not load the SPC Day 6 probability outlook image.",
        },
        {
            "title": "Day 7 Probability",
            "subtitle": "Farthest-range SPC outlook in this view, best used for trend awareness.",
            "image_url": image_futures["day7"].result(),
            "warning_text": "Could not load the SPC Day 7 probability outlook image.",
        },
        {
            "title": "Day 8 Probability",
            "subtitle": "Final long-range SPC probability panel for broad severe pattern awareness.",
            "image_url": image_futures["day8"].result(),
            "warning_text": "Could not load the SPC Day 8 probability outlook image.",
        },
    ]
    _render_outlook_group(
        heading="Day 4–8 Outlooks",
        caption="Lower-confidence, experimental longer-range probabilistic guidance intended more for pattern recognition than short-fuse decisions.",
        columns_count=5,
        cards=secondary_cards,
        secondary=True,
    )

    selected_day = st.session_state.get("spc_open_detail_day")
    if selected_day in (1, 2, 3):
        _show_spc_detail_dialog(selected_day, st.session_state.city_key, nums)
        st.session_state["spc_open_detail_day"] = None
