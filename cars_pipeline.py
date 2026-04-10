from __future__ import annotations

from typing import Any

import pandas as pd

from cars_api import load_authenticated_specs, load_korea_api_data, run_api_key_demo
from cars_dataset import build_all_cars, build_comparison
from cars_http import build_session, format_rates_df, get_cbr_rates
from cars_logging import setup_logging
from cars_reporting import business_summary, summarize_comparison
from cars_sources import load_asia_data, load_europe_data, load_russia_data


def collect_market_data(*, force_refresh: bool = True) -> dict[str, Any]:
    setup_logging()
    session = build_session()
    rates = get_cbr_rates(session)

    korea_df = load_korea_api_data(session, force_refresh=force_refresh)
    russia_df = load_russia_data(session, force_refresh=force_refresh)
    europe_df = load_europe_data(session, force_refresh=force_refresh)
    asia_df = load_asia_data(session, force_refresh=force_refresh)

    foreign_for_api = pd.concat([korea_df, asia_df, europe_df], ignore_index=True)
    api_specs_df = load_authenticated_specs(session, foreign_for_api, force_refresh=force_refresh)
    api_demo_df = run_api_key_demo(session, foreign_for_api, requests_limit=5)

    return {
        "session": session,
        "rates": rates,
        "rates_df": format_rates_df(rates),
        "korea_df": korea_df,
        "russia_df": russia_df,
        "europe_df": europe_df,
        "asia_df": asia_df,
        "api_specs_df": api_specs_df,
        "api_demo_df": api_demo_df,
    }


def build_project_outputs(artifacts: dict[str, Any]) -> dict[str, Any]:
    all_cars = build_all_cars(
        artifacts["korea_df"],
        artifacts["russia_df"],
        artifacts["europe_df"],
        artifacts["rates"],
        artifacts["api_specs_df"],
        asia_df=artifacts["asia_df"],
    )
    comparison_df = build_comparison(all_cars)
    artifacts["all_cars"] = all_cars
    artifacts["comparison_df"] = comparison_df
    artifacts["business_summary"] = business_summary(all_cars, comparison_df)
    return artifacts


def run_pipeline(*, force_refresh: bool = True) -> dict[str, Any]:
    artifacts = collect_market_data(force_refresh=force_refresh)
    return build_project_outputs(artifacts)


if __name__ == "__main__":
    artifacts = run_pipeline(force_refresh=True)
    print("rates:", artifacts["rates_df"].to_dict()["rub_per_unit"])
    print(
        "rows:",
        {
            key: len(artifacts[key])
            for key in ["korea_df", "russia_df", "europe_df", "asia_df", "api_specs_df", "all_cars", "comparison_df"]
        },
    )
    print(summarize_comparison(artifacts["comparison_df"]))
