from __future__ import annotations

from typing import Any

import requests
import streamlit as st


HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/geo+json, application/json",
}


@st.cache_data(ttl=1800, show_spinner=False)
def get_nws_point_properties(lat: float, lon: float, timeout: int = 20) -> dict[str, Any]:
    response = requests.get(
        f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}",
        headers=HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    return (response.json() or {}).get("properties") or {}
