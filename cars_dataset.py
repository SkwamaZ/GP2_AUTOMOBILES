from __future__ import annotations

from typing import Any

import pandas as pd

from cars_config import MARKET_NAMES_EN, TARGET_MODEL_KEYS
from cars_import_costs import calculate_import_cost_components
from cars_normalization import standardize_vehicle_rows
from cars_paths import OUTPUT_ALL_CARS, OUTPUT_COMPARISON
from cars_specs import infer_specs_from_text


COMPARISON_COLUMNS = [
    "model_key",
    "foreign_market",
    "foreign_median_year",
    "foreign_rows",
    "russia_rows_matched",
    "foreign_median_price_rub",
    "imported_median_price_rub",
    "russia_median_price_rub",
    "price_gap_rub",
    "decision",
]


def safe_export_csv(df: pd.DataFrame, path) -> None:
    try:
        df.to_csv(path, index=False)
    except PermissionError:
        pass


def enrich_specs(all_cars: pd.DataFrame, api_specs_df: pd.DataFrame) -> pd.DataFrame:
    result = all_cars.copy()
    api_columns = [
        "api_engine_cc",
        "api_cylinders",
        "api_drive",
        "api_fuel_type",
        "api_class",
        "api_transmission",
        "api_source",
    ]

    if not api_specs_df.empty:
        merge_columns = ["model_key", *api_columns]
        result = result.merge(api_specs_df[merge_columns], on="model_key", how="left")
        missing_engine = result["engine_cc"].isna() & result["api_engine_cc"].notna()
        result.loc[missing_engine, "engine_cc"] = result.loc[missing_engine, "api_engine_cc"]
        result.loc[missing_engine, "spec_source"] = result.loc[missing_engine, "api_source"]

        missing_fuel = result["fuel_type"].isna() & result["api_fuel_type"].notna()
        missing_transmission = result["transmission"].isna() & result["api_transmission"].notna()
        result.loc[missing_fuel, "fuel_type"] = result.loc[missing_fuel, "api_fuel_type"]
        result.loc[missing_transmission, "transmission"] = result.loc[missing_transmission, "api_transmission"]
    else:
        for column in api_columns:
            result[column] = None

    inferred = result.apply(
        lambda row: pd.Series(
            infer_specs_from_text(row),
            index=["engine_cc", "power_hp", "spec_source"],
        ),
        axis=1,
    )
    result[["engine_cc", "power_hp", "spec_source"]] = inferred
    return result


def build_all_cars(
    korea_df: pd.DataFrame,
    russia_df: pd.DataFrame,
    europe_df: pd.DataFrame,
    rates: dict[str, float],
    api_specs_df: pd.DataFrame,
    *,
    asia_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frames = [frame for frame in [korea_df, russia_df, europe_df, asia_df] if frame is not None and not frame.empty]
    all_cars = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if all_cars.empty:
        return all_cars

    numeric_columns = ["year", "mileage_km", "price_original", "engine_cc", "power_hp"]
    for column in numeric_columns:
        all_cars[column] = pd.to_numeric(all_cars[column], errors="coerce")

    all_cars = standardize_vehicle_rows(all_cars)
    all_cars = enrich_specs(all_cars, api_specs_df)
    all_cars["rate_to_rub"] = all_cars["currency"].map(rates).fillna(1.0)
    all_cars["price_rub"] = (all_cars["price_original"] * all_cars["rate_to_rub"]).round(0)
    eur_rate = float(rates.get("EUR") or 1.0)
    import_components = all_cars.apply(
        lambda row: pd.Series(calculate_import_cost_components(row, eur_rate)),
        axis=1,
    )
    all_cars = pd.concat([all_cars, import_components], axis=1)

    all_cars["market_name"] = all_cars["market"].map(MARKET_NAMES_EN)
    all_cars = all_cars.sort_values(["market", "brand", "model", "year"], ascending=[True, True, True, False]).reset_index(drop=True)
    safe_export_csv(all_cars, OUTPUT_ALL_CARS)
    return all_cars


def build_comparison(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        comparison_df = pd.DataFrame(columns=COMPARISON_COLUMNS)
        safe_export_csv(comparison_df, OUTPUT_COMPARISON)
        return comparison_df

    comparison_rows: list[dict[str, Any]] = []
    russia = df[df["market"] == "RU"]
    foreign = df[df["market"] != "RU"]

    for model_key in TARGET_MODEL_KEYS:
        foreign_by_model = foreign[foreign["model_key"] == model_key]
        russian_by_model = russia[russia["model_key"] == model_key]
        if foreign_by_model.empty or russian_by_model.empty:
            continue

        for market_code in foreign_by_model["market"].dropna().unique():
            foreign_group = foreign_by_model[foreign_by_model["market"] == market_code]
            target_year = int(round(foreign_group["year"].dropna().median()))

            russian_match = russian_by_model.copy()
            russian_match["year_gap"] = (russian_match["year"] - target_year).abs()
            russian_match = russian_match.sort_values("year_gap").head(10)
            if russian_match.empty:
                continue

            imported_median = round(foreign_group["estimated_total_rub"].median())
            russian_median = round(russian_match["estimated_total_rub"].median())
            gap = round(imported_median - russian_median)
            comparison_rows.append(
                {
                    "model_key": model_key,
                    "foreign_market": MARKET_NAMES_EN[market_code],
                    "foreign_median_year": target_year,
                    "foreign_rows": len(foreign_group),
                    "russia_rows_matched": len(russian_match),
                    "foreign_median_price_rub": round(foreign_group["price_rub"].median()),
                    "imported_median_price_rub": imported_median,
                    "russia_median_price_rub": russian_median,
                    "price_gap_rub": gap,
                    "decision": "Import is cheaper" if gap < 0 else "Russia is cheaper",
                }
            )

    comparison_df = pd.DataFrame(comparison_rows, columns=COMPARISON_COLUMNS).sort_values("price_gap_rub").reset_index(drop=True)
    safe_export_csv(comparison_df, OUTPUT_COMPARISON)
    return comparison_df
