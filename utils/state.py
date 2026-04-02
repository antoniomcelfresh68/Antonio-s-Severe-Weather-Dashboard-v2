# utils/state.py

import streamlit as st
from utils.config import DEFAULT_CITY_KEY, CITY_PRESETS

def init_state() -> None:
    ## Initialize the Streamlit session state with default values, ensures every page load has a consistent starting point.

    if "city_key" not in st.session_state:
        st.session_state.city_key = DEFAULT_CITY_KEY

    if "location_source" not in st.session_state:
        st.session_state.location_source = "preset"
    
    if "lat" not in st.session_state or "lon" not in st.session_state:
        lat, lon = CITY_PRESETS[st.session_state.city_key]
        st.session_state.lat = float(lat)
        st.session_state.lon = float(lon)

def set_location(city_key: str, lat: float, lon: float, source: str = "preset") -> None:
    ## Update the session state with the selected city and its corresponding latitude and longitude.

    st.session_state.city_key = city_key
    st.session_state.lat = float(lat)
    st.session_state.lon = float(lon)
    st.session_state.location_source = source
    
    
