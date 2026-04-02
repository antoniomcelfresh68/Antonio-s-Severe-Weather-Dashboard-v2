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
        "satellites": GOES_SATS,
        "sectors": GOES_SECTORS,
        "products": GOES_PRODUCTS,
        "defaults": {
            "satellite": "GOES-East",
            "sector": "CONUS",
            "product": "GeoColor",
        },
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
        .sat-toolbar {{
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          padding: 16px;
          background: rgba(7, 18, 29, 0.92);
          border-bottom: 1px solid #24415f;
        }}
        .sat-field {{
          display: flex;
          flex-direction: column;
          gap: 6px;
        }}
        .sat-label {{
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          color: #8fb3d9;
        }}
        .sat-select {{
          width: 100%;
          border: 1px solid #385a7b;
          border-radius: 10px;
          padding: 10px 12px;
          background: #112538;
          color: #f4f8fb;
          font-size: 15px;
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
        .sat-meta {{
          display: flex;
          justify-content: space-between;
          gap: 12px;
          padding: 12px 16px;
          background: rgba(8, 19, 31, 0.94);
          color: #b8cde2;
          font-size: 13px;
          border-top: 1px solid #24415f;
        }}
        .sat-button {{
          border: 1px solid #4a7297;
          border-radius: 999px;
          padding: 6px 12px;
          background: transparent;
          color: #d9e8f6;
          cursor: pointer;
          font-size: 13px;
        }}
        @media (max-width: 760px) {{
          .sat-toolbar {{
            grid-template-columns: 1fr;
          }}
          .sat-image {{
            min-height: 480px;
          }}
          .sat-meta {{
            flex-direction: column;
          }}
        }}
      </style>
      <div class="sat-shell">
        <div class="sat-toolbar">
          <label class="sat-field">
            <span class="sat-label">Satellite</span>
            <select id="satellite" class="sat-select"></select>
          </label>
          <label class="sat-field">
            <span class="sat-label">Sector</span>
            <select id="sector" class="sat-select"></select>
          </label>
          <label class="sat-field">
            <span class="sat-label">Product</span>
            <select id="product" class="sat-select"></select>
          </label>
        </div>
        <div class="sat-stage">
          <div class="sat-frame">
            <img id="sat-image" class="sat-image" alt="GOES satellite imagery viewer" />
            <div class="sat-meta">
              <div id="sat-caption"></div>
              <button id="refresh" class="sat-button" type="button">Refresh image</button>
            </div>
          </div>
        </div>
      </div>
      <script>
        const config = {json.dumps(config)};
        const satelliteSelect = document.getElementById("satellite");
        const sectorSelect = document.getElementById("sector");
        const productSelect = document.getElementById("product");
        const image = document.getElementById("sat-image");
        const caption = document.getElementById("sat-caption");
        const refreshButton = document.getElementById("refresh");

        function fillSelect(select, values, chosen) {{
          select.innerHTML = "";
          Object.keys(values).forEach((label) => {{
            const option = document.createElement("option");
            option.value = label;
            option.textContent = label;
            option.selected = label === chosen;
            select.appendChild(option);
          }});
        }}

        function buildUrl() {{
          const sat = config.satellites[satelliteSelect.value];
          const sector = config.sectors[sectorSelect.value];
          const product = config.products[productSelect.value];
          return `${{config.baseUrl}}/${{sat}}/ABI/${{sector}}/${{product}}/latest.jpg?cb=${{Date.now()}}`;
        }}

        function renderImage() {{
          const url = buildUrl();
          image.src = url;
          caption.textContent = `${{satelliteSelect.value}} | ${{sectorSelect.value}} | ${{productSelect.value}}`;
        }}

        fillSelect(satelliteSelect, config.satellites, config.defaults.satellite);
        fillSelect(sectorSelect, config.sectors, config.defaults.sector);
        fillSelect(productSelect, config.products, config.defaults.product);

        satelliteSelect.addEventListener("change", renderImage);
        sectorSelect.addEventListener("change", renderImage);
        productSelect.addEventListener("change", renderImage);
        refreshButton.addEventListener("click", renderImage);

        renderImage();
      </script>
    </div>
    """

    components.html(html, height=920, scrolling=False)
    st.caption("GOES imagery from NOAA NESDIS STAR.")
