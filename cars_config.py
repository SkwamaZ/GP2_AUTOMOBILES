from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    model_key: str
    brand: str
    model: str
    api_make: str
    api_model: str
    autoscout_url: str
    asia_url: str | None = None


@dataclass(frozen=True)
class RussiaCityConfig:
    city_id: str
    city_name: str
    city_slug: str


MARKET_NAMES_EN = {
    "RU": "Russia",
    "EU": "Europe",
    "KO": "Korea",
    "AS": "Asia",
}

MARKET_NAMES_RU = {
    "RU": "Россия",
    "EU": "Европа",
    "KO": "Корея",
    "AS": "Азия",
}

BASE_COLUMNS = [
    "market",
    "market_name",
    "source_portal",
    "collection_method",
    "brand",
    "model",
    "model_key",
    "listing_title",
    "year",
    "mileage_km",
    "price_original",
    "currency",
    "link",
    "engine_cc",
    "power_hp",
    "fuel_type",
    "transmission",
    "spec_source",
]

IMPORT_RULES = {
    "RU": {"fee_rate": 0.00, "logistics_rub": 0, "broker_rub": 0},
    "EU": {"fee_rate": 0.33, "logistics_rub": 250_000, "broker_rub": 120_000},
    "KO": {"fee_rate": 0.30, "logistics_rub": 350_000, "broker_rub": 120_000},
    "AS": {"fee_rate": 0.30, "logistics_rub": 350_000, "broker_rub": 120_000},
}

MODEL_CONFIGS: tuple[ModelConfig, ...] = (
    ModelConfig(
        model_key="BMW X5",
        brand="BMW",
        model="X5",
        api_make="BMW",
        api_model="X5",
        autoscout_url="https://www.autoscout24.com/lst/bmw/x5",
        asia_url="https://www.tc-v.com/used_car/bmw/x5",
    ),
    ModelConfig(
        model_key="BMW X7",
        brand="BMW",
        model="X7",
        api_make="BMW",
        api_model="X7",
        autoscout_url="https://www.autoscout24.com/lst/bmw/x7",
        asia_url="https://www.tc-v.com/used_car/bmw/x7",
    ),
    ModelConfig(
        model_key="Toyota Alphard",
        brand="Toyota",
        model="Alphard",
        api_make="Toyota",
        api_model="Alphard",
        autoscout_url="https://www.autoscout24.com/lst/toyota/alphard",
        asia_url="https://www.tc-v.com/used_car/toyota/alphard",
    ),
    ModelConfig(
        model_key="Porsche Panamera",
        brand="Porsche",
        model="Panamera",
        api_make="Porsche",
        api_model="Panamera",
        autoscout_url="https://www.autoscout24.com/lst/porsche/panamera",
        asia_url="https://www.tc-v.com/used_car/porsche/panamera",
    ),
    ModelConfig(
        model_key="Porsche Cayenne",
        brand="Porsche",
        model="Cayenne",
        api_make="Porsche",
        api_model="Cayenne",
        autoscout_url="https://www.autoscout24.com/lst/porsche/cayenne",
        asia_url="https://www.tc-v.com/used_car/porsche/cayenne",
    ),
    ModelConfig(
        model_key="Volkswagen Tiguan",
        brand="Volkswagen",
        model="Tiguan",
        api_make="Volkswagen",
        api_model="Tiguan",
        autoscout_url="https://www.autoscout24.com/lst/volkswagen/tiguan",
        asia_url="https://www.tc-v.com/used_car/volkswagen/tiguan",
    ),
    ModelConfig(
        model_key="Audi Q5",
        brand="Audi",
        model="Q5",
        api_make="Audi",
        api_model="Q5",
        autoscout_url="https://www.autoscout24.com/lst/audi/q5",
        asia_url="https://www.tc-v.com/used_car/audi/q5",
    ),
    ModelConfig(
        model_key="Audi Q7",
        brand="Audi",
        model="Q7",
        api_make="Audi",
        api_model="Q7",
        autoscout_url="https://www.autoscout24.com/lst/audi/q7",
        asia_url="https://www.tc-v.com/used_car/audi/q7",
    ),
    ModelConfig(
        model_key="Toyota Camry",
        brand="Toyota",
        model="Camry",
        api_make="Toyota",
        api_model="Camry",
        autoscout_url="https://www.autoscout24.com/lst/toyota/camry",
        asia_url="https://www.tc-v.com/used_car/toyota/camry",
    ),
    ModelConfig(
        model_key="Kia Sorento",
        brand="Kia",
        model="Sorento",
        api_make="Kia",
        api_model="Sorento",
        autoscout_url="https://www.autoscout24.com/lst/kia/sorento",
        asia_url="https://www.tc-v.com/used_car/kia/sorento",
    ),
    ModelConfig(
        model_key="Kia Picanto",
        brand="Kia",
        model="Picanto",
        api_make="Kia",
        api_model="Picanto",
        autoscout_url="https://www.autoscout24.com/lst/kia/picanto",
        asia_url="https://www.tc-v.com/used_car/kia/picanto",
    ),
    ModelConfig(
        model_key="Kia Soul",
        brand="Kia",
        model="Soul",
        api_make="Kia",
        api_model="Soul",
        autoscout_url="https://www.autoscout24.com/lst/kia/soul",
        asia_url="https://www.tc-v.com/used_car/kia/soul",
    ),
    ModelConfig(
        model_key="Kia Carnival",
        brand="Kia",
        model="Carnival",
        api_make="Kia",
        api_model="Carnival",
        autoscout_url="https://www.autoscout24.com/lst/kia/carnival",
        asia_url="https://www.tc-v.com/used_car/kia/carnival",
    ),
    ModelConfig(
        model_key="Hyundai Tucson",
        brand="Hyundai",
        model="Tucson",
        api_make="Hyundai",
        api_model="Tucson",
        autoscout_url="https://www.autoscout24.com/lst/hyundai/tucson",
        asia_url="https://www.tc-v.com/used_car/hyundai/tucson",
    ),
    ModelConfig(
        model_key="Skoda Kodiaq",
        brand="Skoda",
        model="Kodiaq",
        api_make="Skoda",
        api_model="Kodiaq",
        autoscout_url="https://www.autoscout24.com/lst/skoda/kodiaq",
        asia_url="https://www.tc-v.com/used_car/skoda/kodiaq",
    ),
)

MODEL_CONFIG_BY_KEY = {item.model_key: item for item in MODEL_CONFIGS}
TARGET_MODEL_KEYS = tuple(item.model_key for item in MODEL_CONFIGS)

RUSSIA_CITY_CONFIGS: tuple[RussiaCityConfig, ...] = (
    RussiaCityConfig("576d0612d53f3d80945f8b5d", "Moscow", "moskva"),
    RussiaCityConfig("576d0612d53f3d80945f8b5e", "Saint Petersburg", "sankt-peterburg"),
    RussiaCityConfig("576d0618d53f3d80945f964e", "Yekaterinburg", "ekaterinburg"),
    RussiaCityConfig("576d0616d53f3d80945f93b6", "Novosibirsk", "novosibirsk"),
    RussiaCityConfig("576d0615d53f3d80945f902c", "Krasnodar", "krasnodar"),
    RussiaCityConfig("576d0615d53f3d80945f9112", "Krasnoyarsk", "krasnoyarsk"),
    RussiaCityConfig("576d061ad53f3d80945f992e", "Chelyabinsk", "chelyabinsk"),
    RussiaCityConfig("576d0619d53f3d80945f9864", "Tyumen", "tyumen"),
    RussiaCityConfig("576d0613d53f3d80945f8c72", "Ufa", "ufa"),
    RussiaCityConfig("576d0617d53f3d80945f952c", "Rostov-on-Don", "rostov-na-donu"),
    RussiaCityConfig("576d0618d53f3d80945f97a5", "Kazan", "kazan"),
    RussiaCityConfig("576d0617d53f3d80945f9482", "Perm", "perm"),
    RussiaCityConfig("576d0618d53f3d80945f95ae", "Samara", "samara"),
    RussiaCityConfig("576d0616d53f3d80945f934b", "Nizhny Novgorod", "nizhniy_novgorod"),
    RussiaCityConfig("576d0619d53f3d80945f98d1", "Khabarovsk", "habarovsk"),
    RussiaCityConfig("576d0617d53f3d80945f93e8", "Omsk", "omsk"),
    RussiaCityConfig("576d0618d53f3d80945f95ed", "Saratov", "saratov"),
    RussiaCityConfig("576d0619d53f3d80945f9805", "Tomsk", "tomsk"),
    RussiaCityConfig("576d0614d53f3d80945f8db8", "Voronezh", "voronezh"),
    RussiaCityConfig("576d0613d53f3d80945f8d64", "Volgograd", "volgograd"),
)

SOURCE_HINTS = {
    "BMW X5": {"engine_cc": 2993, "power_hp": 286},
    "BMW X7": {"engine_cc": 2998, "power_hp": 340},
    "Toyota Alphard": {"engine_cc": 2487, "power_hp": 250},
    "Porsche Panamera": {"engine_cc": 2894, "power_hp": 330},
    "Porsche Cayenne": {"engine_cc": 2995, "power_hp": 470},
    "Volkswagen Tiguan": {"engine_cc": 1968, "power_hp": 150},
    "Audi Q5": {"engine_cc": 1984, "power_hp": 249},
    "Audi Q7": {"engine_cc": 2995, "power_hp": 340},
    "Toyota Camry": {"engine_cc": 2487, "power_hp": 204},
    "Kia Sorento": {"engine_cc": 2497, "power_hp": 281},
    "Kia Picanto": {"engine_cc": 998, "power_hp": 67},
    "Kia Soul": {"engine_cc": 1591, "power_hp": 128},
    "Kia Carnival": {"engine_cc": 2199, "power_hp": 200},
    "Hyundai Tucson": {"engine_cc": 1598, "power_hp": 180},
    "Skoda Kodiaq": {"engine_cc": 1984, "power_hp": 180},
}

UTIL_FEE_2026 = [
    {"max_engine_cc": 999, "bands": [{"max_hp": float("inf"), "under_3": 180_200, "over_3": 460_000}]},
    {
        "max_engine_cc": 1_999,
        "bands": [
            {"max_hp": 160, "under_3": 800_800, "over_3": 1_408_800},
            {"max_hp": 190, "under_3": 900_000, "over_3": 1_492_800},
            {"max_hp": 220, "under_3": 952_800, "over_3": 1_584_000},
            {"max_hp": 250, "under_3": 1_010_400, "over_3": 1_677_600},
            {"max_hp": 280, "under_3": 1_142_400, "over_3": 1_838_400},
            {"max_hp": 310, "under_3": 1_291_200, "over_3": 2_011_200},
            {"max_hp": 340, "under_3": 1_459_200, "over_3": 2_203_200},
            {"max_hp": 370, "under_3": 1_663_200, "over_3": 2_412_000},
            {"max_hp": 400, "under_3": 1_896_000, "over_3": 2_640_000},
            {"max_hp": 430, "under_3": 2_160_000, "over_3": 2_892_000},
            {"max_hp": 460, "under_3": 2_464_800, "over_3": 3_168_000},
            {"max_hp": 500, "under_3": 2_808_000, "over_3": 3_468_000},
            {"max_hp": float("inf"), "under_3": 3_201_600, "over_3": 3_796_800},
        ],
    },
    {
        "max_engine_cc": 2_999,
        "bands": [
            {"max_hp": 160, "under_3": 2_250_400, "over_3": 3_407_200},
            {"max_hp": 190, "under_3": 2_306_800, "over_3": 3_456_000},
            {"max_hp": 220, "under_3": 2_364_000, "over_3": 3_501_600},
            {"max_hp": 250, "under_3": 2_402_400, "over_3": 3_552_000},
            {"max_hp": 280, "under_3": 2_520_000, "over_3": 3_660_000},
            {"max_hp": 310, "under_3": 2_620_800, "over_3": 3_770_400},
            {"max_hp": 340, "under_3": 2_726_400, "over_3": 3_873_600},
            {"max_hp": 370, "under_3": 2_834_400, "over_3": 3_981_600},
            {"max_hp": 400, "under_3": 2_949_600, "over_3": 4_094_400},
            {"max_hp": 430, "under_3": 3_067_200, "over_3": 4_209_600},
            {"max_hp": 460, "under_3": 3_189_600, "over_3": 4_327_200},
            {"max_hp": 500, "under_3": 3_316_800, "over_3": 4_447_200},
            {"max_hp": float("inf"), "under_3": 3_448_800, "over_3": 4_572_000},
        ],
    },
    {
        "max_engine_cc": 3_499,
        "bands": [
            {"max_hp": 160, "under_3": 2_584_000, "over_3": 3_956_200},
            {"max_hp": 190, "under_3": 2_635_200, "over_3": 4_000_800},
            {"max_hp": 220, "under_3": 2_688_000, "over_3": 4_044_000},
            {"max_hp": 250, "under_3": 2_743_200, "over_3": 4_087_200},
            {"max_hp": 280, "under_3": 2_810_400, "over_3": 4_144_800},
            {"max_hp": 310, "under_3": 2_880_000, "over_3": 4_248_000},
            {"max_hp": 340, "under_3": 3_038_400, "over_3": 4_356_000},
            {"max_hp": 370, "under_3": 3_206_400, "over_3": 4_485_600},
            {"max_hp": 400, "under_3": 3_384_000, "over_3": 4_620_000},
            {"max_hp": 430, "under_3": 3_568_800, "over_3": 4_759_200},
            {"max_hp": 460, "under_3": 3_765_600, "over_3": 4_900_800},
            {"max_hp": 500, "under_3": 3_972_000, "over_3": 5_049_600},
            {"max_hp": float("inf"), "under_3": 4_190_400, "over_3": 5_200_800},
        ],
    },
    {
        "max_engine_cc": float("inf"),
        "bands": [
            {"max_hp": 160, "under_3": 3_290_600, "over_3": 4_325_800},
            {"max_hp": 190, "under_3": 3_345_600, "over_3": 4_389_600},
            {"max_hp": 220, "under_3": 3_403_200, "over_3": 4_456_800},
            {"max_hp": 250, "under_3": 3_460_800, "over_3": 4_524_000},
            {"max_hp": 280, "under_3": 3_530_400, "over_3": 4_627_200},
            {"max_hp": 310, "under_3": 3_600_000, "over_3": 4_732_800},
            {"max_hp": 340, "under_3": 3_727_200, "over_3": 4_992_000},
            {"max_hp": 370, "under_3": 3_857_600, "over_3": 5_268_000},
            {"max_hp": 400, "under_3": 3_993_600, "over_3": 5_558_400},
            {"max_hp": 430, "under_3": 4_132_800, "over_3": 5_863_200},
            {"max_hp": 460, "under_3": 4_276_800, "over_3": 6_187_200},
            {"max_hp": 500, "under_3": 4_425_600, "over_3": 6_528_000},
            {"max_hp": float("inf"), "under_3": 4_581_600, "over_3": 6_885_600},
        ],
    },
]
