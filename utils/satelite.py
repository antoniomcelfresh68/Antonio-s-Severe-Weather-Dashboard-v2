from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

GOES_BASE = "https://cdn.star.nesdis.noaa.gov"

GOES_SATS = {
    "GOES-East": "GOES19",
    "GOES-West": "GOES18",
}

GOES_SECTORS = {
    "CONUS": "CONUS",
    "Full Disk": "FD",
    "Mesoscale 1": "M1",
    "Mesoscale 2": "M2",
}

GOES_PRODUCTS = {
    "GeoColor": "GEOCOLOR",
    "Air Mass RGB": "AIRMASS",
    "Clean IR": "CLEANIR",
    "Water Vapor": "WV",
    "Dust RGB": "DUST",
    "Fire Temperature": "FIRETEMP",
    "Band 02 Visible": "BAND02",
    "Band 13 IR": "BAND13",
}


def render_satellite_panel() -> None:
    st.markdown(" # Satellite")

    config = {
        "baseUrl": GOES_BASE,
        "satellite": GOES_SATS["GOES-East"],
        "sector": GOES_SECTORS["CONUS"],
        "product": GOES_PRODUCTS["GeoColor"],
    }

    html = f"""
    <div style="font-family: Arial, sans-serif; color: #e5eef7;">
      <style>
        .sat-shell {{
          background: linear-gradient(180deg, #0b1724 0%, #102235 100%);
          border: 1px solid #24415f;
          border-radius: 18px;
          overflow: hidden;
        }}
        .sat-stage {{
          padding: 16px;
        }}
        .sat-frame {{
          background: #07111b;
          border: 1px solid #24415f;
          border-radius: 16px;
          overflow: hidden;
        }}
        .sat-image {{
          display: block;
          width: 100%;
          min-height: 720px;
          object-fit: contain;
          background: #050b12;
        }}
        @media (max-width: 760px) {{
          .sat-image {{
            min-height: 480px;
          }}
        }}
      </style>
      <div class="sat-shell">
        <div class="sat-stage">
          <div class="sat-frame">
            <img id="sat-image" class="sat-image" alt="GOES-East GeoColor satellite image" />
          </div>
        </div>
      </div>
      <script>
        const config = {json.dumps(config)};
        const image = document.getElementById("sat-image");

        function buildUrl() {{
          return `${{config.baseUrl}}/${{config.satellite}}/ABI/${{config.sector}}/${{config.product}}/latest.jpg?cb=${{Date.now()}}`;
        }}

        function renderImage() {{
          image.src = buildUrl();
        }}

        renderImage();
        window.setInterval(renderImage, 60000);
      </script>
    </div>
    """

    components.html(html, height=920, scrolling=False)
    st.caption("GOES imagery from NOAA NESDIS STAR.")
