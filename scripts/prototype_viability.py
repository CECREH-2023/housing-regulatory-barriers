#!/usr/bin/env python3
"""Create descriptive public-data tables for the housing regulatory barriers prototype."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
REPORTS = ROOT / "outputs" / "reports"


def pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{value:.1%}"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    panel_path = PROCESSED / "county_prototype_panel_2020_2025.csv"
    text_path = PROCESSED / "zoning_text_term_counts.csv"
    mhs_inventory_path = ROOT / "data" / "interim" / "mhs_workbook_inventory.csv"

    panel = pd.read_csv(panel_path, dtype={"geoid": str, "state_fips": str, "county_fips": str})
    text = pd.read_csv(text_path)
    mhs_inventory = pd.read_csv(mhs_inventory_path)

    latest_year = int(panel["year"].max())
    latest = panel[panel["year"] == latest_year].copy()

    summary = (
        panel.groupby(["state_abbr", "year"], as_index=False)
        .agg(
            counties=("geoid", "nunique"),
            total_permitted_units=("total_units", "sum"),
            one_unit_permitted_units=("one_unit_units", "sum"),
            multifamily_permitted_units=("multifamily_units", "sum"),
            median_permits_per_1000_housing_units=("permits_per_1000_housing_units", "median"),
            median_mobile_home_share=("mobile_home_share", "median"),
            median_risk_score=("RISK_SCORE", "median"),
        )
        .sort_values(["state_abbr", "year"])
    )
    summary.to_csv(TABLES / "state_year_permit_affordability_risk_summary.csv", index=False)

    top_mobile = (
        latest.sort_values("mobile_home_share", ascending=False)
        .loc[
            :,
            [
                "geoid",
                "NAME",
                "state_abbr",
                "county_name",
                "total_units",
                "permits_per_1000_housing_units",
                "acs_total_housing_units",
                "acs_mobile_home_units",
                "mobile_home_share",
                "RISK_SCORE",
                "RISK_RATNG",
                "SOVI_SCORE",
                "RESL_SCORE",
            ],
        ]
        .head(50)
    )
    top_mobile.to_csv(TABLES / f"top_mobile_home_share_counties_{latest_year}.csv", index=False)

    candidate = latest[
        (latest["mobile_home_share"] >= latest["mobile_home_share"].quantile(0.65))
        & (latest["RISK_SCORE"] >= latest["RISK_SCORE"].quantile(0.65))
    ].copy()
    candidate = candidate.sort_values(
        ["mobile_home_share", "RISK_SCORE", "permits_per_1000_housing_units"],
        ascending=[False, False, False],
    )
    candidate[
        [
            "geoid",
            "NAME",
            "state_abbr",
            "total_units",
            "permits_per_1000_housing_units",
            "mobile_home_share",
            "RISK_SCORE",
            "RISK_RATNG",
            "SOVI_SCORE",
            "SOVI_RATNG",
            "RESL_SCORE",
            "RESL_RATNG",
        ]
    ].head(75).to_csv(TABLES / f"high_mh_high_risk_candidate_counties_{latest_year}.csv", index=False)

    numeric = latest[
        [
            "total_units",
            "permits_per_1000_housing_units",
            "mobile_home_share",
            "acs_median_household_income",
            "acs_median_gross_rent",
            "acs_median_home_value",
            "RISK_SCORE",
            "SOVI_SCORE",
            "RESL_SCORE",
            "CFLD_RISKS",
            "HRCN_RISKS",
            "SWND_RISKS",
            "TRND_RISKS",
            "WFIR_RISKS",
            "HWAV_RISKS",
        ]
    ].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(numeric_only=True).loc[
        ["permits_per_1000_housing_units", "mobile_home_share"],
        [
            "total_units",
            "mobile_home_share",
            "acs_median_household_income",
            "acs_median_gross_rent",
            "acs_median_home_value",
            "RISK_SCORE",
            "SOVI_SCORE",
            "RESL_SCORE",
        ],
    ]
    corr.to_csv(TABLES / f"prototype_correlation_smoke_test_{latest_year}.csv")

    text_accessible = text[text["download_status"].isin(["downloaded", "exists"])]
    text_weak = text[~text["download_status"].isin(["downloaded", "exists"])]
    barrier_cols = [
        "manufactured_home",
        "manufactured_housing",
        "mobile_home",
        "modular_home",
        "hud_code",
        "zoning",
        "permit",
        "specific_use",
        "variance",
        "foundation",
        "inspection",
        "site_plan",
        "setback",
        "age_limit",
        "district_only",
    ]
    text_summary = text[["source_id", "jurisdiction", "download_status", "text_characters", *barrier_cols]]
    text_summary.to_csv(TABLES / "zoning_text_barrier_signal_summary.csv", index=False)

    rows = len(panel)
    counties = panel["geoid"].nunique()
    years = ", ".join(str(y) for y in sorted(panel["year"].unique()))
    acs_coverage = panel["acs_total_housing_units"].notna().mean()
    nri_coverage = panel["RISK_SCORE"].notna().mean()
    total_permits_latest = int(latest["total_units"].sum())
    median_mobile_share = latest["mobile_home_share"].median()
    median_permit_rate = latest["permits_per_1000_housing_units"].median()

    strongest_text_terms = (
        text_summary[barrier_cols]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .to_dict()
    )
    term_line = ", ".join(f"{k}={int(v)}" for k, v in strongest_text_terms.items())

    report = "# Regulatory data prototype\n\nGenerated tables summarize public housing, permits, hazard, and regulatory-text measures. These are descriptive diagnostics; dated policy changes and a separate identification design are required for causal claims.\n"

    (REPORTS / "prototype_viability_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

