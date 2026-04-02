import re
import time
from html import unescape
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
import streamlit as st

USER_AGENT = "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}
IMAGE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

PARTNERS_BASE = "https://www.spc.noaa.gov/partners/outlooks/national"
OUTLOOK_PAGE_URLS = {
    1: "https://www.spc.noaa.gov/products/outlook/day1otlk.html",
    2: "https://www.spc.noaa.gov/products/outlook/day2otlk.html",
    3: "https://www.spc.noaa.gov/products/outlook/day3otlk.html",
}
DAY4_8_IMAGE_BASE = "https://www.spc.noaa.gov/products/exper/day4-8"
REQUEST_TIMEOUT = (3, 8)
CACHE_TTL_SECONDS = 900
DAY_DETAIL_MAP_LABELS = {
    1: [
        ("tornado", "Tornado Probability"),
        ("wind", "Wind Probability"),
        ("hail", "Hail Probability"),
    ],
    2: [
        ("tornado", "Tornado Probability"),
        ("wind", "Wind Probability"),
        ("hail", "Hail Probability"),
    ],
    3: [
        ("probability", "Total Severe Probability"),
    ],
}


def _with_cache_bust(url: str, bucket: int | None = None) -> str:
    bucket = bucket if bucket is not None else int(time.time() // CACHE_TTL_SECONDS)
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["t"] = str(bucket)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _fetch_text(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def _is_image_available(url: str) -> bool:
    response = requests.get(url, headers=IMAGE_HEADERS, timeout=REQUEST_TIMEOUT, stream=True)
    try:
        response.raise_for_status()
        content_type = (response.headers.get("Content-Type") or "").lower()
        return content_type.startswith("image/")
    except requests.RequestException:
        return False
    finally:
        response.close()


def _extract_print_page_url(day: int, html: str) -> str | None:
    match = re.search(r'href="([^"]+_prt\.html)"', html, flags=re.IGNORECASE)
    if match:
        return urljoin(OUTLOOK_PAGE_URLS[day], match.group(1))
    return None


def _extract_print_image_url(day: int, html: str, base_url: str) -> str | None:
    pattern = rf'(?:src|href)="([^"]*day{day}otlk_[^"]+?_prt\.(?:png|gif))"'
    match = re.search(pattern, html, flags=re.IGNORECASE)
    if match:
        return urljoin(base_url, match.group(1))
    return None


def _resolve_print_fallback(day: int) -> str | None:
    page_url = OUTLOOK_PAGE_URLS[day]
    try:
        html = _fetch_text(page_url)
    except requests.RequestException:
        return None

    direct_from_page = _extract_print_image_url(day, html, page_url)
    if direct_from_page and _is_image_available(direct_from_page):
        return direct_from_page

    print_page_url = _extract_print_page_url(day, html)
    if not print_page_url:
        return None

    try:
        print_html = _fetch_text(print_page_url)
    except requests.RequestException:
        return None

    print_image_url = _extract_print_image_url(day, print_html, print_page_url)
    if print_image_url and _is_image_available(print_image_url):
        return print_image_url
    return None


def _strip_tags(raw_html: str) -> str:
    return re.sub(r"<[^>]+>", "", raw_html)


def _normalize_discussion_text(raw_html: str) -> str:
    text = unescape(_strip_tags(raw_html))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_discussion_text(html: str) -> str | None:
    pre_blocks = re.findall(r"<pre[^>]*>(.*?)</pre>", html, flags=re.IGNORECASE | re.DOTALL)
    if pre_blocks:
        text = "\n\n".join(_normalize_discussion_text(block) for block in pre_blocks if block.strip())
        return text.strip() or None

    discussion_match = re.search(
        r"Forecast Discussion(.*?)(?:NOTE:\s+THE NEXT DAY|\Z)",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not discussion_match:
        return None
    text = _normalize_discussion_text(discussion_match.group(1))
    return text or None


def _extract_updated_text(html: str) -> str | None:
    match = re.search(r"Updated:\s*(.*?)\s*(?:\(|<)", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    updated = _normalize_discussion_text(match.group(1))
    return updated or None


def _extract_valid_text(discussion_text: str | None) -> str | None:
    if not discussion_text:
        return None
    match = re.search(r"Valid\s+([^\n]+)", discussion_text)
    if not match:
        return None
    return match.group(1).strip()


def _extract_detail_maps(day: int, html: str, base_url: str) -> list[dict]:
    maps: list[dict] = []

    categorical_match = re.search(
        rf'(?:src|href)="([^"]*day{day}otlk_[^"]+?_prt\.(?:png|gif))"',
        html,
        flags=re.IGNORECASE,
    )
    if categorical_match:
        maps.append(
            {
                "key": "categorical",
                "label": "Categorical Outlook",
                "url": _with_cache_bust(urljoin(base_url, categorical_match.group(1))),
                "primary": True,
            }
        )

    for key, label in DAY_DETAIL_MAP_LABELS.get(day, []):
        if day == 3 and key == "probability":
            pattern = r'(?:src|href)="([^"]*day3[^"]*prob[^"]*_prt\.(?:png|gif))"'
        else:
            pattern = rf'(?:src|href)="([^"]*day{day}probotlk_[^"]*_{key}_prt\.(?:png|gif))"'

        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            maps.append(
                {
                    "key": key,
                    "label": label,
                    "url": _with_cache_bust(urljoin(base_url, match.group(1))),
                    "primary": False,
                }
            )

    return maps


def _resolve_day_1_3_image(day: int) -> str | None:
    bucket = int(time.time() // CACHE_TTL_SECONDS)
    partner_url = f"{PARTNERS_BASE}/swody{day}.png"
    if _is_image_available(partner_url):
        return _with_cache_bust(partner_url, bucket)

    fallback_url = _resolve_print_fallback(day)
    if fallback_url:
        return _with_cache_bust(fallback_url, bucket)
    return None


def get_day1_categorical_image_url() -> str | None:
    return _resolve_day_1_3_image(1)


def get_day2_categorical_image_url() -> str | None:
    return _resolve_day_1_3_image(2)


def get_day3_categorical_image_url() -> str | None:
    return _resolve_day_1_3_image(3)


def get_day4_8_prob_image_url(day: int) -> str | None:
    if day < 4 or day > 8:
        raise ValueError("day must be between 4 and 8")

    bucket = int(time.time() // CACHE_TTL_SECONDS)
    image_url = f"{DAY4_8_IMAGE_BASE}/day{day}prob.gif"
    if _is_image_available(image_url):
        return _with_cache_bust(image_url, bucket)
    return None


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_day1_3_detail_payload(day: int) -> dict:
    if day not in OUTLOOK_PAGE_URLS:
        raise ValueError("day must be 1, 2, or 3")

    page_url = OUTLOOK_PAGE_URLS[day]
    page_html = _fetch_text(page_url)
    print_page_url = _extract_print_page_url(day, page_html) or page_url
    print_html = _fetch_text(print_page_url) if print_page_url != page_url else page_html

    maps = _extract_detail_maps(day, print_html, print_page_url)
    discussion = _extract_discussion_text(print_html)
    updated = _extract_updated_text(page_html) or _extract_updated_text(print_html)
    valid_period = _extract_valid_text(discussion)

    return {
        "day": day,
        "title": f"Day {day} Severe Weather Details",
        "page_url": page_url,
        "print_page_url": print_page_url,
        "updated": updated,
        "valid_period": valid_period,
        "maps": maps,
        "discussion": discussion,
    }
