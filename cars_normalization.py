from __future__ import annotations

import re

import pandas as pd

from cars_config import MARKET_NAMES_EN, MODEL_CONFIG_BY_KEY, TARGET_MODEL_KEYS
from cars_text import build_clean_title, canonical_key, english_title, normalize_brand, normalize_fuel_type, normalize_transmission


MODEL_ALIASES = {
    "BMW X5": ("bmw x5", "x5"),
    "BMW X7": ("bmw x7", "x7"),
    "Toyota Alphard": ("toyota alphard", "alphard", "alpadeu", "vellfire", "belpaieo"),
    "Porsche Panamera": ("porsche panamera", "panamera"),
    "Porsche Cayenne": ("porsche cayenne", "cayenne"),
    "Volkswagen Tiguan": ("volkswagen tiguan", "tiguan"),
    "Audi Q5": ("audi q5", "q5"),
    "Audi Q7": ("audi q7", "q7"),
    "Toyota Camry": ("toyota camry", "camry", "kaemri"),
    "Kia Sorento": ("kia sorento", "sorento", "ssorento"),
    "Kia Picanto": ("kia picanto", "picanto", "morning", "moning"),
    "Kia Soul": ("kia soul", "soul", "ssoul"),
    "Kia Carnival": ("kia carnival", "carnival", "kanibal"),
    "Hyundai Tucson": ("hyundai tucson", "tucson", "tussan"),
    "Skoda Kodiaq": ("skoda kodiaq", "kodiaq", "kodiak"),
}


def normalize_model_key(
    brand: str | None,
    model: str | None,
    listing_title: str | None = None,
    current_model_key: str | None = None,
) -> str:
    if current_model_key in MODEL_CONFIG_BY_KEY:
        return str(current_model_key)

    raw_text = " ".join(part for part in [brand or "", model or "", listing_title or ""] if part)
    text = canonical_key(raw_text)

    for model_key, aliases in MODEL_ALIASES.items():
        if any(re.search(rf"(^|\s){re.escape(alias)}($|\s)", text) for alias in aliases):
            return model_key

    clean_brand = normalize_brand(brand)
    clean_model = english_title(model)
    if clean_brand and clean_model:
        return f"{clean_brand} {clean_model}"
    if clean_model:
        return clean_model
    return clean_brand


def standardize_vehicle_rows(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["market_name"] = result["market"].map(MARKET_NAMES_EN)
    result["brand"] = result["brand"].map(normalize_brand)
    result["model"] = result["model"].map(english_title)
    result["fuel_type"] = result["fuel_type"].map(normalize_fuel_type)
    result["transmission"] = result["transmission"].map(normalize_transmission)
    result["model_key"] = result.apply(
        lambda row: normalize_model_key(
            row.get("brand"),
            row.get("model"),
            row.get("listing_title"),
            row.get("model_key"),
        ),
        axis=1,
    )

    for model_key in TARGET_MODEL_KEYS:
        config = MODEL_CONFIG_BY_KEY[model_key]
        mask = result["model_key"] == model_key
        result.loc[mask, "brand"] = config.brand
        result.loc[mask, "model"] = config.model

    result["listing_title"] = result.apply(
        lambda row: build_clean_title(
            row["brand"],
            row["model"],
            row.get("year"),
            row.get("fuel_type"),
            row.get("transmission"),
        ),
        axis=1,
    )
    return result
