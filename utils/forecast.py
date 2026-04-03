from datetime import datetime
from html import escape
from textwrap import dedent
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import pandas as pd
import requests
import streamlit as st
from utils.ai_context import update_page_ai_context

from utils.nws import get_nws_point_properties

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}


@st.cache_data(ttl=900, show_spinner=False)
def _get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=900, show_spinner=False)
def get_location_forecast(lat: float, lon: float) -> dict[str, list[dict[str, Any]]]:
    props = get_nws_point_properties(lat, lon)

    forecast_url = props.get("forecast")
    hourly_url = props.get("forecastHourly")

    if not forecast_url or not hourly_url:
        raise ValueError("Forecast endpoints were unavailable for this location.")

    forecast = _get_json(forecast_url)
    hourly = _get_json(hourly_url)

    return {
        "daily_periods": ((forecast.get("properties") or {}).get("periods") or []),
        "hourly_periods": ((hourly.get("properties") or {}).get("periods") or []),
    }


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _format_temp(period: dict[str, Any]) -> str:
    temp = period.get("temperature")
    unit = period.get("temperatureUnit") or "F"
    if temp is None:
        return "--"
    return f"{temp}°{unit}"


def _format_wind(period: dict[str, Any]) -> str:
    speed = str(period.get("windSpeed") or "").strip()
    direction = str(period.get("windDirection") or "").strip()
    if speed and direction:
        return f"{direction} {speed}"
    return speed or direction or "Not available"


def _precip_value(period: dict[str, Any]) -> int:
    value = (period.get("probabilityOfPrecipitation") or {}).get("value")
    if value is None:
        return 0
    return int(round(value))


def _temp_value(period: dict[str, Any]) -> int | None:
    value = period.get("temperature")
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except Exception:
        return None


def _condition_emoji(text: str | None, is_daytime: bool = True) -> str:
    forecast = (text or "").lower()
    if "thunder" in forecast:
        return "⛈️"
    if "snow" in forecast or "blizzard" in forecast:
        return "❄️"
    if "sleet" in forecast or "ice" in forecast or "freezing" in forecast:
        return "🧊"
    if "fog" in forecast or "haze" in forecast or "smoke" in forecast:
        return "🌫️"
    if "rain" in forecast or "showers" in forecast or "drizzle" in forecast:
        return "🌧️"
    if "wind" in forecast or "breezy" in forecast:
        return "💨"
    if "cloud" in forecast or "overcast" in forecast:
        return "⛅" if is_daytime else "☁️"
    if "sunny" in forecast or "clear" in forecast:
        return "☀️" if is_daytime else "🌙"
    return "🌤️" if is_daytime else "🌌"


def _wind_bucket(wind_text: str) -> str:
    upper = wind_text.upper()
    if upper.startswith(("N", "NN", "NW", "NE")):
        return "north"
    if upper.startswith(("S", "SS", "SW", "SE")):
        return "south"
    if upper.startswith(("E", "EE")):
        return "east"
    if upper.startswith(("W", "WW")):
        return "west"
    return "unknown"


def _detect_front_signal(current: dict[str, Any], upcoming: dict[str, Any]) -> dict[str, str] | None:
    current_temp = _temp_value(current)
    upcoming_temp = _temp_value(upcoming)
    if current_temp is None or upcoming_temp is None:
        return None

    delta = upcoming_temp - current_temp
    current_text = f"{current.get('shortForecast') or ''} {current.get('detailedForecast') or ''}".lower()
    upcoming_text = f"{upcoming.get('shortForecast') or ''} {upcoming.get('detailedForecast') or ''}".lower()
    combined_text = f"{current_text} {upcoming_text}"

    current_wind = _wind_bucket(_format_wind(current))
    upcoming_wind = _wind_bucket(_format_wind(upcoming))
    northerly_shift = current_wind == "south" and upcoming_wind == "north"
    southerly_shift = current_wind == "north" and upcoming_wind == "south"

    cold_hint = "cold front" in combined_text or "cooler" in upcoming_text or "turning cooler" in upcoming_text
    warm_hint = "warm front" in combined_text or "warmer" in upcoming_text or "warming" in upcoming_text

    if delta <= -12 or cold_hint or (delta <= -8 and northerly_shift):
        return {
            "type": "cold",
            "label": "Possible Cold Front",
            "detail": f"Temperatures drop {abs(delta)}° with a likely cooler push into {upcoming.get('name') or 'the next period'}.",
            "symbols": "▲ ▲ ▲ ▲ ▲",
        }

    if delta >= 12 or warm_hint or (delta >= 8 and southerly_shift):
        return {
            "type": "warm",
            "label": "Possible Warm Front",
            "detail": f"Temperatures rise {delta}° heading into {upcoming.get('name') or 'the next period'}.",
            "symbols": "◗ ◗ ◗ ◗ ◗",
        }

    return None


def _daytime_period_indices(periods: list[dict[str, Any]]) -> list[int]:
    indices: list[int] = []
    for index, period in enumerate(periods):
        if period.get("isDaytime") is True:
            indices.append(index)
    return indices


def _hero_outlook(hourly_periods: list[dict[str, Any]], daily_periods: list[dict[str, Any]]) -> dict[str, str]:
    current = hourly_periods[0] if hourly_periods else {}
    next_period = daily_periods[0] if daily_periods else (hourly_periods[1] if len(hourly_periods) > 1 else {})
    later_period = daily_periods[1] if len(daily_periods) > 1 else {}

    current_temp = _temp_value(current)
    next_temp = _temp_value(next_period)

    trend_label = "Steady pattern ahead"
    trend_note = "Conditions look fairly consistent through the next forecast period."
    trend_emoji = "🌤️"

    if current_temp is not None and next_temp is not None:
        delta = next_temp - current_temp
        if delta >= 10:
            trend_label = "Warm-up on deck"
            trend_note = f"Expect about a {delta}° jump into {next_period.get('name') or 'the next period'}."
            trend_emoji = "📈"
        elif delta <= -10:
            trend_label = "Cool-down incoming"
            trend_note = f"Temperatures fall about {abs(delta)}° by {next_period.get('name') or 'the next period'}."
            trend_emoji = "📉"
        elif _precip_value(next_period) >= 50:
            trend_label = "Wet stretch ahead"
            trend_note = f"Rain chances increase into {next_period.get('name') or 'the next period'}."
            trend_emoji = "🌧️"
        elif "thunder" in f"{next_period.get('shortForecast') or ''} {later_period.get('shortForecast') or ''}".lower():
            trend_label = "Storm signal ahead"
            trend_note = "Thunderstorm wording shows up in the near-term forecast."
            trend_emoji = "⛈️"

    return {
        "trend_label": trend_label,
        "trend_note": trend_note,
        "trend_emoji": trend_emoji,
        "next_name": str(next_period.get("name") or "Next period"),
        "next_temp": _format_temp(next_period) if next_period else "--",
        "next_summary": str(next_period.get("shortForecast") or "Forecast updating"),
        "later_name": str(later_period.get("name") or "Then"),
        "later_summary": str(later_period.get("shortForecast") or "Forecast will update soon."),
    }


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .forecast-shell {
            position: relative;
            overflow: hidden;
            border-radius: 30px;
            padding: 1.6rem 1.6rem 1.3rem 1.6rem;
            background:
                radial-gradient(circle at top left, rgba(255, 156, 89, 0.22), transparent 30%),
                radial-gradient(circle at 85% 20%, rgba(255, 220, 120, 0.16), transparent 25%),
                linear-gradient(140deg, rgba(18, 24, 34, 0.95), rgba(48, 14, 18, 0.94) 58%, rgba(102, 24, 22, 0.95));
            border: 1px solid rgba(255, 180, 116, 0.28);
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.32);
        }

        .forecast-shell::before {
            content: "";
            position: absolute;
            inset: -30% auto auto -10%;
            width: 260px;
            height: 260px;
            border-radius: 999px;
            background: rgba(255, 173, 84, 0.09);
            filter: blur(20px);
        }

        .forecast-kicker {
            font-size: 0.85rem;
            font-weight: 800;
            letter-spacing: 0.18rem;
            text-transform: uppercase;
            color: rgba(255, 223, 190, 0.76);
            margin-bottom: 0.45rem;
        }

        .forecast-headline {
            font-size: clamp(2rem, 1.7rem + 1.7vw, 3.3rem);
            font-weight: 900;
            line-height: 1.04;
            color: #fff8ef;
            margin: 0;
        }

        .forecast-sub {
            margin-top: 0.7rem;
            max-width: 820px;
            font-size: 1rem;
            color: rgba(255, 238, 223, 0.84);
        }

        .forecast-hero-grid {
            display: grid;
            grid-template-columns: 1.55fr 0.95fr;
            gap: 1rem;
            margin-top: 1.3rem;
        }

        .forecast-main-card,
        .forecast-mini-card,
        .forecast-hour-card,
        .forecast-daily-card {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.04));
            border: 1px solid rgba(255, 214, 178, 0.14);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07), 0 16px 38px rgba(0, 0, 0, 0.24);
            backdrop-filter: blur(8px);
        }

        .forecast-main-card {
            border-radius: 26px;
            padding: 1.3rem 1.35rem;
        }

        .forecast-location {
            font-size: 0.9rem;
            font-weight: 700;
            color: rgba(255, 224, 198, 0.74);
            text-transform: uppercase;
            letter-spacing: 0.1rem;
        }

        .forecast-now {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-top: 0.55rem;
        }

        .forecast-emoji {
            font-size: 4rem;
            line-height: 1;
            filter: drop-shadow(0 10px 20px rgba(0, 0, 0, 0.2));
        }

        .forecast-temp {
            font-size: clamp(2.7rem, 2.1rem + 2vw, 4.2rem);
            font-weight: 900;
            color: #fff6ea;
            line-height: 0.95;
        }

        .forecast-condition {
            margin-top: 0.2rem;
            font-size: 1.08rem;
            font-weight: 700;
            color: rgba(255, 236, 218, 0.9);
        }

        .forecast-detail-line {
            margin-top: 0.9rem;
            font-size: 0.98rem;
            color: rgba(255, 229, 205, 0.83);
        }

        .forecast-mini-stack {
            display: grid;
            gap: 0.95rem;
        }

        .forecast-mini-card {
            border-radius: 24px;
            padding: 1rem 1.1rem;
        }

        .forecast-mini-label {
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12rem;
            text-transform: uppercase;
            color: rgba(255, 224, 198, 0.67);
        }

        .forecast-mini-value {
            margin-top: 0.45rem;
            font-size: 1.5rem;
            font-weight: 800;
            color: #fff6ea;
            line-height: 1.2;
        }

        .forecast-mini-note {
            margin-top: 0.35rem;
            font-size: 0.95rem;
            color: rgba(255, 234, 216, 0.78);
        }

        .forecast-section-title {
            margin-top: 1.8rem;
            margin-bottom: 0.85rem;
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: 0.02rem;
            color: #fff3e5;
        }

        .forecast-section-note {
            margin-top: -0.15rem;
            margin-bottom: 1rem;
            color: rgba(255, 228, 204, 0.74);
        }

        .forecast-hour-card {
            border-radius: 24px;
            padding: 1rem 0.95rem;
            text-align: left;
            min-height: 220px;
        }

        .forecast-hour-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.5rem;
        }

        .forecast-hour-time {
            font-size: 0.95rem;
            font-weight: 800;
            color: #fff4e7;
        }

        .forecast-hour-emoji {
            font-size: 1.65rem;
            line-height: 1;
        }

        .forecast-hour-temp {
            margin-top: 0.55rem;
            font-size: 2rem;
            font-weight: 900;
            color: #ffdfbc;
        }

        .forecast-hour-text {
            margin-top: 0.25rem;
            min-height: 2.7rem;
            font-size: 0.95rem;
            font-weight: 700;
            color: rgba(255, 237, 220, 0.88);
        }

        .forecast-hour-meta {
            margin-top: 0.6rem;
            font-size: 0.88rem;
            color: rgba(255, 227, 203, 0.76);
        }

        .forecast-daily-card {
            border-radius: 28px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 0.95rem;
        }

        .forecast-daily-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }

        .forecast-daily-name {
            font-size: 1.12rem;
            font-weight: 800;
            color: #fff5e7;
        }

        .forecast-daily-temp {
            font-size: 1.55rem;
            font-weight: 900;
            color: #ffd8af;
            white-space: nowrap;
        }

        .forecast-daily-summary {
            margin-top: 0.35rem;
            font-size: 1rem;
            font-weight: 700;
            color: rgba(255, 236, 218, 0.9);
        }

        .forecast-daily-meta {
            margin-top: 0.5rem;
            font-size: 0.92rem;
            color: rgba(255, 223, 199, 0.78);
        }

        .forecast-daily-detail {
            margin-top: 0.7rem;
            font-size: 0.96rem;
            color: rgba(255, 230, 210, 0.84);
        }

        .forecast-front-divider {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            border-radius: 999px;
            padding: 0.8rem 1rem;
            margin: 0.15rem 0 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        .forecast-front-divider.cold {
            background: linear-gradient(90deg, rgba(45, 110, 188, 0.26), rgba(16, 26, 41, 0.82));
        }

        .forecast-front-divider.warm {
            background: linear-gradient(90deg, rgba(185, 79, 45, 0.3), rgba(44, 20, 18, 0.82));
        }

        .forecast-front-symbols {
            font-size: 1.15rem;
            letter-spacing: 0.2rem;
            white-space: nowrap;
        }

        .forecast-front-divider.cold .forecast-front-symbols {
            color: #7ec8ff;
        }

        .forecast-front-divider.warm .forecast-front-symbols {
            color: #ffb273;
        }

        .forecast-front-copy {
            min-width: 0;
        }

        .forecast-front-label {
            font-size: 0.86rem;
            font-weight: 800;
            letter-spacing: 0.08rem;
            text-transform: uppercase;
            color: #fff1de;
        }

        .forecast-front-detail {
            margin-top: 0.16rem;
            font-size: 0.92rem;
            color: rgba(255, 232, 212, 0.8);
        }

        @media (max-width: 900px) {
            .forecast-hero-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero(hourly_periods: list[dict[str, Any]], daily_periods: list[dict[str, Any]]) -> None:
    if not hourly_periods:
        st.warning("Hourly forecast data is unavailable right now.")
        return

    current = hourly_periods[0]
    current_short = current.get("shortForecast") or "Forecast unavailable"
    current_detail = current.get("detailedForecast") or current_short
    emoji = _condition_emoji(current_short, bool(current.get("isDaytime", True)))
    outlook = _hero_outlook(hourly_periods, daily_periods)

    hero_html = dedent(
        f"""
        <div class="forecast-shell">
          <div class="forecast-kicker">Free forecast for your selected location</div>
          <h2 class="forecast-headline">Your Forecast</h2>
          <div class="forecast-sub">
            Personalized NOAA weather guidance for <strong>{escape(str(st.session_state.city_key))}</strong>,
            refreshed from the National Weather Service and styled for quick scanning.
          </div>

          <div class="forecast-hero-grid">
            <div class="forecast-main-card">
              <div class="forecast-location">{outlook['trend_emoji']} {escape(outlook['trend_label'])}</div>
              <div class="forecast-now">
                <div class="forecast-emoji">{emoji}</div>
                <div>
                  <div class="forecast-temp">{escape(_format_temp(current))}</div>
                  <div class="forecast-condition">{escape(current_short)}</div>
                </div>
              </div>
              <div class="forecast-detail-line">
                Wind: <strong>{escape(_format_wind(current))}</strong> &nbsp;|&nbsp;
                Rain chance: <strong>{_precip_value(current)}%</strong>
              </div>
              <div class="forecast-detail-line">
                {escape(outlook['trend_note'])}
              </div>
            </div>

            <div class="forecast-mini-stack">
              <div class="forecast-mini-card">
                <div class="forecast-mini-label">{escape(outlook['next_name'])}</div>
                <div class="forecast-mini-value">{escape(outlook['next_temp'])}</div>
                <div class="forecast-mini-note">
                  {escape(outlook['next_summary'])}
                </div>
              </div>
              <div class="forecast-mini-card">
                <div class="forecast-mini-label">{escape(outlook['later_name'])}</div>
                <div class="forecast-mini-value">{escape(outlook['later_summary'])}</div>
                <div class="forecast-mini-note">
                  {escape(current_detail)}
                </div>
              </div>
            </div>
          </div>
        </div>
        """
    )
    st.markdown(hero_html, unsafe_allow_html=True)


def _render_hourly(hourly_periods: list[dict[str, Any]]) -> None:
    st.markdown('<div class="forecast-section-title">Hour By Hour</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="forecast-section-note">Temperature and rain chances for the next 12 hours, plotted for fast trend spotting.</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Location: {st.session_state.city_key}")

    plot_periods = hourly_periods[:12]
    if not plot_periods:
        st.caption("Hourly forecast data is unavailable.")
        return

    rows: list[dict[str, Any]] = []
    for period in plot_periods:
        start = _parse_time(period.get("startTime"))
        label = start.strftime("%-I %p") if start else (period.get("name") or "Hour")
        rows.append(
            {
                "label": label,
                "temperature": period.get("temperature"),
                "precipitation": _precip_value(period),
                "wind": _format_wind(period),
                "forecast": period.get("shortForecast") or "Forecast unavailable",
            }
        )

    df = pd.DataFrame(rows)

    fig, ax_temp = plt.subplots(figsize=(12, 4.6))
    fig.patch.set_facecolor("#11161f")
    ax_temp.set_facecolor("#11161f")

    x_positions = list(range(len(df)))
    ax_precip = ax_temp.twinx()
    ax_precip.bar(
        x_positions,
        df["precipitation"],
        color="#3aa6ff",
        alpha=0.28,
        width=0.65,
        label="Rain Chance (%)",
    )
    temps = df["temperature"].astype(float)
    temp_min = float(temps.min())
    temp_max = float(temps.max())
    if temp_min == temp_max:
        temp_min -= 1
        temp_max += 1
    norm = Normalize(vmin=temp_min, vmax=temp_max)
    cmap = plt.get_cmap("coolwarm")

    points = list(zip(x_positions, temps))
    segments = [[points[i], points[i + 1]] for i in range(len(points) - 1)]
    if segments:
        line_collection = LineCollection(
            segments,
            cmap=cmap,
            norm=norm,
            linewidths=3,
        )
        line_collection.set_array((temps.iloc[:-1].to_numpy() + temps.iloc[1:].to_numpy()) / 2)
        ax_temp.add_collection(line_collection)

    scatter = ax_temp.scatter(
        x_positions,
        temps,
        c=temps,
        cmap=cmap,
        norm=norm,
        s=72,
        edgecolors="#fff4e4",
        linewidths=0.8,
        zorder=3,
        label="Temperature",
    )

    ax_temp.set_xticks(x_positions)
    ax_temp.set_xticklabels(df["label"], color="#f7ead9", fontsize=12, fontweight="bold")
    ax_temp.set_ylabel("Temperature (°F)", color="#ffcf94", fontsize=11, fontweight="bold")
    ax_precip.set_ylabel("Rain Chance (%)", color="#8fd0ff", fontsize=11, fontweight="bold")

    ax_temp.tick_params(axis="y", colors="#ffcf94")
    ax_precip.tick_params(axis="y", colors="#8fd0ff")
    ax_temp.tick_params(axis="x", colors="#f7ead9")

    ax_temp.grid(axis="y", color="white", alpha=0.09, linewidth=1)
    for spine in ax_temp.spines.values():
        spine.set_color("#3c2b2f")
    for spine in ax_precip.spines.values():
        spine.set_color("#3c2b2f")

    ax_temp.set_ylim(bottom=max(min(df["temperature"].fillna(0)) - 8, 0))
    ax_precip.set_ylim(0, max(100, int(df["precipitation"].max()) + 10))

    for index, temp in enumerate(df["temperature"]):
        if pd.notna(temp):
            ax_temp.text(
                index,
                temp - 2.2,
                f"{int(temp)}°",
                color="#fff4e4",
                fontsize=9,
                ha="center",
                va="top",
                fontweight="bold",
            )

    legend_items = ax_temp.get_legend_handles_labels()
    precip_items = ax_precip.get_legend_handles_labels()
    handles = legend_items[0] + precip_items[0]
    labels = legend_items[1] + precip_items[1]
    legend = ax_temp.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.04),
        ncol=2,
        frameon=False,
        fontsize=10,
    )
    for text in legend.get_texts():
        text.set_color("#f7ead9")

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    summary_cols = st.columns(4, gap="small")
    warmest_idx = int(df["temperature"].fillna(-999).idxmax())
    coldest_idx = int(df["temperature"].fillna(999).idxmin())
    wettest_idx = int(df["precipitation"].idxmax())

    summary_cols[0].metric("Warmest Hour", f"{int(df.loc[warmest_idx, 'temperature'])}°F", f"at {df.loc[warmest_idx, 'label']}")
    summary_cols[1].metric("Coldest Hour", f"{int(df.loc[coldest_idx, 'temperature'])}°F", f"at {df.loc[coldest_idx, 'label']}")
    summary_cols[2].metric("Highest Rain Chance", f"{int(df.loc[wettest_idx, 'precipitation'])}%", f"at {df.loc[wettest_idx, 'label']}")
    summary_cols[3].metric("Current Conditions", str(rows[0]["forecast"]))


def _render_daily(daily_periods: list[dict[str, Any]]) -> None:
    st.markdown('<div class="forecast-section-title">The Bigger Picture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="forecast-section-note">Longer-form forecast periods with the details you would normally have to dig around to find.</div>',
        unsafe_allow_html=True,
    )

    periods = daily_periods[:8]
    daytime_indices = _daytime_period_indices(periods)
    front_signals_by_index: dict[int, dict[str, str]] = {}
    for daytime_index, current_index in enumerate(daytime_indices[:-1]):
        next_index = daytime_indices[daytime_index + 1]
        front_signal = _detect_front_signal(periods[current_index], periods[next_index])
        if front_signal:
            front_signals_by_index[current_index] = front_signal

    for index, period in enumerate(periods):
        short = period.get("shortForecast") or "Forecast unavailable"
        emoji = _condition_emoji(short, bool(period.get("isDaytime", True)))
        card_html = dedent(
            f"""
            <div class="forecast-daily-card">
              <div class="forecast-daily-top">
                <div class="forecast-daily-name">{emoji} {escape(period.get("name") or "Forecast")}</div>
                <div class="forecast-daily-temp">{escape(_format_temp(period))}</div>
              </div>
              <div class="forecast-daily-summary">{escape(short)}</div>
              <div class="forecast-daily-meta">
                💨 Wind: {escape(_format_wind(period))} &nbsp;|&nbsp;
                💧 Precipitation chance: {_precip_value(period)}%
              </div>
              <div class="forecast-daily-detail">{escape(period.get("detailedForecast") or short)}</div>
            </div>
            """
        )
        st.markdown(card_html, unsafe_allow_html=True)

        front_signal = front_signals_by_index.get(index)
        if front_signal:
            divider_html = dedent(
                f"""
                <div class="forecast-front-divider {front_signal['type']}">
                  <div class="forecast-front-symbols">{front_signal['symbols']}</div>
                  <div class="forecast-front-copy">
                    <div class="forecast-front-label">{escape(front_signal['label'])}</div>
                    <div class="forecast-front-detail">{escape(front_signal['detail'])}</div>
                  </div>
                </div>
                """
            )
            st.markdown(divider_html, unsafe_allow_html=True)


def render() -> None:
    _render_styles()

    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)

    try:
        forecast = get_location_forecast(lat, lon)
    except Exception:
        st.warning("The location forecast could not be loaded right now. Please try again in a moment.")
        return

    hourly_periods = forecast.get("hourly_periods") or []
    daily_periods = forecast.get("daily_periods") or []

    update_page_ai_context(
        "Forecast",
        notes={
            "hourly_period_count": len(hourly_periods),
            "daily_period_count": len(daily_periods),
            "source": "NOAA / api.weather.gov",
        },
        selected_model=None,
        selected_model_run=None,
        selected_forecast_hour=None,
    )

    _render_hourly(hourly_periods)
    st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
    _render_daily(daily_periods)
