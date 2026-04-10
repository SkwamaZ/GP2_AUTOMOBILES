from __future__ import annotations

import math
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Iterable

import pandas as pd
import requests

from cars_config import BASE_COLUMNS
from cars_paths import CACHE_FILES, OUTPUT_ALL_CARS


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )
    return session


def clean_number(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return int(round(float(value)))

    text = str(value).strip()
    compact = re.sub(r"\s+", "", text.replace("\xa0", ""))
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", compact):
        return int(round(float(compact.replace(",", "."))))

    digits = "".join(char for char in compact if char.isdigit())
    return int(digits) if digits else None


def clean_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", ".")
    match = []
    dot_seen = False
    for char in text:
        if char.isdigit():
            match.append(char)
        elif char == "." and not dot_seen:
            match.append(char)
            dot_seen = True
        elif match:
            break
    cleaned = "".join(match)
    return float(cleaned) if cleaned and cleaned != "." else None


def ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            result[column] = None
    return result[list(columns)]


def fetch_page(
    session: requests.Session,
    url: str,
    *,
    pause: float = 0.15,
    timeout: int = 40,
    retry_on_429: bool = True,
    **kwargs: Any,
) -> requests.Response:
    response = session.get(url, timeout=timeout, **kwargs)
    time.sleep(pause)
    if response.status_code == 429 and retry_on_429:
        time.sleep(2.0)
        response = session.get(url, timeout=timeout, **kwargs)
        time.sleep(pause)
    response.raise_for_status()
    return response


def save_cache(df: pd.DataFrame, market_code: str) -> None:
    if df.empty:
        return
    ensure_columns(df, BASE_COLUMNS).to_csv(CACHE_FILES[market_code], index=False)


def load_cache(market_code: str) -> pd.DataFrame | None:
    path = CACHE_FILES[market_code]
    if path.exists():
        return ensure_columns(pd.read_csv(path), BASE_COLUMNS)

    if OUTPUT_ALL_CARS.exists():
        all_cars = pd.read_csv(OUTPUT_ALL_CARS)
        if "market" in all_cars.columns:
            part = all_cars[all_cars["market"] == market_code].copy()
            if not part.empty:
                part = ensure_columns(part, BASE_COLUMNS)
                part.to_csv(path, index=False)
                return part
    return None


def get_cbr_rates(session: requests.Session) -> dict[str, float]:
    response = fetch_page(session, "https://www.cbr.ru/scripts/XML_daily.asp", pause=0.05)
    root = ET.fromstring(response.content)
    rates = {"RUB": 1.0}
    for valute in root.findall("Valute"):
        code = valute.findtext("CharCode")
        nominal = int(valute.findtext("Nominal"))
        value = float(valute.findtext("Value").replace(",", "."))
        rates[code] = value / nominal
    return rates


def format_rates_df(rates: dict[str, float]) -> pd.DataFrame:
    ordered = ["RUB", "USD", "EUR", "KRW"]
    return pd.Series(rates, name="rub_per_unit").to_frame().reindex(ordered)
