# utils/ui.py

import base64
import html
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Optional
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

from utils.nws import get_nws_point_properties

def apply_global_ui() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Montserrat:wght@600;700;800&display=swap');
        :root {
            --font-body: 'Inter', sans-serif;
            --font-display: 'Montserrat', sans-serif;
            --glance-text-muted: rgba(255, 238, 228, 0.74);
            --glance-text-strong: rgba(255, 245, 240, 0.94);
            --glance-number: #ff8f5a;
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: var(--font-body);
            font-weight: 400;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        p, li, label, div[data-testid="stMarkdownContainer"] {
            font-family: var(--font-body);
            font-weight: 400;
        }

        /* Hero title: strong, clean, authoritative */
        h1,
        div[data-testid="stHeadingWithActionElements"] h1 {
            font-family: var(--font-body);
            font-weight: 800;
            font-size: clamp(2.05rem, 1.6rem + 1.65vw, 3.0rem);
            line-height: 1.16;
            letter-spacing: 0.2px;
            margin-top: 2.2rem;
            margin-bottom: 1.05rem;
        }

        /* Section headers */
        h2, h3,
        div[data-testid="stHeadingWithActionElements"] h2,
        div[data-testid="stHeadingWithActionElements"] h3,
        .section-header {
            font-family: var(--font-display);
            font-weight: 700;
            letter-spacing: 0.7px;
            line-height: 1.25;
            margin-top: 2.05rem;
            margin-bottom: 0.8rem;
        }

        h2, div[data-testid="stHeadingWithActionElements"] h2 {
            font-size: clamp(1.38rem, 1.2rem + 0.72vw, 2rem);
        }

        h3, div[data-testid="stHeadingWithActionElements"] h3 {
            font-size: clamp(1.12rem, 1.02rem + 0.46vw, 1.48rem);
        }

        /* Navigation card selector */
        div[data-testid="stHorizontalBlock"]:has(.nav-card-anchor) {
            gap: 0.7rem;
            align-items: stretch;
            margin: 0.55rem 0 1.6rem;
        }

        div[data-testid="column"]:has(.nav-card-anchor) {
            display: flex;
            align-self: stretch;
        }

        div[data-testid="column"]:has(.nav-card-anchor) > div[data-testid="stVerticalBlock"] {
            width: 100%;
        }

        .nav-card-anchor {
            display: none;
        }

        div.stButton > button:has(+ .nav-card-anchor) {
            width: 100%;
            min-height: 112px;
            padding: 1rem 1.05rem;
            border-radius: 22px;
            border: 1px solid rgba(255, 170, 132, 0.2) !important;
            background:
                radial-gradient(circle at 18% 18%, rgba(255, 167, 99, 0.24), transparent 34%),
                radial-gradient(circle at 85% 100%, rgba(173, 32, 36, 0.26), transparent 42%),
                linear-gradient(155deg, rgba(20, 24, 32, 0.98), rgba(60, 13, 18, 0.96)) !important;
            background-color: rgba(31, 18, 24, 0.96) !important;
            color: rgba(255, 246, 241, 0.92) !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.06),
                inset 0 -1px 0 rgba(255, 120, 76, 0.08),
                0 14px 24px rgba(0, 0, 0, 0.22),
                0 0 0 1px rgba(255, 109, 58, 0.04) !important;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, color 0.18s ease;
        }

        div.stButton > button:has(+ .nav-card-anchor):hover {
            transform: translateY(-2px);
            border-color: rgba(255, 166, 111, 0.5) !important;
            background:
                radial-gradient(circle at 18% 18%, rgba(255, 184, 111, 0.3), transparent 34%),
                radial-gradient(circle at 85% 100%, rgba(202, 41, 44, 0.3), transparent 42%),
                linear-gradient(155deg, rgba(24, 28, 37, 1), rgba(75, 16, 22, 0.98)) !important;
            background-color: rgba(43, 20, 27, 0.98) !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.09),
                inset 0 -1px 0 rgba(255, 146, 94, 0.12),
                0 18px 32px rgba(0, 0, 0, 0.3),
                0 0 28px rgba(179, 36, 35, 0.14) !important;
        }

        div.stButton > button:has(+ .nav-card-anchor):focus:not(:active) {
            border-color: rgba(255, 169, 132, 0.6) !important;
            box-shadow:
                0 0 0 0.18rem rgba(255, 119, 56, 0.18),
                0 18px 32px rgba(0, 0, 0, 0.28) !important;
        }

        div.stButton > button:has(+ .nav-card-anchor) p {
            font-family: var(--font-display);
            font-size: 1.02rem;
            font-weight: 700;
            line-height: 1.2;
            letter-spacing: 0.35px;
            color: inherit !important;
        }

        div.stButton > button:has(+ .nav-card-anchor)[kind="primary"] {
            border: 1px solid rgba(255, 188, 136, 0.9) !important;
            background:
                radial-gradient(circle at 18% 18%, rgba(255, 198, 118, 0.55), transparent 34%),
                radial-gradient(circle at 86% 100%, rgba(255, 72, 52, 0.34), transparent 44%),
                linear-gradient(160deg, rgba(111, 21, 19, 0.99), rgba(168, 36, 32, 0.97)) !important;
            background-color: rgba(138, 31, 29, 0.98) !important;
            color: #fffaf5 !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 246, 230, 0.2),
                inset 0 -1px 0 rgba(255, 193, 121, 0.22),
                0 22px 38px rgba(84, 7, 10, 0.42),
                0 0 34px rgba(255, 102, 54, 0.24),
                0 0 0 1px rgba(255, 168, 88, 0.14) !important;
        }

        div.stButton > button:has(+ .nav-card-anchor)[kind="primary"]:hover {
            background:
                radial-gradient(circle at 18% 18%, rgba(255, 216, 138, 0.62), transparent 34%),
                radial-gradient(circle at 86% 100%, rgba(255, 87, 64, 0.4), transparent 44%),
                linear-gradient(160deg, rgba(128, 27, 22, 1), rgba(189, 42, 35, 0.98)) !important;
            background-color: rgba(158, 36, 31, 1) !important;
        }

        /* Metric numbers / data */
        div[data-testid="stMetricValue"] {
            font-family: var(--font-body);
            font-weight: 700;
            letter-spacing: 0.2px;
        }

        /* increase spacing between major Streamlit blocks */
        [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
            margin-bottom: 1.0rem;
        }

        [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(h2),
        [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(h3) {
            margin-top: 1.05rem;
        }

        /* gradient background */
        html, body, [data-testid="stAppViewContainer"] {
            height: 100%;
            background: linear-gradient(
    180deg,
    #0B0D12 0%,
    #1A1218 40%,
    #5A0E13 70%,
    #841617 100%
);

        }

        /* make main content area transparent so gradient shows */
        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        .block-container {
            max-width: 1350px;          /* controls fixed page width */
            margin: 0 auto;             /* centers the app */
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
            img {
        max-width: 100% !important;
        height: auto !important;
    }

iframe {
    width: 100% !important;
    max-width: 100% !important;
    border: none !important;
    overflow: hidden !important;
}
.block-container {
    overflow-x: hidden;
}

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {
            display: block;
            background: rgba(7, 13, 22, 0.95);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        div[data-testid="stToolbar"] {
            background: transparent;
        }
        div[data-testid="stDecoration"] {
            background: rgba(7, 13, 22, 0.95);
        }
        [data-testid="stAppViewContainer"] > .main {padding-top: 3.2rem;}
/* ============================= */
/* Tornado Counter Metric Card  */
/* ============================= */

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #111317, #1c1416);
    padding: 10px;
    border-radius: 30px;
    border: 5px solid rgba(255, 100, 0, 0.15);
    box-shadow: 0 0 30px rgba(255, 0, 0, 0.08);
    transition: all 0.4s ease;
}

div[data-testid="stMetric"]:hover {
    border: 1px solid rgba(255, 60, 60, 0.6);
    box-shadow: 0 0 40px rgba(255, 0, 0, 0.18);
}

/* Label styling */
div[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif;
    font-size: 25px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    opacity: 0.75;
    font-weight: 600;
}

/* Big number styling */
div[data-testid="stMetricValue"] {
    font-size: 42px;
    font-weight: 800;
    color: #ff3b3b;
}

/* ========================================== */
/* Top-left temp/dewpoint glance panel        */
/* ========================================== */

.glance-panel-wrap{
  display: flex;
  justify-content: flex-start;
  width: 100%;
  margin: 0;
}

.hero-info-stack{
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.8rem;
  width: 100%;
}

.glance-panel{
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.34rem;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 0.46rem 0.74rem;
  border-radius: 14px;
  background: linear-gradient(130deg, rgba(16, 20, 26, 0.95), rgba(79, 10, 10, 0.88));
  border: 1px solid rgba(255, 112, 67, 0.65);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.28), 0 10px 22px rgba(0, 0, 0, 0.35);
}

.glance-panel.compact{
  gap: 0.28rem;
  padding: 0.38rem 0.64rem;
}

.glance-panel.stats-panel{
  gap: 0.24rem;
  padding: 0.34rem 0.58rem;
}

.glance-panel.stats-panel .glance-loc{
  font-size: 0.74rem;
}

.glance-panel.stats-panel .glance-time{
  font-size: 0.78rem;
}

.glance-panel.stats-panel .glance-val{
  font-size: 0.85rem;
}

.glance-panel.stats-panel .glance-val.severe-storms{
  font-size: 0.78rem;
}

.glance-panel.stats-panel .glance-val.severe-storms .glance-number{
  font-size: 0.94em;
}

.glance-loc{
  font-family: var(--font-body);
  font-size: 0.80rem;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-transform: none;
  color: var(--glance-text-muted);
}

.glance-time{
  font-family: var(--font-body);
  font-size: 0.84rem;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--glance-text-muted);
}

.glance-time.local{
  color: var(--glance-text-muted);
}

.glance-time.zulu{
  color: var(--glance-text-muted);
}

.glance-val{
  font-family: var(--font-body);
  font-size: 0.92rem;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.2px;
  color: var(--glance-text-strong);
  display: block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.glance-label{
  color: var(--glance-text-strong);
}

.glance-number{
  color: var(--glance-number);
}

.glance-time{
  display: block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 900px) {
  .hero-info-stack{
    gap: 0.68rem;
  }
  .glance-panel{
    max-width: none;
  }
}
/* ============================= */
/* Observations detail cards     */
/* ============================= */

.obs-card{
  border-radius: 30px;                 /* match your metric radius */
  padding: 22px 26px;
  background: linear-gradient(145deg, #111317, #1c1416);  /* match stMetric */
  border: 5px solid rgba(255, 100, 0, 0.15);             /* match stMetric */
  box-shadow: 0 0 30px rgba(255, 0, 0, 0.08);            /* match stMetric */
  transition: all 0.4s ease;
  min-height: 140px;
}

.obs-card:hover{
  border: 1px solid rgba(255, 60, 60, 0.6);
  box-shadow: 0 0 40px rgba(255, 0, 0, 0.18);
}

.obs-card-title{
  font-family: 'Montserrat', sans-serif;
  font-size: 22px;
  text-transform: uppercase;
  letter-spacing: 0.9px;
  opacity: .75;
  font-weight: 700;
  margin-bottom: 12px;
}

.obs-card-value{
  font-family: 'Inter', sans-serif;
  font-size: 42px;
  font-weight: 800;
  color: #ff3b3b;     /* match metric number color */
  line-height: 1.1;
}

.obs-card-sub{
  font-family: 'Inter', sans-serif;
  margin-top: 10px;
  opacity: .80;
  font-size: 18px;
  font-weight: 600;
}
/* Small observation cards (top row: Temp/Dew/RH/SLP/Vis) */
.obs-card.small{
  min-height: 90px;
  padding: 18px 22px;
}
.obs-card.small .obs-card-title{
  font-size: 16px;
  margin-bottom: 10px;
}
.obs-card.small .obs-card-value{
  font-size: 34px;
}

@media (max-width: 900px) {
    .block-container {
        padding-left: 1.15rem;
        padding-right: 1.15rem;
        padding-top: 1rem;
    }
    div[data-testid="stHorizontalBlock"]:has(.nav-card-anchor) {
        gap: 0.45rem;
        flex-wrap: wrap;
    }
    div.stButton > button:has(+ .nav-card-anchor) {
        min-height: 88px;
        padding: 0.9rem 0.85rem;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 34px;
    }
    .obs-card-title {
        font-size: 18px;
    }
    .obs-card-value {
        font-size: 34px;
    }
}


        </style>
        """,
        unsafe_allow_html=True,
    )

def obs_card(title: str, value: str, subtitle: Optional[str] = None) -> None:
    html = f"""
<div class="obs-card">
  <div class="obs-card-title">{title}</div>
  <div class="obs-card-value">{value}</div>
  {f'<div class="obs-card-sub">{subtitle}</div>' if subtitle else ''}
</div>
"""
    st.markdown(dedent(html), unsafe_allow_html=True)

def obs_small_card(title: str, value: str) -> None:
    html = f"""
<div class="obs-card small">
  <div class="obs-card-title">{title}</div>
  <div class="obs-card-value">{value}</div>
</div>
    """
    st.markdown(dedent(html), unsafe_allow_html=True)


def _build_glance_panel_html(content_html: str, *, panel_class: str = "", aria_label: str) -> str:
    class_name = "glance-panel"
    if panel_class:
        class_name = f"{class_name} {panel_class}"
    return (
        '<div class="glance-panel-wrap">'
        f'<div class="{class_name}" aria-label="{html.escape(aria_label)}">'
        f"{content_html}"
        "</div></div>"
    )


def render_info_box_stack(boxes_html: list[str]) -> None:
    if not boxes_html:
        return
    stack_html = '<div class="hero-info-stack">' + "".join(boxes_html) + "</div>"
    st.markdown(dedent(stack_html), unsafe_allow_html=True)

def render_nav_cards(options: list[str | tuple[str, str]], key: str = "nav") -> str:
    normalized_options = [
        (option, option) if isinstance(option, str) else option
        for option in options
    ]
    valid_values = [value for _, value in normalized_options]

    if key not in st.session_state or st.session_state[key] not in valid_values:
        st.session_state[key] = valid_values[0]

    def set_nav(option_value: str) -> None:
        st.session_state[key] = option_value

    cols = st.columns(len(normalized_options), gap="small")
    for col, (label, value) in zip(cols, normalized_options):
        with col:
            is_active = st.session_state[key] == value
            st.button(
                label,
                key=f"{key}_{value}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                on_click=set_nav,
                args=(value,),
            )
            st.markdown('<div class="nav-card-anchor"></div>', unsafe_allow_html=True)

    return st.session_state[key]

@st.cache_data(ttl=3600, show_spinner=False)
def _timezone_for_lat_lon(lat: float, lon: float) -> str:
    try:
        tz_name = get_nws_point_properties(lat, lon).get("timeZone")
        if isinstance(tz_name, str) and tz_name:
            return tz_name
    except Exception:
        pass
    return "UTC"

def render_temp_dew_glance(
    location: str,
    temp_f: Optional[float],
    dew_f: Optional[float],
    lat: float,
    lon: float,
) -> None:
    panel_html, local_id, zulu_id, tz_name = build_temp_dew_glance_panel(
        location,
        temp_f,
        dew_f,
        lat,
        lon,
    )
    render_info_box_stack([panel_html])
    mount_glance_clock(local_id, zulu_id, tz_name)


def build_temp_dew_glance_panel(
    location: str,
    temp_f: Optional[float],
    dew_f: Optional[float],
    lat: float,
    lon: float,
) -> tuple[str, str, str, str]:
    def fmt(v: Optional[float]) -> str:
        if v is None:
            return "--"
        return f"{int(round(v))}&deg;F"

    tz_name = _timezone_for_lat_lon(lat, lon)
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = timezone.utc
        tz_name = "UTC"

    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(local_tz)
    local_initial = f"Local Time: {now_local:%H:%M:%S} {now_local:%Z}"
    zulu_initial = f"Zulu Time: {now_utc:%H:%M:%S} UTC"

    local_id = f"glance-local-{uuid.uuid4().hex}"
    zulu_id = f"glance-zulu-{uuid.uuid4().hex}"
    location_safe = html.escape(location)

    content_html = f"""
    <span class="glance-loc">{location_safe}</span>
    <span class="glance-time local" id="{local_id}">{local_initial}</span>
    <span class="glance-time zulu" id="{zulu_id}">{zulu_initial}</span>
    <span class="glance-val"><span class="glance-label">Temp:</span> <span class="glance-number">{fmt(temp_f)}</span></span>
    <span class="glance-val"><span class="glance-label">Dew Point:</span> <span class="glance-number">{fmt(dew_f)}</span></span>
"""
    panel_html = _build_glance_panel_html(
        dedent(content_html),
        aria_label="Current local observations",
    )
    return panel_html, local_id, zulu_id, tz_name


def mount_glance_clock(local_id: str, zulu_id: str, tz_name: str) -> None:
    components.html(
        f"""
<script>
const localId = {json.dumps(local_id)};
const zuluId = {json.dumps(zulu_id)};
const tzName = {json.dumps(tz_name)};

function two(n) {{
  return String(n).padStart(2, '0');
}}

function formatLocal(now) {{
  const parts = new Intl.DateTimeFormat('en-US', {{
    timeZone: tzName,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  }}).formatToParts(now);

  const hour = parts.find(p => p.type === 'hour')?.value ?? '00';
  const minute = parts.find(p => p.type === 'minute')?.value ?? '00';
  const second = parts.find(p => p.type === 'second')?.value ?? '00';
  const zone = parts.find(p => p.type === 'timeZoneName')?.value ?? 'UTC';
  return `Local Time: ${{hour}}:${{minute}}:${{second}} ${{zone}}`;
}}

function formatZulu(now) {{
  return `Zulu Time: ${{two(now.getUTCHours())}}:${{two(now.getUTCMinutes())}}:${{two(now.getUTCSeconds())}} UTC`;
}}

function updateClock() {{
  const localNode = parent.document.getElementById(localId);
  const zuluNode = parent.document.getElementById(zuluId);
  if (!localNode || !zuluNode) {{
    return;
  }}
  const now = new Date();
  localNode.textContent = formatLocal(now);
  zuluNode.textContent = formatZulu(now);
}}

updateClock();
setInterval(updateClock, 1000);
</script>
""",
        height=0,
        width=0,
    )

def render_wind_conditions_glance(wind_text: str, conditions_text: str) -> None:
    render_info_box_stack([build_wind_conditions_glance_panel(wind_text, conditions_text)])


def build_wind_conditions_glance_panel(wind_text: str, conditions_text: str) -> str:
    wind_safe = html.escape((wind_text or "--").strip() or "--")
    cond_safe = html.escape((conditions_text or "--").strip() or "--")
    content_html = f"""
    <span class="glance-val wind">Wind: {wind_safe}</span>
    <span class="glance-val cond">Current Conditions: {cond_safe}</span>
"""
    return _build_glance_panel_html(
        dedent(content_html),
        aria_label="Current wind and conditions",
    )

def render_statistics_glance(year: int, tornado_count: int | str, severe_count: int | str) -> None:
    render_info_box_stack([build_statistics_glance_panel(year, tornado_count, severe_count)])


def build_statistics_glance_panel(year: int, tornado_count: int | str, severe_count: int | str) -> str:
    tor_safe = html.escape(str(tornado_count))
    svr_safe = html.escape(str(severe_count))
    content_html = f"""
    <span class="glance-loc">Statistics</span>
    <span class="glance-time local">YTD {year}</span>
    <span class="glance-val"><span class="glance-label">Tornado Warnings:</span> <span class="glance-number">{tor_safe}</span></span>
    <span class="glance-val severe-storms"><span class="glance-label">Severe Thunderstorms:</span> <span class="glance-number">{svr_safe}</span></span>
"""
    return _build_glance_panel_html(
        dedent(content_html),
        panel_class="stats-panel",
        aria_label="Current yearly warning statistics",
    )


def render_spc_day1_summary_glance(category: str, tornado: int | None, wind: int | None, hail: int | None) -> None:
    render_info_box_stack([build_spc_day1_summary_glance_panel("Today", tornado, wind, hail)])


def build_spc_day1_summary_glance_panel(
    title: str,
    tornado: int | None,
    wind: int | None,
    hail: int | None,
) -> str:
    def fmt_pct(value: int | None) -> str:
        return "None" if value is None else f"{value}%"

    title_safe = html.escape(str(title).strip() or "Location")
    content_html = f"""
    <span class="glance-loc">{title_safe}</span>
    <span class="glance-val"><span class="glance-label">TOR -</span> <span class="glance-number">{fmt_pct(tornado)}</span></span>
    <span class="glance-val"><span class="glance-label">WND -</span> <span class="glance-number">{fmt_pct(wind)}</span></span>
    <span class="glance-val"><span class="glance-label">HAIL -</span> <span class="glance-number">{fmt_pct(hail)}</span></span>
"""
    return _build_glance_panel_html(
        dedent(content_html),
        panel_class="compact",
        aria_label="Location-based SPC day 1 summary",
    )

def render_disclaimer_footer() -> None:
    st.markdown("---")
    st.caption(
        "Disclaimer: This dashboard is a personal, experimental project and should not be used for official decision-making."
    )


@st.cache_data(show_spinner=False)
def _load_base64_asset(path: str, modified_ns: int) -> str:
    # Cache local asset encoding so large hero images are not re-read on every rerun.
    del modified_ns
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _load_base64_asset_if_exists(path: Optional[str]) -> Optional[str]:
    if not path:
        return None

    asset_path = Path(path)
    if not asset_path.exists():
        return None

    return _load_base64_asset(str(asset_path), asset_path.stat().st_mtime_ns)

def render_global_hero(
    image_path: str,
    title: str,
    location: str,
    version: str,
    logo_path: Optional[str] = None,
) -> None:
    encoded = _load_base64_asset(image_path, Path(image_path).stat().st_mtime_ns)

    logo_html = ""
    logo_encoded = _load_base64_asset_if_exists(logo_path)
    if logo_encoded:
        logo_html = (
            f'<img class="hero-logo" src="data:image/png;base64,{logo_encoded}" '
            f'alt="{title} logo" />'
        )

    st.markdown(
        f"""
        <style>
        /* Paint the hero image behind upper page content, then fade it out */
        .block-container {{
            position: relative;
            isolation: isolate;
        }}

        .block-container::before {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            height: 1050px;
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-position: center top;
            background-size: cover;
            background-repeat: no-repeat;
            opacity: 0.42;
            pointer-events: none;
            z-index: 0;
            -webkit-mask-image: linear-gradient(
                to bottom,
                rgba(0,0,0,0.95) 0%,
                rgba(0,0,0,0.75) 45%,
                rgba(0,0,0,0.28) 78%,
                rgba(0,0,0,0) 100%
            );
            mask-image: linear-gradient(
                to bottom,
                rgba(0,0,0,0.95) 0%,
                rgba(0,0,0,0.75) 45%,
                rgba(0,0,0,0.28) 78%,
                rgba(0,0,0,0) 100%
            );
        }}

        .block-container > * {{
            position: relative;
            z-index: 1;
        }}

        .hero-wrap {{
            position: relative;
            width: 100%;
            height: 320px;
            overflow: visible;
            background: transparent;
        }}

        .hero-text {{
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 0 1.5rem;
            z-index: 5;
            color: rgba(255,255,255,0.95);
        }}

        .hero-logo {{
            display: block;
            margin: 0 auto 0.85rem auto;
            width: min(380px, 41vw) !important;
            max-width: none !important;
            height: auto;
            filter: drop-shadow(0 10px 30px rgba(0,0,0,0.45));
        }}

        .hero-text .loc {{
            margin-top: 0.7rem;
            font-size: 1.0rem;
            opacity: 0.92;
        }}

        .hero-text .links {{
            margin-top: 0.35rem;
            font-size: 0.88rem;
            opacity: 0.85;
        }}

        .hero-text .links a {{
            color: rgba(255,255,255,0.92);
            text-decoration: underline;
        }}

        .hero-text .links a:hover {{
            color: rgba(255,255,255,1.0);
        }}

        .hero-text .ver {{
            margin-top: 0.25rem;
            font-size: 0.82rem;
            opacity: 0.70;
        }}
        </style>

        <div class="hero-wrap">
          <div class="hero-text">
            <div>
              {logo_html}
              <div class="loc">Current Location: {location}</div>
              <div class="links">
                Developed by Antonio McElfresh |
                GitHub: <a href="https://github.com/antoniomcelfresh68/Antonio-s-Severe-Weather-Dashboard" target="_blank">View on GitHub</a> |
                LinkedIn: <a href="https://www.linkedin.com/in/antonio-mcelfresh-632462309/" target="_blank">View Profile</a>
              </div>
              <div class="ver">{version}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
