import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from utils.nws import get_nws_point_properties


AI_PAGE_CONTEXT_KEY = "ai_page_context"
AI_CURRENT_PAGE_KEY = "ai_current_page"

BASE_SYSTEM_PROMPT = (
    "You are the AI assistant for Antonio's Severe Weather Dashboard. "
    "Answer using the structured dashboard context provided in a separate system message whenever it is available. "
    "Do not guess about the user's current page, location, hazards, radar, model settings, or observations. "
    "If dashboard context is missing for part of a question, say what is unavailable and answer only from the confirmed context."
)


def init_ai_context_state() -> None:
    """Ensure the shared AI context containers exist in Streamlit session state."""
    st.session_state.setdefault(AI_PAGE_CONTEXT_KEY, {})
    st.session_state.setdefault(AI_CURRENT_PAGE_KEY, "Home")


def set_current_ai_page(page_name: str) -> None:
    """Track the currently visible dashboard page for the assistant."""
    init_ai_context_state()
    st.session_state[AI_CURRENT_PAGE_KEY] = page_name


def update_page_ai_context(page_name: str, **context: Any) -> None:
    """
    Merge lightweight page-specific values into shared AI context.
    Pages can call this independently without affecting other pages.
    """
    init_ai_context_state()
    page_context = dict(st.session_state[AI_PAGE_CONTEXT_KEY].get(page_name, {}))
    page_context.update({key: value for key, value in context.items()})
    st.session_state[AI_PAGE_CONTEXT_KEY][page_name] = page_context


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _timezone_name_for_location(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "UTC"

    try:
        tz_name = get_nws_point_properties(lat, lon).get("timeZone")
        if isinstance(tz_name, str) and tz_name:
            return tz_name
    except Exception:
        pass
    return "UTC"


def _iso_now_strings(lat: float | None, lon: float | None) -> dict[str, str]:
    tz_name = _timezone_name_for_location(lat, lon)
    now_utc = datetime.now(timezone.utc)

    try:
        local_zone = ZoneInfo(tz_name)
    except Exception:
        local_zone = timezone.utc
        tz_name = "UTC"

    now_local = now_utc.astimezone(local_zone)
    return {
        "timezone": tz_name,
        "local_time": now_local.isoformat(),
        "utc_time": now_utc.isoformat(),
    }


def _get_page_context(page_name: str) -> dict[str, Any]:
    page_contexts = st.session_state.get(AI_PAGE_CONTEXT_KEY, {})
    raw_context = page_contexts.get(page_name, {})
    return raw_context if isinstance(raw_context, dict) else {}


def _get_best_context_value(current_page: str, field_name: str) -> Any:
    page_contexts = st.session_state.get(AI_PAGE_CONTEXT_KEY, {})
    ordered_pages = [current_page, "Home", "Observations", "Forecast"]

    for page_name in ordered_pages:
        raw_context = page_contexts.get(page_name, {})
        if isinstance(raw_context, dict) and raw_context.get(field_name) is not None:
            return raw_context.get(field_name)

    for raw_context in page_contexts.values():
        if isinstance(raw_context, dict) and raw_context.get(field_name) is not None:
            return raw_context.get(field_name)
    return None


def _global_model_context() -> dict[str, Any]:
    # These are intentionally optional so future pages can set them without
    # requiring any assistant changes.
    return {
        "selected_model": st.session_state.get("selected_model_name"),
        "selected_model_run": st.session_state.get("selected_model_run"),
        "selected_forecast_hour": st.session_state.get("selected_forecast_hour"),
    }


def build_ai_context() -> str:
    """
    Build compact, structured dashboard context for the assistant.
    The returned JSON is safe to inject as an extra system message.
    """
    init_ai_context_state()

    current_page = str(st.session_state.get(AI_CURRENT_PAGE_KEY, "Home"))
    location_name = st.session_state.get("city_key") or "Unknown location"
    lat = _safe_float(st.session_state.get("lat"))
    lon = _safe_float(st.session_state.get("lon"))
    time_context = _iso_now_strings(lat, lon)
    current_page_context = _get_page_context(current_page)

    context = {
        "dashboard": "Antonio's Severe Weather Dashboard",
        "current_page": current_page,
        "location": {
            "name": location_name,
            "latitude": lat,
            "longitude": lon,
        },
        "time": {
            "timezone": time_context["timezone"],
            "local_time": time_context["local_time"],
            "utc_time": time_context["utc_time"],
        },
        "spc_summary": _get_best_context_value(current_page, "spc_summary"),
        "local_hazard_percentages": _get_best_context_value(current_page, "local_hazard_percentages"),
        "latest_observation": _get_best_context_value(current_page, "latest_observation"),
        "radar_station": _get_best_context_value(current_page, "radar_station"),
        "selected_mesoanalysis_parameter": _get_best_context_value(current_page, "selected_mesoanalysis_parameter"),
        "selected_model_context": {
            "model": _get_best_context_value(current_page, "selected_model") or _global_model_context()["selected_model"],
            "run": _get_best_context_value(current_page, "selected_model_run") or _global_model_context()["selected_model_run"],
            "forecast_hour": _get_best_context_value(current_page, "selected_forecast_hour") or _global_model_context()["selected_forecast_hour"],
        },
        "page_specific_context": current_page_context.get("notes"),
    }
    return json.dumps(context, indent=2, ensure_ascii=True)


def build_context_system_message() -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            "Current dashboard context from Streamlit session state. "
            "Treat this as authoritative page state for the active user view.\n\n"
            f"{build_ai_context()}"
        ),
    }
