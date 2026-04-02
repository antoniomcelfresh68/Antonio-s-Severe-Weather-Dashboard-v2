import requests
import streamlit as st

from utils.nws import get_nws_point_properties
from utils.state import set_location

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}


@st.cache_data(ttl=1800, show_spinner=False)
def nearest_city_label(lat: float, lon: float) -> str:
    """Resolve nearest city/town label via NWS points metadata."""
    try:
        props = get_nws_point_properties(lat, lon)
        rel = (props.get("relativeLocation") or {}).get("properties", {})
        city = rel.get("city")
        state = rel.get("state")
        if city and state:
            return f"{city}, {state}"
    except Exception:
        pass
    return f"{lat:.3f}, {lon:.3f}"


@st.cache_data(ttl=1800, show_spinner=False)
def local_nws_office_url(lat: float, lon: float) -> str | None:
    """Resolve the local NWS office URL from points metadata."""
    try:
        office_code = get_nws_point_properties(lat, lon).get("cwa")
        if isinstance(office_code, str) and office_code:
            return f"https://www.weather.gov/{office_code.lower()}/"
    except Exception:
        pass
    return None


def _format_geocode_label(result: dict) -> str:
    address = result.get("address") or {}
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("hamlet")
        or address.get("municipality")
        or address.get("county")
    )
    state = address.get("state")
    if city and state:
        return f"{city}, {state}"

    display_name = str(result.get("display_name") or "").strip()
    if not display_name:
        return "Custom Location"

    parts = [part.strip() for part in display_name.split(",") if part.strip()]
    if len(parts) >= 2:
        return f"{parts[0]}, {parts[1]}"
    return parts[0]


@st.cache_data(ttl=1800, show_spinner=False)
def geocode_location_query(query: str) -> tuple[str, float, float] | None:
    """Resolve a city or street address to a label and coordinates."""
    clean_query = query.strip()
    if not clean_query:
        return None

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": clean_query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        results = response.json() or []
        if not results:
            return None

        best = results[0]
        label = _format_geocode_label(best)
        return label, float(best["lat"]), float(best["lon"])
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def geocode_location_suggestions(query: str, limit: int = 5) -> list[tuple[str, float, float]]:
    """Return multiple candidate matches for autosuggest."""
    clean_query = query.strip()
    if len(clean_query) < 3:
        return []

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": clean_query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        results = response.json() or []
        suggestions: list[tuple[str, float, float]] = []
        seen: set[tuple[str, float, float]] = set()

        for result in results:
            label = _format_geocode_label(result)
            item = (label, float(result["lat"]), float(result["lon"]))
            if item in seen:
                continue
            seen.add(item)
            suggestions.append(item)

        return suggestions
    except Exception:
        return []

def sync_location_from_widget_state() -> None:
    """
    Retained for compatibility with the app entrypoint; location is now driven
    by search or device geolocation actions.
    """
    return


def render_location_controls() -> None:
    """Render shared location controls: preset list + device geolocation."""
    st.markdown("### Location")

    pending_search_value = st.session_state.pop("location_search_query_pending", None)
    if pending_search_value is not None:
        st.session_state["location_search_query"] = pending_search_value

    st.markdown(
        """
        <style>
        button[data-testid="stBaseButton-primary"] {
            border: 2px solid #ff2b2b !important;
            box-shadow: 0 0 7px rgba(255, 43, 43, 0.72), 0 0 18px rgba(255, 20, 20, 0.48) !important;
        }
        button[data-testid="stBaseButton-primary"]:hover {
            border-color: #ff4a4a !important;
            box-shadow: 0 0 10px rgba(255, 74, 74, 0.82), 0 0 22px rgba(255, 35, 35, 0.54) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    controls_col, _right_spacer = st.columns([2.1, 1.9], gap="small")

    with controls_col:
        search_col, device_col = st.columns([1.7, 0.55], gap="small")
        with search_col:
            search_query = st.text_input(
                "Search city or address",
                key="location_search_query",
                placeholder="Norman, OK or 120 David L Boren Blvd, Norman, OK",
            )
        with device_col:
            st.markdown("<div style='height: 1.78rem;'></div>", unsafe_allow_html=True)
            use_device = st.button(
                "Use location Device",
                use_container_width=True,
                key="location_device_btn",
                type="primary",
            )

        search_btn_col, _spacer = st.columns([0.55, 1.7], gap="small")
        with search_btn_col:
            use_search = st.button(
                "Search",
                key="location_search_btn",
                use_container_width=True,
            )

        suggestions = geocode_location_suggestions(search_query)
        hide_suggestions = search_query.strip() == str(st.session_state.city_key).strip()
        if search_query.strip() and suggestions and not hide_suggestions:
            st.caption("Suggestions")
            for index, (label, lat, lon) in enumerate(suggestions):
                if st.button(
                    label,
                    key=f"location_suggestion_{index}_{label}_{lat:.4f}_{lon:.4f}",
                    use_container_width=True,
                ):
                    set_location(label, lat, lon, source="search")
                    st.session_state["location_search_query_pending"] = label
                    st.rerun()

        office_url = local_nws_office_url(
            float(st.session_state.lat),
            float(st.session_state.lon),
        )
        if office_url:
            location_label = str(st.session_state.city_key).split(",")[0].strip()
            st.markdown(
                f"[Your Local NWS Office ({location_label})]({office_url})",
                unsafe_allow_html=False,
            )

    if use_device:
        st.session_state.device_loc_nonce = st.session_state.get("device_loc_nonce", 0) + 1
        st.session_state.device_loc_pending = True

    if use_search:
        result = geocode_location_query(search_query)
        if result is None:
            st.warning("Location search did not find a match. Try a more specific city or street address.")
        else:
            label, new_lat, new_lon = result
            set_location(label, new_lat, new_lon, source="search")
            st.rerun()

    if st.session_state.get("device_loc_pending", False):
        try:
            from streamlit_js_eval import get_geolocation
        except Exception as exc:
            st.error("Device geolocation dependency is unavailable.")
            st.exception(exc)
            st.session_state.device_loc_pending = False
            return

        nonce = st.session_state.get("device_loc_nonce", 0)
        geo = get_geolocation(component_key=f"device_geolocation_{nonce}")
        if isinstance(geo, dict) and isinstance(geo.get("coords"), dict):
            coords = geo["coords"]
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            if lat is not None and lon is not None:
                new_lat = float(lat)
                new_lon = float(lon)
                label = nearest_city_label(new_lat, new_lon)
                set_location(label, new_lat, new_lon, source="device")
                st.session_state.device_loc_pending = False
                st.rerun()

        st.info("Waiting for device location permission in your browser...")

    st.caption(
        f"Current: {st.session_state.city_key} ({float(st.session_state.lat):.4f}, {float(st.session_state.lon):.4f})"
    )
