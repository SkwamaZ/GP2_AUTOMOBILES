from __future__ import annotations

import math
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
LOG_DIR = PROJECT_DIR / "logs"

CACHE_FILES = {
    "RU": PROJECT_DIR / "russia_cache.csv",
    "EU": PROJECT_DIR / "europe_cache.csv",
    "KO": PROJECT_DIR / "korea_cache.csv",
    "AS": PROJECT_DIR / "asia_cache.csv",
}

OUTPUT_ALL_CARS = PROJECT_DIR / "cars_all.csv"
OUTPUT_COMPARISON = PROJECT_DIR / "comparison_result.csv"
OUTPUT_API_SPECS = PROJECT_DIR / "vehicle_specs_api_cache.csv"
OUTPUT_API_DEMO = PROJECT_DIR / "api_demo_requests.csv"

AUTOSCOUT_PAGE_SIZE = 100
EU_ROWS_PER_MODEL = 420
EU_MAX_PAGES_PER_MODEL = math.ceil(EU_ROWS_PER_MODEL / AUTOSCOUT_PAGE_SIZE)

AUTO_RU_ROWS_PER_PAGE = 37
RUSSIA_TARGET_ROWS = 5_500
RUSSIA_MAX_PAGES = 450
RUSSIA_MODEL_MAX_PAGES = 10

ENCAR_PAGE_SIZE = 100
KOREA_TARGET_ROWS = 5_000
KOREA_MAX_PAGES = 80

TCV_PAGE_SIZE = 25
ASIA_TARGET_ROWS = 5_000
ASIA_MAX_PAGES = math.ceil(ASIA_TARGET_ROWS / TCV_PAGE_SIZE) + 10
