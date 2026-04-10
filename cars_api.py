from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from cars_config import BASE_COLUMNS, MARKET_NAMES_EN, MODEL_CONFIG_BY_KEY, MODEL_CONFIGS
from cars_http import clean_float, clean_number, ensure_columns, fetch_page, load_cache, save_cache
from cars_normalization import normalize_model_key
from cars_paths import ENCAR_PAGE_SIZE, KOREA_MAX_PAGES, KOREA_TARGET_ROWS, OUTPUT_API_DEMO, OUTPUT_API_SPECS
from cars_specs import infer_specs_from_text, representative_year
from cars_text import build_clean_title, english_title, normalize_brand, normalize_fuel_type, normalize_transmission


logger = logging.getLogger("cars_project")

API_SPECS_COLUMNS = [
    "model_key",
    "api_make",
    "api_model",
    "api_year",
    "api_engine_cc",
    "api_cylinders",
    "api_drive",
    "api_fuel_type",
    "api_class",
    "api_transmission",
    "api_source",
]


def load_local_api_key() -> str | None:
    direct = os.getenv("API_NINJAS_KEY") or os.getenv("CARS_API_NINJAS_KEY")
    if direct:
        return direct

    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("API_NINJAS_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def parse_intish(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return int(round(float(value)))
    return clean_number(value)


def parse_year_value(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    match = clean_number(str(value)[:4])
    return match


def fetch_api_ninjas_specs(
    session: requests.Session,
    *,
    make: str,
    model: str,
    year: int,
    api_key: str,
) -> dict[str, Any] | None:
    response = fetch_page(
        session,
        "https://api.api-ninjas.com/v1/cars",
        pause=0.1,
        headers={"X-Api-Key": api_key},
        params={"make": make, "model": model, "year": year},
    )
    items = response.json()
    if not items:
        return None

    item = items[0]
    displacement_l = clean_float(item.get("displacement"))
    return {
        "api_make": make,
        "api_model": model,
        "api_year": year,
        "api_engine_cc": int(round(displacement_l * 1000)) if displacement_l else None,
        "api_cylinders": clean_number(item.get("cylinders")),
        "api_drive": item.get("drive"),
        "api_fuel_type": item.get("fuel_type"),
        "api_class": item.get("class"),
        "api_transmission": item.get("transmission"),
        "api_source": "API Ninjas (X-Api-Key)",
    }


def load_authenticated_specs(
    session: requests.Session,
    df: pd.DataFrame,
    *,
    force_refresh: bool = True,
) -> pd.DataFrame:
    api_key = load_local_api_key()
    if not force_refresh and OUTPUT_API_SPECS.exists():
        return pd.read_csv(OUTPUT_API_SPECS)

    if not api_key:
        if OUTPUT_API_SPECS.exists():
            logger.warning("API Ninjas key is missing, cached specs are used")
            return pd.read_csv(OUTPUT_API_SPECS)
        logger.warning("API Ninjas key is missing, live specs are skipped")
        return pd.DataFrame(columns=API_SPECS_COLUMNS)

    rows: list[dict[str, Any]] = []
    for config in MODEL_CONFIGS:
        year = representative_year(df, config.model_key)
        try:
            payload = fetch_api_ninjas_specs(
                session,
                make=config.api_make,
                model=config.api_model,
                year=year,
                api_key=api_key,
            )
        except Exception as exc:
            logger.warning("API Ninjas request failed for %s: %s", config.model_key, exc)
            continue

        if payload is None:
            continue
        payload["model_key"] = config.model_key
        rows.append(payload)

    api_specs_df = pd.DataFrame(rows, columns=API_SPECS_COLUMNS)
    if not api_specs_df.empty:
        api_specs_df.to_csv(OUTPUT_API_SPECS, index=False)
    return api_specs_df


def run_api_key_demo(
    session: requests.Session,
    reference_df: pd.DataFrame,
    *,
    requests_limit: int = 5,
) -> pd.DataFrame:
    api_key = load_local_api_key()
    if not api_key:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for config in MODEL_CONFIGS[:requests_limit]:
        year = representative_year(reference_df, config.model_key)
        payload = fetch_api_ninjas_specs(
            session,
            make=config.api_make,
            model=config.api_model,
            year=year,
            api_key=api_key,
        )
        rows.append(
            {
                "brand": config.brand,
                "model": config.model,
                "request_year": year,
                "success": payload is not None,
            }
        )
    demo_df = pd.DataFrame(rows)
    if not demo_df.empty:
        demo_df.to_csv(OUTPUT_API_DEMO, index=False)
    return demo_df


def parse_encar_listing(item: dict[str, Any]) -> dict[str, Any] | None:
    manufacturer = str(item.get("Manufacturer") or "").strip()
    model = str(item.get("Model") or "").strip()
    badge = str(item.get("Badge") or "").strip()
    badge_detail = str(item.get("BadgeDetail") or "").strip()
    detail_parts = [part for part in [model, badge, badge_detail] if part and part.lower() != "none"]
    detail_text = " ".join(detail_parts).strip()
    year = parse_year_value(item.get("Year") or item.get("FormYear"))
    price = parse_intish(item.get("Price"))
    vehicle_id = item.get("Id")

    if not detail_text or year is None or price is None or not vehicle_id:
        return None

    brand = normalize_brand(manufacturer)
    model_name = english_title(detail_text)
    model_key = normalize_model_key(brand, model_name, detail_text)
    known_config = MODEL_CONFIG_BY_KEY.get(model_key)
    if known_config:
        brand = known_config.brand
        model_name = known_config.model

    row = {
        "market": "KO",
        "market_name": MARKET_NAMES_EN["KO"],
        "source_portal": "Encar",
        "collection_method": "API",
        "brand": brand,
        "model": model_name,
        "model_key": model_key,
        "listing_title": "",
        "year": year,
        "mileage_km": parse_intish(item.get("Mileage")),
        "price_original": price * 10_000,
        "currency": "KRW",
        "link": f"https://fem.encar.com/cars/detail/{vehicle_id}",
        "engine_cc": None,
        "power_hp": None,
        "fuel_type": normalize_fuel_type(item.get("FuelType")),
        "transmission": normalize_transmission(item.get("Transmission")),
        "spec_source": None,
    }
    row["listing_title"] = build_clean_title(row["brand"], row["model"], row["year"], row["fuel_type"], row["transmission"])
    engine_cc, power_hp, spec_source = infer_specs_from_text(pd.Series(row))
    row["engine_cc"] = engine_cc
    row["power_hp"] = power_hp
    row["spec_source"] = spec_source
    return row


def load_korea_api_data(session: requests.Session, *, force_refresh: bool = True) -> pd.DataFrame:
    if not force_refresh:
        cached = load_cache("KO")
        if cached is not None and len(cached) >= KOREA_TARGET_ROWS:
            return cached

    cache_df = load_cache("KO")
    try:
        rows: list[dict[str, Any]] = []
        seen_links: set[str] = set()
        stale_pages = 0

        for page in range(KOREA_MAX_PAGES):
            before = len(rows)
            offset = page * ENCAR_PAGE_SIZE
            response = fetch_page(
                session,
                "https://api.encar.com/search/car/list/general",
                pause=0.08,
                params={
                    "count": "true",
                    "q": "(And.Hidden.N._.CarType.Y.)",
                    "sr": f"|ModifiedDate|{offset}|{ENCAR_PAGE_SIZE}",
                },
            )
            items = response.json().get("SearchResults", [])
            if not items:
                break

            for item in items:
                row = parse_encar_listing(item)
                if row is None or row["link"] in seen_links:
                    continue
                seen_links.add(row["link"])
                rows.append(row)

            if len(rows) == before:
                stale_pages += 1
            else:
                stale_pages = 0

            if len(rows) >= KOREA_TARGET_ROWS or stale_pages >= 8:
                break

        korea_df = ensure_columns(pd.DataFrame(rows), BASE_COLUMNS).head(KOREA_TARGET_ROWS)
        if cache_df is not None and len(cache_df) > len(korea_df):
            korea_df = cache_df
        if not korea_df.empty:
            save_cache(korea_df, "KO")
        return korea_df
    except Exception:
        if cache_df is not None:
            logger.warning("Korea API is unavailable, cached data is used")
            return cache_df
        raise
