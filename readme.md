# Antonio's Severe Weather Dashboard
## Version 4.0

Operational severe weather dashboard built with Streamlit for fast, location-aware monitoring of SPC outlooks, NOAA/NWS forecasts and observations, radar, satellite imagery, and active severe alerts.

---

## What's New in v4.0.0

- Version badge updated to `v4.0.0`
- New searchable location workflow:
  - Search by city or street address
  - Autosuggested location matches
  - Browser device geolocation
  - Local NWS office quick link for the selected point
- New share snapshot workflow:
  - Generates a shareable link pinned to the current location
  - Restores shared location state through URL query parameters
  - Tracks local analytics events for shared-link opens and share-link creation
- Expanded home-page glance panels:
  - Current temperature and dewpoint
  - Year-to-date tornado warning count
  - Year-to-date severe thunderstorm warning count
  - National SPC Day 1 severe summary with tornado, wind, and hail highlights
- New forecast experience:
  - Styled forecast hero with trend callouts
  - Hourly temperature and precipitation charting
  - Near-term and multi-period NOAA/NWS forecast cards
- Expanded observations experience:
  - GOES satellite viewer with selectable satellite, sector, and product
  - Auto-selected nearby radar loops
  - SPC mesoanalysis embedded viewer
- Updated SPC location intelligence:
  - Day 1-2 hazard percentages for tornado, wind, and hail
  - Conditional Intensity Group labels when present
  - Day 3 probability at the selected location

---

## Core Features

### Home

- Nationwide severe alert ticker for:
  - Tornado Warning
  - Severe Thunderstorm Warning
  - Tornado Watch
  - Severe Thunderstorm Watch
- Redesigned hero with logo, current location, and version badge
- Live glance cards for temperature/dewpoint, warning totals, and national SPC Day 1 summary
- SPC Day 1-3 categorical outlook images
- SPC Day 4-7 probabilistic outlook images
- Location-based SPC hazard percentages
  - Day 1: tornado, wind, hail
  - Day 2: tornado, wind, hail
  - Day 3: overall probability
- Conditional Intensity Group labels when your point falls inside SPC CIG overlays

### Observations

- SPC mesoanalysis embedded viewer
- Nearest radar selection from NWS points API
- Radar loops:
  - Base Reflectivity
  - Base Velocity
- GOES satellite viewer
  - GOES-East and GOES-West support
  - CONUS, Full Disk, and mesoscale sectors
  - Multiple products including GeoColor, Air Mass RGB, Water Vapor, and infrared bands
- Latest nearby NWS observation data powers the top-level temperature, dewpoint, wind, and conditions glance state

### Forecast

- Free NOAA/NWS forecast for the selected location
- Forecast hero with current conditions signal and next-period trend messaging
- Hourly temperature and precipitation charting
- Multi-period outlook cards with detailed forecast text

### Location and Sharing

- City and address geocoding through OpenStreetMap Nominatim
- Device geolocation option in the browser
- Shared location state across tabs
- Shareable snapshot links that reopen the dashboard on the same point and default to the Home view

---

## Project Structure

```text
Antonio-s-Severe-Weather-Dashboard/
|-- app.py
|-- assets/
|   |-- banner.jpg
|   |-- logo.png
|   `-- gallery/
|-- analytics/
|   `-- events.jsonl
|-- utils/
|   |-- about.py
|   |-- config.py
|   |-- forecast.py
|   |-- home.py
|   |-- location.py
|   |-- nws.py
|   |-- nws_alerts.py
|   |-- observations.py
|   |-- satelite.py
|   |-- share.py
|   |-- spc.py
|   |-- spc_outlooks.py
|   |-- state.py
|   |-- ticker.py
|   |-- tornado_warning_counter.py
|   |-- severe_thunderstorm_warning_counter.py
|   `-- ui.py
`-- requirements.txt
```

---

## Data Sources

- NOAA / NWS API:
  - `https://api.weather.gov/alerts/active`
  - `https://api.weather.gov/points/{lat},{lon}`
  - forecast and hourly forecast endpoints
  - observation station and latest observation endpoints
- NOAA SPC outlook map services and outlook imagery
- NWS RIDGE radar imagery
- NOAA NESDIS STAR GOES satellite imagery
- OpenStreetMap Nominatim geocoding

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deployment Notes

- Streamlit Cloud-safe (no desktop GUI dependencies)
- Cached NWS/SPC requests to reduce API load
- Query-parameter share links supported
- Local analytics log writes to `analytics/events.jsonl` when sharing actions occur
- Ensure `assets/logo.png` and `assets/banner.jpg` are present before deploy

---

## Author

Antonio McElfresh  
Meteorology - University of Oklahoma  
GIS Minor

---

## Disclaimer

This dashboard is for educational and informational use only.  
For life-safety decisions, always use official NOAA/NWS products and local emergency management guidance.
