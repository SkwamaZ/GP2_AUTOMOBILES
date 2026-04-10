from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from cars_config import BASE_COLUMNS, MARKET_NAMES_EN, MODEL_CONFIGS
from cars_http import clean_number, ensure_columns, fetch_page, load_cache, save_cache
from cars_normalization import normalize_model_key
from cars_paths import (
    ASIA_MAX_PAGES,
    ASIA_TARGET_ROWS,
    AUTOSCOUT_PAGE_SIZE,
    EU_MAX_PAGES_PER_MODEL,
    EU_ROWS_PER_MODEL,
    RUSSIA_MAX_PAGES,
    RUSSIA_MODEL_MAX_PAGES,
    RUSSIA_TARGET_ROWS,
)
from cars_specs import infer_specs_from_text
from cars_text import build_clean_title, english_title, normalize_brand, normalize_fuel_type, normalize_transmission


logger = logging.getLogger("cars_project")

TCV_ALL_CARS_URL = "https://www.tc-v.com/used_car/all/all/"
AUTO_RU_USED_URL = "https://auto.ru/cars/used/"
AUTO_RU_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

KNOWN_TITLE_BRANDS = (
    "Mercedes-Benz",
    "Land Rover",
    "Alfa Romeo",
    "Aston Martin",
    "Great Wall",
    "Rolls-Royce",
    "Volkswagen",
    "Porsche",
    "Toyota",
    "Hyundai",
    "Chevrolet",
    "Mitsubishi",
    "Subaru",
    "Suzuki",
    "Renault",
    "Peugeot",
    "Citroen",
    "Jaguar",
    "Lexus",
    "Mazda",
    "Honda",
    "Nissan",
    "Skoda",
    "Audi",
    "BMW",
    "Kia",
    "Ford",
    "Mini",
    "Jeep",
    "Volvo",
    "Chrysler",
    "Cadillac",
    "Infiniti",
    "Lada",
    "Geely",
    "Chery",
    "Haval",
    "Xiaomi",
    "Brabus",
)

MODEL_SLUG_ALIASES = {
    "c hr": "C-HR",
    "c klasse": "C-Class",
    "cla klasse": "CLA-Class",
    "cx 5": "CX-5",
    "e klasse": "E-Class",
    "g klasse": "G-Class",
    "glb klasse": "GLB-Class",
    "glc klasse": "GLC-Class",
    "gle klasse": "GLE-Class",
    "gls klasse": "GLS-Class",
    "land cruiser": "Land Cruiser",
    "land cruiser prado": "Land Cruiser Prado",
    "range rover": "Range Rover",
    "range rover evoque": "Range Rover Evoque",
    "range rover sport": "Range Rover Sport",
    "range rover velar": "Range Rover Velar",
    "s klasse": "S-Class",
    "v klasse": "V-Class",
    "x ceed": "XCeed",
    "x trail": "X-Trail",
    "yaris cross": "Yaris Cross",
}

RUSSIA_MODEL_URLS = (
    "https://auto.ru/cars/bmw/x5/all/",
    "https://auto.ru/cars/bmw/x7/all/",
    "https://auto.ru/cars/toyota/alphard/all/",
    "https://auto.ru/cars/porsche/panamera/all/",
    "https://auto.ru/cars/porsche/cayenne/all/",
    "https://auto.ru/cars/volkswagen/tiguan/all/",
    "https://auto.ru/cars/audi/q5/all/",
    "https://auto.ru/cars/audi/q7/all/",
    "https://auto.ru/cars/toyota/camry/all/",
    "https://auto.ru/cars/kia/sorento/all/",
    "https://auto.ru/cars/kia/picanto/all/",
    "https://auto.ru/cars/kia/soul/all/",
    "https://auto.ru/cars/kia/carnival/all/",
    "https://auto.ru/cars/hyundai/tucson/all/",
    "https://auto.ru/cars/skoda/kodiaq/all/",
)


def build_chrome_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--lang=ru-RU")
    return webdriver.Chrome(options=options)


def parse_next_data(response_text: str) -> dict[str, Any]:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response_text)
    if not match:
        raise ValueError("AutoScout24 payload not found")
    return json.loads(match.group(1))["props"]["pageProps"]


def parse_power_hp_from_autoscout(item: dict[str, Any]) -> int | None:
    for detail in item.get("vehicleDetails", []):
        if detail.get("ariaLabel") != "Power":
            continue
        text = str(detail.get("data") or "")
        hp_match = re.search(r"\(([\d\s]+)\s*hp\)", text, flags=re.IGNORECASE)
        if hp_match:
            return clean_number(hp_match.group(1))
        hp_match = re.search(r"([\d\s]+)\s*hp", text, flags=re.IGNORECASE)
        if hp_match:
            return clean_number(hp_match.group(1))
        kw_match = re.search(r"(\d+)\s*kW", text, flags=re.IGNORECASE)
        if kw_match:
            return int(round(int(kw_match.group(1)) * 1.35962))
    return None


def parse_autoscout_payload(payload: dict[str, Any], config) -> tuple[pd.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("listings", []):
        vehicle = item.get("vehicle", {})
        details = {detail.get("ariaLabel"): detail.get("data") for detail in item.get("vehicleDetails", [])}
        year_match = re.search(r"(19|20)\d{2}", str(details.get("First registration", "")))
        price_value = clean_number(item.get("price", {}).get("priceFormatted"))
        if not vehicle or not year_match or not price_value:
            continue

        fuel_type = normalize_fuel_type(vehicle.get("fuel") or details.get("Fuel type"))
        transmission = normalize_transmission(vehicle.get("transmission") or details.get("Gear"))
        row = {
            "market": "EU",
            "market_name": MARKET_NAMES_EN["EU"],
            "source_portal": "AutoScout24",
            "collection_method": "Scraping",
            "brand": config.brand,
            "model": config.model,
            "model_key": config.model_key,
            "listing_title": "",
            "year": int(year_match.group()),
            "mileage_km": clean_number(details.get("Mileage") or vehicle.get("mileageInKm")),
            "price_original": price_value,
            "currency": "EUR",
            "link": "https://www.autoscout24.com" + item.get("url", ""),
            "engine_cc": clean_number(vehicle.get("engineDisplacementInCCM")),
            "power_hp": parse_power_hp_from_autoscout(item),
            "fuel_type": fuel_type,
            "transmission": transmission,
            "spec_source": "source",
        }
        row["listing_title"] = build_clean_title(config.brand, config.model, row["year"], fuel_type, transmission)
        rows.append(row)

    return ensure_columns(pd.DataFrame(rows), BASE_COLUMNS), int(payload.get("numberOfPages", 1))


def parse_autoscout_page_html(response_text: str, config) -> tuple[pd.DataFrame, int]:
    payload = parse_next_data(response_text)
    return parse_autoscout_payload(payload, config)


def fetch_autoscout_page_requests(session: requests.Session, config, page: int) -> tuple[pd.DataFrame, int]:
    url = f"{config.autoscout_url}?page={page}&size={AUTOSCOUT_PAGE_SIZE}&sort=standard&desc=0"
    response = fetch_page(session, url, pause=0.08)
    return parse_autoscout_page_html(response.text, config)


def fetch_autoscout_page_selenium(driver: webdriver.Chrome, config, page: int) -> tuple[pd.DataFrame, int]:
    url = f"{config.autoscout_url}?page={page}&size={AUTOSCOUT_PAGE_SIZE}&sort=standard&desc=0"
    driver.get(url)
    time.sleep(2.5)
    return parse_autoscout_page_html(driver.page_source, config)


def load_europe_data(session: requests.Session, *, force_refresh: bool = True) -> pd.DataFrame:
    if not force_refresh:
        cached = load_cache("EU")
        if cached is not None and len(cached) >= 5_000:
            logger.info("Europe cache is used: %s rows", len(cached))
            return cached

    cache_df = load_cache("EU")
    driver: webdriver.Chrome | None = None
    try:
        driver = build_chrome_driver()
        frames: list[pd.DataFrame] = []
        seen_links: set[str] = set()

        for config in MODEL_CONFIGS:
            model_frames: list[pd.DataFrame] = []
            max_pages = 1

            for page in range(1, EU_MAX_PAGES_PER_MODEL + 1):
                if page == 1 and driver is not None:
                    frame, number_of_pages = fetch_autoscout_page_selenium(driver, config, page)
                else:
                    frame, number_of_pages = fetch_autoscout_page_requests(session, config, page)

                max_pages = min(number_of_pages, EU_MAX_PAGES_PER_MODEL)
                if frame.empty:
                    break

                frame = frame[~frame["link"].isin(seen_links)].copy()
                seen_links.update(frame["link"].dropna().tolist())
                if frame.empty:
                    continue

                model_frames.append(frame)
                if sum(len(part) for part in model_frames) >= EU_ROWS_PER_MODEL or page >= max_pages:
                    break

            if model_frames:
                frames.append(pd.concat(model_frames, ignore_index=True).head(EU_ROWS_PER_MODEL))

        europe_df = ensure_columns(pd.concat(frames, ignore_index=True), BASE_COLUMNS) if frames else ensure_columns(pd.DataFrame(columns=BASE_COLUMNS), BASE_COLUMNS)
        if cache_df is not None and len(cache_df) > len(europe_df):
            europe_df = cache_df
        if not europe_df.empty:
            save_cache(europe_df, "EU")
            logger.info("Europe source collected: %s rows", len(europe_df))
        return europe_df
    except Exception:
        if cache_df is not None:
            logger.warning("Europe source is unavailable, cached data is used")
            return cache_df
        raise
    finally:
        if driver is not None:
            driver.quit()


def guess_brand_model_from_title(title_body: str) -> tuple[str, str]:
    normalized = english_title(title_body)
    lower_text = normalized.lower()
    for brand in KNOWN_TITLE_BRANDS:
        if lower_text.startswith(brand.lower() + " "):
            return brand, normalized[len(brand):].strip()

    parts = normalized.split()
    if not parts:
        return "", ""
    if len(parts) >= 2 and f"{parts[0]} {parts[1]}" in KNOWN_TITLE_BRANDS:
        brand = f"{parts[0]} {parts[1]}"
        return brand, normalized[len(brand):].strip()
    return parts[0], " ".join(parts[1:]).strip()


def parse_tcv_listing_card(card: BeautifulSoup) -> dict[str, Any] | None:
    text = " ".join(card.stripped_strings)
    href = None
    title = None

    for link in card.select('a[href^="/used_car/"]'):
        candidate_href = link.get("href")
        candidate_text = link.get_text(" ", strip=True)
        if href is None and candidate_href:
            href = candidate_href
        if title is None and candidate_text:
            title = candidate_text

    if href is None:
        return None

    if title is None:
        match = re.search(r"STOCK\s+(\d{4}\s+.+?)\s+FOB Price", text, flags=re.IGNORECASE)
        title = match.group(1).strip() if match else ""

    title = re.sub(r"^STOCK\s+", "", title, flags=re.IGNORECASE).strip()
    title_body = re.sub(r"^(?:19|20)\d{2}\s+", "", title).strip()
    year_match = re.search(r"Registration Year\s*(\d{4})", text, flags=re.IGNORECASE) or re.search(r"^(?:19|20)\d{2}", title)
    price_match = re.search(r"FOB Price\s*US\$\s*([\d,]+)", text, flags=re.IGNORECASE)
    mileage_match = re.search(r"Mileage\s*([\d,]+)km", text, flags=re.IGNORECASE)
    engine_match = re.search(r"Engine Capacity\s*([\d,]+)cc", text, flags=re.IGNORECASE)
    if year_match is None or price_match is None:
        return None

    brand, model_name = guess_brand_model_from_title(title_body)
    model_key = normalize_model_key(brand, model_name, title_body)

    fuel_type = None
    for candidate in ["Plug-in Hybrid", "Hybrid", "Diesel", "Gasoline", "Petrol", "Electric", "LPG"]:
        if candidate.lower() in text.lower():
            fuel_type = normalize_fuel_type(candidate)
            break

    transmission = None
    for candidate in ["CVT", "Automatic", "Manual", "AT", "MT"]:
        if re.search(rf"\b{re.escape(candidate)}\b", text, flags=re.IGNORECASE):
            transmission = normalize_transmission(candidate)
            break

    year_text = year_match.group(1) if year_match.lastindex else year_match.group(0)
    row = {
        "market": "AS",
        "market_name": MARKET_NAMES_EN["AS"],
        "source_portal": "TCV",
        "collection_method": "Scraping",
        "brand": brand,
        "model": model_name,
        "model_key": model_key,
        "listing_title": "",
        "year": clean_number(year_text),
        "mileage_km": clean_number(mileage_match.group(1)) if mileage_match else None,
        "price_original": clean_number(price_match.group(1)),
        "currency": "USD",
        "link": f"https://www.tc-v.com{href}",
        "engine_cc": clean_number(engine_match.group(1)) if engine_match else None,
        "power_hp": None,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "spec_source": "source" if engine_match else None,
    }
    row["listing_title"] = build_clean_title(brand, model_name, row["year"], fuel_type, transmission)
    engine_cc, power_hp, spec_source = infer_specs_from_text(pd.Series(row))
    row["engine_cc"] = engine_cc
    row["power_hp"] = power_hp
    row["spec_source"] = spec_source
    return row


def load_asia_data(session: requests.Session, *, force_refresh: bool = True) -> pd.DataFrame:
    if not force_refresh:
        cached = load_cache("AS")
        if cached is not None and len(cached) >= ASIA_TARGET_ROWS:
            logger.info("Asia cache is used: %s rows", len(cached))
            return cached

    cache_df = load_cache("AS")
    try:
        rows: list[dict[str, Any]] = []
        seen_links: set[str] = set()

        for page in range(ASIA_MAX_PAGES):
            page_url = TCV_ALL_CARS_URL if page == 0 else f"{TCV_ALL_CARS_URL}?pn={page}"
            response = fetch_page(session, page_url, pause=0.08)
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("div.vehicle__car-item")
            if not cards:
                break

            for card in cards:
                row = parse_tcv_listing_card(card)
                if row is None or row["link"] in seen_links:
                    continue
                seen_links.add(row["link"])
                rows.append(row)

            if len(rows) >= ASIA_TARGET_ROWS:
                break

        asia_df = ensure_columns(pd.DataFrame(rows), BASE_COLUMNS).head(ASIA_TARGET_ROWS)
        if cache_df is not None and len(cache_df) > len(asia_df):
            asia_df = cache_df
        if not asia_df.empty:
            save_cache(asia_df, "AS")
            logger.info("Asia source collected: %s rows", len(asia_df))
        return asia_df
    except Exception:
        if cache_df is not None:
            logger.warning("Asia source is unavailable, cached data is used")
            return cache_df
        raise


def slug_to_title(slug: str | None) -> str:
    if not slug:
        return ""
    raw_slug = str(slug).replace("_", " ").replace("-", " ")
    clean_slug = english_title(raw_slug)
    alias_key = raw_slug.lower().strip()
    return MODEL_SLUG_ALIASES.get(alias_key, clean_slug)


def parse_auto_ru_link(link: str) -> tuple[str, str]:
    match = re.search(r"/sale/([^/]+)/([^/]+)/", link)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def parse_auto_ru_card(card: BeautifulSoup) -> dict[str, Any] | None:
    link_tag = card.select_one("a.ListingItemTitle__link")
    price_tag = card.select_one("div.ListingItemUniversalPrice__title-vqOQR")
    year_tag = card.select_one("div.ListingItemUniversalCondition-jdGR4 .Typography2__h5-mkmlZ")
    mileage_tag = card.select_one("div.ListingItemUniversalCondition__status-CEPP6 .Typography2__body2-dAL30")
    seller_tag = card.select_one("span.MetroListPlace__regionName")
    spec_tags = card.select("div.ListingItemUniversalSpecs__spec-S5lzA")

    if link_tag is None or price_tag is None or year_tag is None:
        return None

    link = str(link_tag.get("href") or "").strip()
    title_text = link_tag.get_text(" ", strip=True)
    price_value = clean_number(price_tag.get_text(" ", strip=True))
    year_value = clean_number(year_tag.get_text(" ", strip=True))

    if not link or not title_text or not price_value or not year_value:
        return None

    slug_brand, slug_model = parse_auto_ru_link(link)
    title_base = re.sub(r",\s*(19|20)\d{2}.*$", "", title_text).strip()
    brand_from_title, _ = guess_brand_model_from_title(title_base)
    brand = normalize_brand(brand_from_title or slug_brand.replace("_", " "))
    model = slug_to_title(slug_model)
    model_key = normalize_model_key(brand, model, title_base)

    spec_values = [tag.get_text(" ", strip=True) for tag in spec_tags]
    fuel_type = normalize_fuel_type(spec_values[0]) if spec_values else None
    transmission = None
    for value in spec_values:
        candidate = normalize_transmission(value)
        if candidate in {"Automatic", "Manual", "CVT", "Robot"}:
            transmission = candidate
            break

    mileage_from_title = None
    mileage_match = re.search(r"(\d[\d\s]*)\s*км", title_text, flags=re.IGNORECASE)
    if mileage_match:
        mileage_from_title = clean_number(mileage_match.group(1))

    row = {
        "market": "RU",
        "market_name": MARKET_NAMES_EN["RU"],
        "source_portal": "Auto.ru",
        "collection_method": "Scraping",
        "brand": brand,
        "model": model,
        "model_key": model_key,
        "listing_title": "",
        "year": year_value,
        "mileage_km": clean_number(mileage_tag.get_text(" ", strip=True)) if mileage_tag else mileage_from_title,
        "price_original": price_value,
        "currency": "RUB",
        "link": link,
        "engine_cc": None,
        "power_hp": None,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "spec_source": None,
    }
    if seller_tag is not None and seller_tag.get_text(" ", strip=True):
        row["listing_title"] = build_clean_title(brand, model, year_value, fuel_type, transmission) + f" | {english_title(seller_tag.get_text(' ', strip=True))}"
    else:
        row["listing_title"] = build_clean_title(brand, model, year_value, fuel_type, transmission)

    engine_cc, power_hp, spec_source = infer_specs_from_text(pd.Series(row))
    row["engine_cc"] = engine_cc
    row["power_hp"] = power_hp
    row["spec_source"] = spec_source
    return row


def extend_rows_from_auto_ru_page(
    session: requests.Session,
    page_url: str,
    rows: list[dict[str, Any]],
    seen_links: set[str],
) -> int:
    response = fetch_page(session, page_url, pause=0.1, headers=AUTO_RU_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("div.ListingCars__universalSnippetWrapper")
    if not cards:
        return 0

    before = len(rows)
    for card in cards:
        row = parse_auto_ru_card(card)
        if row is None or row["link"] in seen_links:
            continue
        seen_links.add(row["link"])
        rows.append(row)
    return len(rows) - before


def load_russia_data(session: requests.Session, *, force_refresh: bool = True) -> pd.DataFrame:
    if not force_refresh:
        cached = load_cache("RU")
        if cached is not None and len(cached) >= 5_000:
            logger.info("Russia cache is used: %s rows", len(cached))
            return cached

    cache_df = load_cache("RU")
    try:
        rows: list[dict[str, Any]] = []
        seen_links: set[str] = set()
        if cache_df is not None and not cache_df.empty:
            cache_records = ensure_columns(cache_df, BASE_COLUMNS).to_dict("records")
            rows.extend(cache_records)
            seen_links.update(str(record.get("link") or "") for record in cache_records if record.get("link"))
            logger.info("Russia source starts from cache seed: %s rows", len(rows))

        stale_pages = 0

        for page in range(1, RUSSIA_MAX_PAGES + 1):
            if len(rows) >= RUSSIA_TARGET_ROWS:
                break
            page_url = AUTO_RU_USED_URL if page == 1 else f"{AUTO_RU_USED_URL}?page={page}"
            added_on_page = extend_rows_from_auto_ru_page(session, page_url, rows, seen_links)
            if added_on_page == 0:
                stale_pages += 1
                if stale_pages >= 8:
                    break
                continue

            stale_pages = 0

            if len(rows) >= RUSSIA_TARGET_ROWS or stale_pages >= 5:
                break

        if len(rows) < RUSSIA_TARGET_ROWS:
            for base_url in RUSSIA_MODEL_URLS:
                for page in range(1, RUSSIA_MODEL_MAX_PAGES + 1):
                    if len(rows) >= RUSSIA_TARGET_ROWS:
                        break
                    page_url = base_url if page == 1 else f"{base_url}?page={page}"
                    extend_rows_from_auto_ru_page(session, page_url, rows, seen_links)
                if len(rows) >= RUSSIA_TARGET_ROWS:
                    break

        russia_df = ensure_columns(pd.DataFrame(rows), BASE_COLUMNS).head(RUSSIA_TARGET_ROWS)
        if not russia_df.empty:
            save_cache(russia_df, "RU")
            logger.info(
                "Russia source collected: %s rows after merge",
                len(russia_df),
            )
        return russia_df
    except Exception:
        if cache_df is not None:
            logger.warning("Russia source is unavailable, cached data is used")
            return cache_df
        raise
