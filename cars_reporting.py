from __future__ import annotations

from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from cars_config import MARKET_NAMES_RU


METHOD_NAMES_RU = {
    "Scraping": "Скрапинг",
    "API": "API",
}

MARKET_NAME_EN_TO_RU = {
    "Russia": MARKET_NAMES_RU["RU"],
    "Europe": MARKET_NAMES_RU["EU"],
    "Korea": MARKET_NAMES_RU["KO"],
    "Asia": MARKET_NAMES_RU["AS"],
}


def market_name_ru(series: pd.Series) -> pd.Series:
    return series.map(MARKET_NAME_EN_TO_RU).fillna(series)


def set_plot_style() -> None:
    sns.set_theme(style="whitegrid", palette="Set2")
    plt.rcParams["figure.figsize"] = (12, 6)
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["font.family"] = "DejaVu Sans"


def market_overview(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["market_name", "source_portal", "collection_method"], dropna=False)
        .agg(
            rows=("link", "count"),
            median_price_rub=("price_rub", "median"),
            median_year=("year", "median"),
            median_mileage_km=("mileage_km", "median"),
        )
        .reset_index()
        .sort_values(["rows", "median_price_rub"], ascending=[False, False])
    )


def brand_overview(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    return (
        df.groupby("brand", dropna=False)
        .agg(
            rows=("link", "count"),
            median_price_rub=("price_rub", "median"),
            median_year=("year", "median"),
        )
        .reset_index()
        .sort_values(["rows", "median_price_rub"], ascending=[False, False])
        .head(top_n)
    )


def model_overview(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    return (
        df.groupby("model_key", dropna=False)
        .agg(
            rows=("link", "count"),
            median_price_rub=("price_rub", "median"),
            median_year=("year", "median"),
        )
        .reset_index()
        .sort_values(["rows", "median_price_rub"], ascending=[False, False])
        .head(top_n)
    )


def missingness_summary(df: pd.DataFrame) -> pd.DataFrame:
    stats = pd.DataFrame(
        {
            "column": df.columns,
            "missing_rows": df.isna().sum().values,
            "missing_share": (df.isna().mean().values * 100).round(2),
        }
    )
    return stats.sort_values(["missing_rows", "column"], ascending=[False, True]).reset_index(drop=True)


def outlier_summary(df: pd.DataFrame, columns: Iterable[str] = ("price_rub", "mileage_km", "year")) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for column in columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = ((series < lower) | (series > upper)).sum()
        rows.append(
            {
                "column": column,
                "q1": round(float(q1), 2),
                "q3": round(float(q3), 2),
                "iqr": round(float(iqr), 2),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2),
                "outlier_rows": int(outliers),
                "outlier_share": round(float(outliers / len(series) * 100), 2),
            }
        )
    return pd.DataFrame(rows)


def plot_market_counts(df: pd.DataFrame) -> None:
    counts = market_name_ru(df["market_name"]).value_counts().sort_values(ascending=False)
    ax = counts.plot(kind="bar", color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"])
    ax.set_title("Количество объявлений по рынкам")
    ax.set_xlabel("")
    ax.set_ylabel("Количество объявлений")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()


def plot_source_mix(df: pd.DataFrame) -> None:
    data = df.copy()
    data["market_name"] = market_name_ru(data["market_name"])
    data["collection_method"] = data["collection_method"].map(METHOD_NAMES_RU).fillna(data["collection_method"])
    table = (
        data.groupby(["market_name", "collection_method"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    table.plot(kind="bar", stacked=True, figsize=(12, 6))
    plt.title("Способы сбора данных по рынкам")
    plt.xlabel("")
    plt.ylabel("Количество объявлений")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()


def plot_brand_counts(df: pd.DataFrame, top_n: int = 12) -> None:
    top_brands = df["brand"].value_counts().head(top_n).sort_values()
    ax = top_brands.plot(kind="barh", color="#4C72B0")
    ax.set_title("Самые частые марки в общем датасете")
    ax.set_xlabel("Количество объявлений")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.show()


def plot_market_price_box(df: pd.DataFrame) -> None:
    subset = df[df["price_rub"].notna()].copy()
    subset["price_mln_rub"] = subset["price_rub"] / 1_000_000
    subset["market_name"] = market_name_ru(subset["market_name"])
    sns.boxplot(data=subset, x="market_name", y="price_mln_rub")
    plt.title("Распределение цен по рынкам")
    plt.xlabel("")
    plt.ylabel("Цена, млн руб.")
    plt.tight_layout()
    plt.show()


def plot_year_distribution(df: pd.DataFrame) -> None:
    subset = df[df["year"].notna()].copy()
    subset["market_name"] = market_name_ru(subset["market_name"])
    sns.histplot(data=subset, x="year", hue="market_name", element="step", bins=18, stat="count", common_norm=False)
    plt.title("Распределение годов выпуска по рынкам")
    plt.xlabel("Год выпуска")
    plt.ylabel("Количество объявлений")
    plt.tight_layout()
    plt.show()


def plot_mileage_distribution(df: pd.DataFrame) -> None:
    subset = df[df["mileage_km"].notna()].copy()
    if subset.empty:
        return
    subset["mileage_th_km"] = subset["mileage_km"] / 1_000
    subset["market_name"] = market_name_ru(subset["market_name"])
    sns.histplot(data=subset, x="mileage_th_km", hue="market_name", element="step", bins=30, stat="count", common_norm=False)
    plt.title("Распределение пробега по рынкам")
    plt.xlabel("Пробег, тыс. км")
    plt.ylabel("Количество объявлений")
    plt.tight_layout()
    plt.show()


def plot_target_model_heatmap(comparison_df: pd.DataFrame) -> None:
    if comparison_df.empty:
        return
    pivot = comparison_df.pivot_table(
        index="model_key",
        columns="foreign_market",
        values="price_gap_rub",
        aggfunc="median",
    ) / 1_000_000
    pivot = pivot.rename(columns={"Europe": "Европа", "Korea": "Корея", "Asia": "Азия"})
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn_r", center=0)
    plt.title("Разница с Россией после ввоза, млн руб.")
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.show()


def plot_outlier_boxes(df: pd.DataFrame) -> None:
    subset = df[df["estimated_total_rub"].notna()].copy()
    subset["estimated_total_mln_rub"] = subset["estimated_total_rub"] / 1_000_000
    subset["market_name"] = market_name_ru(subset["market_name"])
    sns.boxplot(data=subset, x="market_name", y="estimated_total_mln_rub")
    plt.title("Итоговая цена с учетом ввоза по рынкам")
    plt.xlabel("")
    plt.ylabel("Итоговая цена, млн руб.")
    plt.tight_layout()
    plt.show()


def summarize_comparison(comparison_df: pd.DataFrame) -> str:
    if comparison_df.empty:
        return "Для итогового сравнения пока не хватает сопоставимых моделей между рынками."

    best_row = comparison_df.iloc[0]
    worst_row = comparison_df.iloc[-1]
    if best_row["price_gap_rub"] < 0:
        best_line = (
            f"Самый выгодный импортный сценарий сейчас у модели {best_row['model_key']} из рынка "
            f"{best_row['foreign_market']}: после ввоза медианная цена ниже российского рынка "
            f"примерно на {abs(int(best_row['price_gap_rub'])):,} руб.".replace(",", " ")
        )
    else:
        best_line = (
            f"Даже лучший вариант импорта пока не дешевле России. Минимальная переплата у модели "
            f"{best_row['model_key']} из рынка {best_row['foreign_market']} и составляет "
            f"{int(best_row['price_gap_rub']):,} руб.".replace(",", " ")
        )

    worst_line = (
        f"Самый слабый вариант импорта у модели {worst_row['model_key']} из рынка "
        f"{worst_row['foreign_market']}: разница с Россией составляет "
        f"{abs(int(worst_row['price_gap_rub'])):,} руб.".replace(",", " ")
    )
    return best_line + "\n" + worst_line


def business_summary(df: pd.DataFrame, comparison_df: pd.DataFrame) -> list[str]:
    summary: list[str] = []
    market_table = market_overview(df)
    biggest_market = market_table.sort_values("rows", ascending=False).iloc[0]
    summary.append(
        f"Самый большой пласт данных пришёл из рынка {biggest_market['market_name']}: "
        f"{int(biggest_market['rows'])} объявлений."
    )

    cheapest_market = (
        df.groupby("market_name")["estimated_total_rub"]
        .median()
        .sort_values()
        .reset_index()
        .iloc[0]
    )
    summary.append(
        f"Самая низкая медианная итоговая цена сейчас у рынка {cheapest_market['market_name']}."
    )

    top_brand = brand_overview(df, top_n=1).iloc[0]
    summary.append(
        f"Самая заметная марка в объединённой выборке — {top_brand['brand']}, "
        f"по ней собрали {int(top_brand['rows'])} объявлений."
    )

    if not comparison_df.empty:
        best_row = comparison_df.iloc[0]
        decision = "выглядит выгоднее ввоза" if best_row["price_gap_rub"] < 0 else "пока выгоднее покупать внутри России"
        summary.append(
            f"По сравнительной части самый сильный кейс — {best_row['model_key']} из рынка "
            f"{best_row['foreign_market']}: он {decision}."
        )

    return summary
