from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from cars_http import clean_number
from cars_specs import estimate_util_fee_rub

REFERENCE_YEAR = datetime.now().year


PERSONAL_IMPORT_OVERHEADS = {
    "RU": {"delivery_rub": 0, "certification_rub": 0, "broker_service_rub": 0},
    "EU": {"delivery_rub": 180_000, "certification_rub": 35_000, "broker_service_rub": 20_000},
    "KO": {"delivery_rub": 250_000, "certification_rub": 35_000, "broker_service_rub": 30_000},
    "AS": {"delivery_rub": 250_000, "certification_rub": 35_000, "broker_service_rub": 30_000},
}

# 2026 customs clearance fees by customs value.
CUSTOMS_CLEARANCE_FEES_2026 = [
    {"max_value_rub": 200_000, "fee_rub": 1_231},
    {"max_value_rub": 450_000, "fee_rub": 2_462},
    {"max_value_rub": 1_200_000, "fee_rub": 4_924},
    {"max_value_rub": 2_700_000, "fee_rub": 13_541},
    {"max_value_rub": 4_200_000, "fee_rub": 18_465},
    {"max_value_rub": 5_500_000, "fee_rub": 21_344},
    {"max_value_rub": 10_000_000, "fee_rub": 49_240},
    {"max_value_rub": float("inf"), "fee_rub": 73_860},
]

# Personal-use customs duty for passenger cars.
# For cars under 3 years the rate depends on customs value in EUR.
UNDER_3_CUSTOMS_DUTY = [
    {"max_price_eur": 8_500, "ad_valorem_rate": 0.54, "min_eur_per_cc": 2.5},
    {"max_price_eur": 16_700, "ad_valorem_rate": 0.48, "min_eur_per_cc": 3.5},
    {"max_price_eur": 42_300, "ad_valorem_rate": 0.48, "min_eur_per_cc": 5.5},
    {"max_price_eur": 84_500, "ad_valorem_rate": 0.48, "min_eur_per_cc": 7.5},
    {"max_price_eur": 169_000, "ad_valorem_rate": 0.48, "min_eur_per_cc": 15.0},
    {"max_price_eur": float("inf"), "ad_valorem_rate": 0.48, "min_eur_per_cc": 20.0},
]

# For cars 3-5 and 5+ years the duty is charged per cc.
FROM_3_TO_5_CUSTOMS_DUTY = [
    {"max_engine_cc": 1_000, "eur_per_cc": 1.5},
    {"max_engine_cc": 1_500, "eur_per_cc": 1.7},
    {"max_engine_cc": 1_800, "eur_per_cc": 2.5},
    {"max_engine_cc": 2_300, "eur_per_cc": 2.7},
    {"max_engine_cc": 3_000, "eur_per_cc": 3.0},
    {"max_engine_cc": float("inf"), "eur_per_cc": 3.6},
]

OVER_5_CUSTOMS_DUTY = [
    {"max_engine_cc": 1_000, "eur_per_cc": 3.0},
    {"max_engine_cc": 1_500, "eur_per_cc": 3.2},
    {"max_engine_cc": 1_800, "eur_per_cc": 3.5},
    {"max_engine_cc": 2_300, "eur_per_cc": 4.8},
    {"max_engine_cc": 3_000, "eur_per_cc": 5.0},
    {"max_engine_cc": float("inf"), "eur_per_cc": 5.7},
]


def age_years(year: Any, reference_year: int = REFERENCE_YEAR) -> int | None:
    year_value = clean_number(year)
    if year_value is None:
        return None
    return max(reference_year - year_value, 0)


def safe_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def customs_age_bucket(year: Any) -> str:
    vehicle_age = age_years(year)
    if vehicle_age is None:
        return "from_3_to_5"
    if vehicle_age < 3:
        return "under_3"
    if vehicle_age <= 5:
        return "from_3_to_5"
    return "over_5"


def estimate_customs_clearance_rub(customs_value_rub: Any) -> int:
    value = safe_float(customs_value_rub)
    if value <= 0:
        return 0

    for band in CUSTOMS_CLEARANCE_FEES_2026:
        if value <= band["max_value_rub"]:
            return band["fee_rub"]
    return 0


def estimate_customs_duty_rub(price_rub: Any, engine_cc: Any, year: Any, eur_rate: float) -> int:
    customs_value_rub = safe_float(price_rub)
    engine_value = clean_number(engine_cc)
    if customs_value_rub <= 0 or engine_value is None or eur_rate <= 0:
        return 0

    customs_value_eur = customs_value_rub / eur_rate
    bucket = customs_age_bucket(year)

    if bucket == "under_3":
        for rule in UNDER_3_CUSTOMS_DUTY:
            if customs_value_eur <= rule["max_price_eur"]:
                ad_valorem_eur = customs_value_eur * rule["ad_valorem_rate"]
                minimum_eur = engine_value * rule["min_eur_per_cc"]
                return int(round(max(ad_valorem_eur, minimum_eur) * eur_rate))
        return 0

    per_cc_rules = FROM_3_TO_5_CUSTOMS_DUTY if bucket == "from_3_to_5" else OVER_5_CUSTOMS_DUTY
    for rule in per_cc_rules:
        if engine_value <= rule["max_engine_cc"]:
            return int(round(engine_value * rule["eur_per_cc"] * eur_rate))
    return 0


def calculate_import_cost_components(row: dict[str, Any] | Any, eur_rate: float) -> dict[str, float | int]:
    market_code = row.get("market")
    price_rub = safe_float(row.get("price_rub"))
    if market_code == "RU" or price_rub <= 0:
        return {
            "price_eur": 0 if price_rub <= 0 else round(price_rub / eur_rate, 2),
            "fee_rate": 0.0,
            "delivery_rub": 0,
            "logistics_rub": 0,
            "customs_clearance_rub": 0,
            "certification_rub": 0,
            "broker_service_rub": 0,
            "broker_rub": 0,
            "customs_duty_rub": 0,
            "util_fee_rub": 0,
            "estimated_total_rub": round(price_rub),
        }

    market_costs = PERSONAL_IMPORT_OVERHEADS.get(market_code, PERSONAL_IMPORT_OVERHEADS["AS"])
    customs_duty_rub = estimate_customs_duty_rub(price_rub, row.get("engine_cc"), row.get("year"), eur_rate)
    customs_clearance_rub = estimate_customs_clearance_rub(price_rub)
    certification_rub = market_costs["certification_rub"]
    broker_service_rub = market_costs["broker_service_rub"]
    delivery_rub = market_costs["delivery_rub"]
    util_fee_rub = estimate_util_fee_rub(row.get("engine_cc"), row.get("power_hp"), row.get("year"))
    broker_rub = customs_clearance_rub + certification_rub + broker_service_rub
    estimated_total_rub = round(price_rub + customs_duty_rub + util_fee_rub + delivery_rub + broker_rub)
    fee_rate = round(customs_duty_rub / price_rub, 6) if price_rub > 0 else 0.0

    return {
        "price_eur": round(price_rub / eur_rate, 2),
        "fee_rate": fee_rate,
        "delivery_rub": delivery_rub,
        "logistics_rub": delivery_rub,
        "customs_clearance_rub": customs_clearance_rub,
        "certification_rub": certification_rub,
        "broker_service_rub": broker_service_rub,
        "broker_rub": broker_rub,
        "customs_duty_rub": customs_duty_rub,
        "util_fee_rub": util_fee_rub,
        "estimated_total_rub": estimated_total_rub,
    }
