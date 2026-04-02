import streamlit as st


def render() -> None:
    st.subheader("About This Dashboard")

    st.markdown(
        """
## Version

Antonio's Severe Weather Dashboard v4.0.0 is a modular Streamlit application
built for fast, location-aware severe-weather situational awareness across the United States.

## Overview

The dashboard brings together official NOAA/NWS, SPC, and GOES imagery into
a single interface with shared location state, cached API workflows, and an
updated visual design built around quick severe-weather scanning.

---

## Features

- Nationwide severe alert ticker filtered to:
  - Tornado Warning
  - Severe Thunderstorm Warning
  - Tornado Watch
  - Severe Thunderstorm Watch
- Redesigned landing layout with live glance panels for:
  - Temperature and dewpoint
  - Year-to-date tornado and severe thunderstorm warning counts
  - National SPC Day 1 summary with tornado, wind, and hail highlights
- SPC Convective Outlooks page with:
  - Day 1-3 categorical outlook imagery
  - Day 4-7 probabilistic outlook imagery
  - Location-based Day 1-2 tornado, wind, and hail percentages
  - Day 3 probability at the selected location
  - Conditional Intensity Group labels when applicable
- Flexible location tools:
  - City or street-address search
  - Autosuggestions
  - Browser device geolocation
  - Local NWS office quick link
- Observations page with:
  - SPC mesoanalysis viewer
  - Auto-selected nearby radar loops
  - GOES satellite viewer with selectable satellite, sector, and product
- Forecast page with:
  - Styled forecast hero and trend callouts
  - Hourly temperature and precipitation visualization
  - Multi-period NOAA/NWS forecast cards

---

## Technical Architecture

- Built with Streamlit and a modular `utils/` package structure
- Shared NWS points metadata helper for forecasts, radar, observations, and local-office resolution
- Cached NOAA/NWS, SPC, and geocoding requests to reduce latency and API load
- Concurrent data fetching for top-level glance panels and SPC imagery
- Share-link query parameter syncing plus lightweight local analytics event logging
- Radar loops served from NWS RIDGE products and satellite imagery from NOAA NESDIS STAR

---

## Project Purpose

- Meteorology portfolio application
- Real-time severe weather situational awareness tool
- Demonstration of operational API integration, UI design, and modular app architecture

---

## Roadmap

- Expanded historical severe-weather statistics and archive views
- Additional observation and analysis layers
- Release/versioning cleanup and deployment hardening
"""
    )

    st.markdown("---")
    st.caption(
        "This dashboard is for educational and informational purposes only. "
        "Use official NOAA/NWS products and local emergency management guidance for life-safety decisions."
    )
