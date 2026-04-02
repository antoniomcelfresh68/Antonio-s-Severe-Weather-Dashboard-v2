# utils/spc.py

import re
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st
from typing import List, Optional

@st.cache_data(ttl=300, show_spinner=False)
def get_spc_location_percents_cached(lat: float, lon: float) -> dict:
    return get_spc_location_percents(lat, lon)


@st.cache_data(ttl=300, show_spinner=False)
def get_spc_day1_national_summary_cached() -> dict:
    return get_spc_day1_national_summary()

SPC_BASE = "https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/MapServer"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}
def _get_json(url: str, params: Optional[dict] = None, timeout: int = 25) -> dict:
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

_service_info_cache: Optional[dict] = None

def spc_service_info() -> dict:
    global _service_info_cache
    if _service_info_cache is None:
        _service_info_cache = _get_json(SPC_BASE, params={"f": "pjson"})
    return _service_info_cache

def find_layer_id(day_label: str, contains: str) -> Optional[int]:
    """
    Find a layer ID by matching substrings in the layer name.
    Example: day_label="Day 1", contains="Categorical"
    """
    day = day_label.lower()
    key = contains.lower()
    for lyr in spc_service_info().get("layers", []) or []:
        name = (lyr.get("name") or "").lower()
        if day in name and key in name:
            return int(lyr["id"])
    # fallback for "probabilistic" naming variations
    if key == "probabilistic":
        for lyr in spc_service_info().get("layers", []) or []:
            name = (lyr.get("name") or "").lower()
            if day in name and ("prob" in name or "probability" in name):
                return int(lyr["id"])
    return None

@st.cache_data(ttl=300, show_spinner=False)
def layer_geojson(layer_id: int) -> dict:
    url = f"{SPC_BASE}/{layer_id}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    return _get_json(url, params=params)


def _point_in_ring(x: float, y: float, ring: list) -> bool:
    # ray casting
    inside = False
    n = len(ring)
    if n < 3:
        return False
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        # check crossing
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1) * (y - y1) / ((y2 - y1) if (y2 - y1) != 0 else 1e-12) + x1
            if x < xinters:
                inside = not inside
    return inside

def _point_in_polygon(x: float, y: float, coords: list) -> bool:
    # coords = [outer_ring, hole1, hole2...]
    if not coords:
        return False
    outer = coords[0]
    if not _point_in_ring(x, y, outer):
        return False
    # must not be inside any hole
    for hole in coords[1:]:
        if _point_in_ring(x, y, hole):
            return False
    return True

def point_in_geometry(lon: float, lat: float, geom: dict) -> bool:
    if not geom:
        return False
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return False

    if gtype == "Polygon":
        return _point_in_polygon(lon, lat, coords)
    if gtype == "MultiPolygon":
        for poly in coords:
            if _point_in_polygon(lon, lat, poly):
                return True
        return False
    return False

_CAT_RANK = {"TSTM": 1, "MRGL": 2, "SLGT": 3, "ENH": 4, "MDT": 5, "HIGH": 6}

def _extract_label(props: dict) -> str:
    for k in ("LABEL", "label", "CAT", "cat", "RISK", "risk", "Name", "name"):
        v = props.get(k)
        if v not in (None, "", " "):
            return str(v).strip()
    return ""

def _extract_percent(props: dict) -> Optional[int]:
    label = _extract_label(props)
    if "cig" in label.lower():
        return None

    # Most services include LABEL like "5%", "15%", or "0.15"
    lab = _extract_label(props)
    if re.fullmatch(r"0?\.\d{2}", lab):
        val = int(round(float(lab) * 100))
        if 0 < val <= 100:
            return val

    m = re.search(r"(\d{1,2})\s*%?", lab)
    if m:
        val = int(m.group(1))
        if 0 < val <= 100:
            return val

    # fallback: scan numeric fields that look like percents
    for v in props.values():
        if isinstance(v, (int, float)) and 0 < v <= 100:
            return int(v)
        if isinstance(v, str):
            s = v.strip().replace("%", "")
            if s.lower().startswith("cig"):
                continue
            if re.fullmatch(r"0?\.\d{2}", s):
                val = int(round(float(s) * 100))
                if 0 < val <= 100:
                    return val
            if s.isdigit():
                val = int(s)
                if 0 < val <= 100:
                    return val
    return None


def _extract_cig(props: dict) -> Optional[str]:
    for key in ("label", "label2", "LABEL", "LABEL2"):
        value = props.get(key)
        if not isinstance(value, str):
            continue
        match = re.search(r"\b(CIG[1-3])\b", value.upper())
        if match:
            return match.group(1)
    return None

def point_day1_3_category(lat: float, lon: float, day: str) -> str:
    layer_id = find_layer_id(day, "Categorical")
    if layer_id is None:
        return "—"
    gj = layer_geojson(layer_id)

    best = None
    best_rank = 0

    for feat in gj.get("features", []) or []:
        if not point_in_geometry(lon, lat, feat.get("geometry", {})):
            continue
        lab = _extract_label(feat.get("properties", {}) or "").upper()
        rank = _CAT_RANK.get(lab, 0)
        if rank > best_rank:
            best_rank = rank
            best = lab

    return best if best else "NONE"

def point_day_prob(lat: float, lon: float, day: str) -> Optional[int]:
    layer_id = find_layer_id(day, "Probabilistic") or find_layer_id(day, "Probability")
    if layer_id is None:
        return None

    url = f"{SPC_BASE}/{layer_id}/query"
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
    }

    data = _get_json(url, params=params)

    best = None
    for feat in data.get("features", []) or []:
        props = feat.get("attributes", {})
        pct = _extract_percent(props)
        if pct is None:
            continue
        if best is None or pct > best:
            best = pct

    return best

def get_spc_point_summary(lat: float, lon: float) -> dict:
    """
    Returns:
      - day1/day2/day3 categorical risk at point
      - day4-7 probabilistic percent at point
    """
    out = {
        "day1_cat": point_day1_3_category(lat, lon, "Day 1"),
        "day2_cat": point_day1_3_category(lat, lon, "Day 2"),
        "day3_cat": point_day1_3_category(lat, lon, "Day 3"),
        "day4_pct": point_day_prob(lat, lon, "Day 4"),
        "day5_pct": point_day_prob(lat, lon, "Day 5"),
        "day6_pct": point_day_prob(lat, lon, "Day 6"),
        "day7_pct": point_day_prob(lat, lon, "Day 7"),
    }
    return out

def _find_layer_id_any(day_label: str, keywords: List[str]) -> Optional[int]:
    """
    More flexible layer finder: all keywords must appear in layer name.
    """
    day = day_label.lower()
    keys = [k.lower() for k in keywords]
    for lyr in spc_service_info().get("layers", []) or []:
        name = (lyr.get("name") or "").lower()
        if day in name and all(k in name for k in keys):
            return int(lyr["id"])
    return None

DAY_HAZARD_LAYER_IDS = {
    "Day 1": {
        "tornado": 3,
        "hail": 5,
        "wind": 7,
    },
    "Day 2": {
        "tornado": 11,
        "hail": 13,
        "wind": 15,
    },
}

def point_hazard_percent(lat: float, lon: float, day: str, hazard: str) -> Optional[int]:
    hz = hazard.lower()

    layer_id = DAY_HAZARD_LAYER_IDS.get(day, {}).get(hz)
    if layer_id is None:
        return None

    url = f"{SPC_BASE}/{layer_id}/query"
    params = {
        "f": "json",
        "where": "1=1",  # <-- REQUIRED (this is the fix)
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "dn,label",     # keep it small
        "returnGeometry": "false",
        "resultRecordCount": "50",
    }

    data = _get_json(url, params=params)

    feats = data.get("features", []) or []
    if not feats:
        return None

    # dn is the percent bucket; take the max one that intersects
    best = max(feats, key=lambda f: (f.get("attributes") or {}).get("dn", -999))
    dn = (best.get("attributes") or {}).get("dn")

    return int(dn) if isinstance(dn, (int, float)) else None


def point_hazard_summary(lat: float, lon: float, day: str, hazard: str) -> dict:
    hz = hazard.lower()
    layer_id = DAY_HAZARD_LAYER_IDS.get(day, {}).get(hz)
    if layer_id is None:
        return {"percent": None, "cig": None}

    url = f"{SPC_BASE}/{layer_id}/query"
    params = {
        "f": "json",
        "where": "1=1",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "dn,label,label2",
        "returnGeometry": "false",
        "resultRecordCount": "50",
    }

    data = _get_json(url, params=params)

    best_percent = None
    best_cig = None
    best_cig_rank = 0

    for feat in data.get("features", []) or []:
        props = feat.get("attributes", {}) or {}

        pct = _extract_percent(props)
        if pct is not None and (best_percent is None or pct > best_percent):
            best_percent = pct

        cig = _extract_cig(props)
        if cig:
            rank = int(cig[-1])
            if rank > best_cig_rank:
                best_cig = cig
                best_cig_rank = rank

    return {"percent": best_percent, "cig": best_cig}

def get_spc_location_percents(lat: float, lon: float) -> dict:
    """
    v1-style numbers for the location.
    Day 1/2: tornado/wind/hail %
    Day 4–7: general probability %
    """
    tasks = {
        "d1_tor": ("Day 1", "tornado"),
        "d1_wind": ("Day 1", "wind"),
        "d1_hail": ("Day 1", "hail"),
        "d2_tor": ("Day 2", "tornado"),
        "d2_wind": ("Day 2", "wind"),
        "d2_hail": ("Day 2", "hail"),
    }

    with ThreadPoolExecutor(max_workers=len(tasks) + 1) as executor:
        futures = {
            key: executor.submit(point_hazard_summary, lat, lon, day, hazard)
            for key, (day, hazard) in tasks.items()
        }
        d3_future = executor.submit(point_day_prob, lat, lon, "Day 3")

    d1_tor = futures["d1_tor"].result()
    d1_wind = futures["d1_wind"].result()
    d1_hail = futures["d1_hail"].result()
    d2_tor = futures["d2_tor"].result()
    d2_wind = futures["d2_wind"].result()
    d2_hail = futures["d2_hail"].result()

    return {
        "d1_tor": d1_tor["percent"],
        "d1_tor_cig": d1_tor["cig"],
        "d1_wind": d1_wind["percent"],
        "d1_wind_cig": d1_wind["cig"],
        "d1_hail": d1_hail["percent"],
        "d1_hail_cig": d1_hail["cig"],

        "d2_tor": d2_tor["percent"],
        "d2_tor_cig": d2_tor["cig"],
        "d2_wind": d2_wind["percent"],
        "d2_wind_cig": d2_wind["cig"],
        "d2_hail": d2_hail["percent"],
        "d2_hail_cig": d2_hail["cig"],
        "d3_prob": d3_future.result(),
    }


def get_spc_day1_national_summary() -> dict:
    """Return the highest Day 1 categorical risk and hazard percentages nationwide."""
    category = "NONE"
    category_rank = 0

    categorical_layer_id = find_layer_id("Day 1", "Categorical")
    if categorical_layer_id is not None:
        gj = layer_geojson(categorical_layer_id)
        for feat in gj.get("features", []) or []:
            label = _extract_label(feat.get("properties", {}) or {}).upper()
            rank = _CAT_RANK.get(label, 0)
            if rank > category_rank:
                category = label
                category_rank = rank

    def _hazard_best_percent(hazard: str) -> Optional[int]:
        layer_id = DAY_HAZARD_LAYER_IDS.get("Day 1", {}).get(hazard)
        if layer_id is None:
            return None

        best_percent = None
        gj = layer_geojson(layer_id)
        for feat in gj.get("features", []) or []:
            pct = _extract_percent(feat.get("properties", {}) or {})
            if pct is not None and (best_percent is None or pct > best_percent):
                best_percent = pct
        return best_percent

    with ThreadPoolExecutor(max_workers=3) as executor:
        hazard_futures = {
            hazard: executor.submit(_hazard_best_percent, hazard)
            for hazard in ("tornado", "wind", "hail")
        }

    hazard_percents = {hazard: future.result() for hazard, future in hazard_futures.items()}

    return {
        "category": category,
        "tornado": hazard_percents["tornado"],
        "wind": hazard_percents["wind"],
        "hail": hazard_percents["hail"],
    }
