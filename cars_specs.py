from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd

from cars_config import SOURCE_HINTS, UTIL_FEE_2026
from cars_http import clean_number


REFERENCE_YEAR = datetime.now().year
REDUCED_PERSONAL_UTIL_FEE = {"under_3": 3_400, "over_3": 5_200}


def infer_specs_from_text(row: pd.Series) -> tuple[int | None, int | None, str | None]:
    engine_cc = row.get("engine_cc")
    power_hp = row.get("power_hp")
    spec_source = row.get("spec_source")

    text = " ".join(str(row.get(column) or "") for column in ["listing_title", "brand", "model"]).lower()

    if pd.notna(engine_cc) and pd.notna(power_hp):
        return int(engine_cc), int(power_hp), spec_source or "source"

    liters_match = re.search(r"\b(\d(?:[.,]\d)?)\s*(?:l|tdi|tsi|gdi|t-gdi|hev|phev)?\b", text)
    if pd.isna(engine_cc) and liters_match:
        engine_cc = int(round(float(liters_match.group(1).replace(",", ".")) * 1000))
        spec_source = "title_regex"

    current_power = clean_number(power_hp)
    if pd.isna(power_hp) or (current_power is not None and current_power < 30):
        power_match = re.search(r"\b(\d{2,4})\s*(?:hp|ps)\b", text)
        if power_match:
            power_hp = int(power_match.group(1))
            spec_source = spec_source or "title_regex"

    if pd.isna(engine_cc) or pd.isna(power_hp):
        hint = SOURCE_HINTS.get(row.get("model_key"))
        if hint:
            engine_cc = engine_cc if pd.notna(engine_cc) else hint["engine_cc"]
            power_hp = power_hp if pd.notna(power_hp) else hint["power_hp"]
            spec_source = "model_hint"

    engine_cc_value = int(engine_cc) if pd.notna(engine_cc) else None
    power_hp_value = int(power_hp) if pd.notna(power_hp) else None
    return engine_cc_value, power_hp_value, spec_source


def age_bucket(year: Any) -> str:
    year_value = clean_number(year)
    if year_value is None:
        return "over_3"
    return "under_3" if year_value >= REFERENCE_YEAR - 2 else "over_3"


def estimate_util_fee_rub(engine_cc: Any, power_hp: Any, year: Any) -> int:
    engine_value = clean_number(engine_cc)
    if engine_value is None:
        return 0

    power_value = clean_number(power_hp)
    bucket = age_bucket(year)
    if power_value is None:
        power_value = 160
    if engine_value <= 3_000 and power_value <= 160:
        return REDUCED_PERSONAL_UTIL_FEE[bucket]

    for engine_rule in UTIL_FEE_2026:
        if engine_value <= engine_rule["max_engine_cc"]:
            for power_rule in engine_rule["bands"]:
                if power_value <= power_rule["max_hp"]:
                    return int(power_rule[bucket])
    return 0


def representative_year(df: pd.DataFrame, model_key: str) -> int:
    model_years = df.loc[df["model_key"] == model_key, "year"].dropna()
    if model_years.empty:
        return REFERENCE_YEAR
    return int(round(model_years.median()))
