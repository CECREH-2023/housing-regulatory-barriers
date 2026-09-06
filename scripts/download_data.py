#!/usr/bin/env python3
"""Download and normalize first-pass data for the CECREH HUD prototype."""

from __future__ import annotations

import csv
import json
import re
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "outputs" / "reports"

USER_AGENT = (
    "Mozilla/5.0 CECREH-HUD-Regulatory-Barriers-Prototype/0.1 "
    "(research data collection; contact: jesseand@ttu.edu)"
)

TARGET_STATES = {
    "01": "AL",
    "05": "AR",
    "12": "FL",
    "13": "GA",
    "22": "LA",
    "28": "MS",
    "37": "NC",
    "40": "OK",
    "45": "SC",
    "47": "TN",
    "48": "TX",
}

BPS_YEARS = range(2020, 2026)

COUNTY_BPS_COLS = [
    "survey_date",
    "state_fips",
    "county_fips",
    "region_code",
    "division_code",
    "county_name",
    "one_unit_bldgs",
    "one_unit_units",
    "one_unit_value",
    "two_unit_bldgs",
    "two_unit_units",
    "two_unit_value",
    "three_four_bldgs",
    "three_four_units",
    "three_four_value",
    "five_plus_bldgs",
    "five_plus_units",
    "five_plus_value",
    "one_unit_rep_bldgs",
    "one_unit_rep_units",
    "one_unit_rep_value",
    "two_unit_rep_bldgs",
    "two_unit_rep_units",
    "two_unit_rep_value",
    "three_four_rep_bldgs",
    "three_four_rep_units",
    "three_four_rep_value",
    "five_plus_rep_bldgs",
    "five_plus_rep_units",
    "five_plus_rep_value",
]

PLACE_BPS_COLS = [
    "survey_date",
    "state_fips",
    "six_digit_id",
    "county_code",
    "census_place_code",
    "fips_place_code",
    "fips_mcd",
    "population",
    "csa_code",
    "cbsa_code",
    "footnote",
    "central_city",
    "zip_code",
    "region_code",
    "division_code",
    "months_reported",
    "place_name",
    "one_unit_bldgs",
    "one_unit_units",
    "one_unit_value",
    "two_unit_bldgs",
    "two_unit_units",
    "two_unit_value",
    "three_four_bldgs",
    "three_four_units",
    "three_four_value",
    "five_plus_bldgs",
    "five_plus_units",
    "five_plus_value",
    "one_unit_rep_bldgs",
    "one_unit_rep_units",
    "one_unit_rep_value",
    "two_unit_rep_bldgs",
    "two_unit_rep_units",
    "two_unit_rep_value",
    "three_four_rep_bldgs",
    "three_four_rep_units",
    "three_four_rep_value",
    "five_plus_rep_bldgs",
    "five_plus_rep_units",
    "five_plus_rep_value",
]

MHS_FILES = [
    (
        "annual_shipmentstostates.xlsx",
        "https://www2.census.gov/programs-surveys/mhs/tables/time-series/annual_shipmentstostates.xlsx",
    ),
    (
        "monthly_shipmentstostates.xlsx",
        "https://www2.census.gov/programs-surveys/mhs/tables/time-series/monthly_shipmentstostates.xlsx",
    ),
    (
        "Annual_AvgPrice.xlsx",
        "https://www2.census.gov/programs-surveys/mhs/tables/time-series/Annual_AvgPrice.xlsx",
    ),
    (
        "Annual_AvgSqft.xlsx",
        "https://www2.census.gov/programs-surveys/mhs/tables/time-series/Annual_AvgSqft.xlsx",
    ),
    (
        "PUF2024.xlsx",
        "https://www2.census.gov/programs-surveys/mhs/tables/2024/PUF2024.xlsx",
    ),
]

ACS_URL = (
    "https://api.census.gov/data/2024/acs/acs5?"
    "get=NAME,B25001_001E,B25024_010E,B19013_001E,B25064_001E,"
    "B25077_001E,B25003_002E,B25003_003E"
    "&for=county:*&in=state:*"
)

NRI_QUERY_URL = (
    "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
    "National_Risk_Index_Counties/FeatureServer/0/query"
)

NRI_FIELDS = [
    "NRI_ID",
    "STATE",
    "STATEABBRV",
    "STATEFIPS",
    "COUNTY",
    "COUNTYFIPS",
    "STCOFIPS",
    "POPULATION",
    "BUILDVALUE",
    "AREA",
    "RISK_SCORE",
    "RISK_RATNG",
    "EAL_SCORE",
    "EAL_RATNG",
    "SOVI_SCORE",
    "SOVI_RATNG",
    "RESL_SCORE",
    "RESL_RATNG",
    "CFLD_RISKS",
    "HRCN_RISKS",
    "SWND_RISKS",
    "TRND_RISKS",
    "WFIR_RISKS",
    "HWAV_RISKS",
]

TEXT_SOURCES = [
    {
        "source_id": "tdlr_modular_before_buying",
        "jurisdiction": "Texas",
        "source_type": "state_guidance",
        "url": "https://www.tdlr.texas.gov/ihb/beforebuying.htm",
    },
    {
        "source_id": "dalhart_code_department",
        "jurisdiction": "Dalhart, TX",
        "source_type": "local_permit_page",
        "url": "https://www.dalharttx.gov/199/Code-Department",
    },
    {
        "source_id": "burnet_cup_manufactured_home_sales",
        "jurisdiction": "Burnet, TX",
        "source_type": "local_ordinance_page",
        "url": "https://www.burnetedc.com/ordinances/conditional-use-permit-manufactured-home-sales",
    },
    {
        "source_id": "trerc_modular_housing",
        "jurisdiction": "Texas",
        "source_type": "research_extension_article",
        "url": "https://trerc.tamu.edu/article/modular-housing/",
    },
    {
        "source_id": "ecode360_hale_center_candidate",
        "jurisdiction": "Hale Center, TX",
        "source_type": "candidate_municipal_code",
        "url": "https://ecode360.com/39635480",
    },
    {
        "source_id": "municode_princeton_candidate",
        "jurisdiction": "Princeton, TX",
        "source_type": "candidate_municipal_code",
        "url": "https://library.municode.com/tx/princeton/codes/code_of_ordinances?nodeId=COOR_CH42MAHO_ARTIIIEN_S42-58IN",
    },
]

TERM_PATTERNS = {
    "manufactured_home": r"\bmanufactured home[s]?\b",
    "manufactured_housing": r"\bmanufactured housing\b",
    "mobile_home": r"\bmobile home[s]?\b",
    "modular_home": r"\bmodular home[s]?\b",
    "hud_code": r"\bHUD[- ]?code\b|\bHUD code\b",
    "zoning": r"\bzoning\b|\bzoned\b|\bzone\b",
    "permit": r"\bpermit[s]?\b|\bpermitting\b",
    "specific_use": r"\bspecific use\b|\bconditional use\b",
    "variance": r"\bvariance[s]?\b",
    "foundation": r"\bfoundation[s]?\b",
    "inspection": r"\binspection[s]?\b|\binspector\b",
    "site_plan": r"\bsite plan[s]?\b",
    "setback": r"\bsetback[s]?\b",
    "age_limit": r"\bmanufactured more than\b|\bfive years earlier\b|\bage\b",
    "district_only": r"\bMH district\b|\bmanufactured housing district\b|\bpark[s]? and subdivision[s]?\b",
}


@dataclass
class DownloadLog:
    source_id: str
    url: str
    path: str
    status: str
    bytes: int = 0
    note: str = ""


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            clean = re.sub(r"\s+", " ", data.strip())
            if clean:
                self.parts.append(clean)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def ensure_dirs() -> None:
    for path in [RAW, INTERIM, PROCESSED, REPORTS]:
        path.mkdir(parents=True, exist_ok=True)


def request_url(url: str, timeout: int = 90) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.read()
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        context = ssl._create_unverified_context()
        with urlopen(req, timeout=timeout, context=context) as response:
            return response.read()


def download_file(source_id: str, url: str, path: Path, overwrite: bool = False) -> DownloadLog:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0 and not overwrite:
        return DownloadLog(source_id, url, str(path.relative_to(ROOT)), "exists", path.stat().st_size)
    try:
        payload = request_url(url)
        path.write_bytes(payload)
        return DownloadLog(source_id, url, str(path.relative_to(ROOT)), "downloaded", len(payload))
    except (HTTPError, URLError, TimeoutError) as exc:
        return DownloadLog(source_id, url, str(path.relative_to(ROOT)), "failed", 0, str(exc))


def clean_text_from_html(html: bytes) -> str:
    parser = TextExtractor()
    parser.feed(html.decode("utf-8", errors="ignore"))
    return parser.text


def write_logs(logs: Iterable[DownloadLog]) -> None:
    rows = [log.__dict__ for log in logs]
    if not rows:
        return
    path = RAW / "download_log.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_bps_county(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=3, header=None, names=COUNTY_BPS_COLS, dtype=str)
    df = df[df["survey_date"].notna()].copy()
    df["year"] = df["survey_date"].str[:4].astype(int)
    df["county_name"] = df["county_name"].str.strip()
    df["state_fips"] = df["state_fips"].str.zfill(2)
    df["county_fips"] = df["county_fips"].str.zfill(3)
    df["geoid"] = df["state_fips"] + df["county_fips"]
    numeric_cols = [c for c in df.columns if c.endswith(("bldgs", "units", "value"))]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["total_units"] = df[["one_unit_units", "two_unit_units", "three_four_units", "five_plus_units"]].sum(axis=1)
    df["multifamily_units"] = df[["two_unit_units", "three_four_units", "five_plus_units"]].sum(axis=1)
    df["total_value"] = df[["one_unit_value", "two_unit_value", "three_four_value", "five_plus_value"]].sum(axis=1)
    return df


def read_bps_place(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=3, header=None, names=PLACE_BPS_COLS, dtype=str)
    df = df[df["survey_date"].notna()].copy()
    df["year"] = df["survey_date"].str[:4].astype(int)
    df["place_name"] = df["place_name"].str.strip()
    df["state_fips"] = df["state_fips"].str.zfill(2)
    df["county_code"] = df["county_code"].str.zfill(3)
    df["county_geoid"] = df["state_fips"] + df["county_code"]
    numeric_cols = [
        "population",
        "months_reported",
        *[c for c in df.columns if c.endswith(("bldgs", "units", "value"))],
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["total_units"] = df[["one_unit_units", "two_unit_units", "three_four_units", "five_plus_units"]].sum(axis=1)
    df["multifamily_units"] = df[["two_unit_units", "three_four_units", "five_plus_units"]].sum(axis=1)
    return df


def fetch_bps(logs: list[DownloadLog]) -> tuple[pd.DataFrame, pd.DataFrame]:
    county_frames = []
    place_frames = []
    county_dir = RAW / "census_bps" / "county"
    place_dir = RAW / "census_bps" / "place_south"
    for year in BPS_YEARS:
        yy = str(year)[-2:]
        county_url = f"https://www2.census.gov/econ/bps/County/co{yy}12y.txt"
        county_path = county_dir / f"co{yy}12y.txt"
        logs.append(download_file(f"bps_county_{year}", county_url, county_path))
        if county_path.exists() and county_path.stat().st_size > 0:
            county_frames.append(read_bps_county(county_path))

        place_url = f"https://www2.census.gov/econ/bps/Place/South%20Region/so{yy}12y.txt"
        place_path = place_dir / f"so{yy}12y.txt"
        logs.append(download_file(f"bps_place_south_{year}", place_url, place_path))
        if place_path.exists() and place_path.stat().st_size > 0:
            place_frames.append(read_bps_place(place_path))

    county = pd.concat(county_frames, ignore_index=True)
    county = county[county["state_fips"].isin(TARGET_STATES)].copy()
    county["state_abbr"] = county["state_fips"].map(TARGET_STATES)
    county.to_csv(PROCESSED / "bps_county_target_states_2020_2025.csv", index=False)

    place = pd.concat(place_frames, ignore_index=True)
    place = place[place["state_fips"].isin(TARGET_STATES)].copy()
    place["state_abbr"] = place["state_fips"].map(TARGET_STATES)
    place.to_csv(PROCESSED / "bps_place_south_target_states_2020_2025.csv", index=False)
    return county, place


def fetch_mhs(logs: list[DownloadLog]) -> None:
    mhs_dir = RAW / "census_mhs"
    inventory = []
    for filename, url in MHS_FILES:
        path = mhs_dir / filename
        logs.append(download_file(f"mhs_{filename}", url, path))
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            xls = pd.ExcelFile(path)
            for sheet in xls.sheet_names:
                preview = pd.read_excel(path, sheet_name=sheet, nrows=5)
                full = pd.read_excel(path, sheet_name=sheet)
                inventory.append(
                    {
                        "file": filename,
                        "sheet": sheet,
                        "rows": int(full.shape[0]),
                        "columns": int(full.shape[1]),
                        "first_columns": "; ".join(str(c) for c in preview.columns[:8]),
                    }
                )
        except Exception as exc:
            inventory.append(
                {
                    "file": filename,
                    "sheet": "",
                    "rows": 0,
                    "columns": 0,
                    "first_columns": f"inventory_failed: {exc}",
                }
            )
    pd.DataFrame(inventory).to_csv(INTERIM / "mhs_workbook_inventory.csv", index=False)


def fetch_acs(logs: list[DownloadLog]) -> pd.DataFrame:
    path = RAW / "census_acs" / "acs5_2024_county_mobilehome_affordability.json"
    logs.append(download_file("acs5_2024_county", ACS_URL, path))
    data = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(data[1:], columns=data[0])
    df["state"] = df["state"].str.zfill(2)
    df["county"] = df["county"].str.zfill(3)
    df["geoid"] = df["state"] + df["county"]
    df = df.rename(
        columns={
            "B25001_001E": "acs_total_housing_units",
            "B25024_010E": "acs_mobile_home_units",
            "B19013_001E": "acs_median_household_income",
            "B25064_001E": "acs_median_gross_rent",
            "B25077_001E": "acs_median_home_value",
            "B25003_002E": "acs_owner_occupied_units",
            "B25003_003E": "acs_renter_occupied_units",
        }
    )
    numeric = [c for c in df.columns if c.startswith("acs_")]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["mobile_home_share"] = df["acs_mobile_home_units"] / df["acs_total_housing_units"]
    df = df[df["state"].isin(TARGET_STATES)].copy()
    df["state_abbr"] = df["state"].map(TARGET_STATES)
    df.to_csv(PROCESSED / "acs5_2024_county_target_states.csv", index=False)
    return df


def fetch_nri(logs: list[DownloadLog]) -> pd.DataFrame:
    all_features = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": ",".join(NRI_FIELDS),
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": 2000,
            "resultOffset": offset,
        }
        url = NRI_QUERY_URL + "?" + urlencode(params)
        payload = request_url(url, timeout=120)
        data = json.loads(payload.decode("utf-8"))
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        if not data.get("exceededTransferLimit") and len(features) < 2000:
            break
        offset += len(features)
        time.sleep(0.2)

    path = RAW / "fema_nri" / "national_risk_index_counties_query.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"features": all_features}, indent=2), encoding="utf-8")
    logs.append(
        DownloadLog(
            "fema_nri_counties",
            NRI_QUERY_URL,
            str(path.relative_to(ROOT)),
            "downloaded",
            path.stat().st_size,
            f"{len(all_features)} features",
        )
    )
    rows = [feature["attributes"] for feature in all_features]
    df = pd.DataFrame(rows)
    df["STATEFIPS"] = df["STATEFIPS"].astype(str).str.zfill(2)
    df["COUNTYFIPS"] = df["COUNTYFIPS"].astype(str).str.zfill(3)
    df["geoid"] = df["STATEFIPS"] + df["COUNTYFIPS"]
    df = df[df["STATEFIPS"].isin(TARGET_STATES)].copy()
    df.to_csv(PROCESSED / "fema_nri_county_target_states.csv", index=False)
    return df


def fetch_text_sources(logs: list[DownloadLog]) -> pd.DataFrame:
    raw_dir = RAW / "zoning_text"
    text_dir = PROCESSED / "zoning_text"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    with (raw_dir / "source_urls.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "jurisdiction", "source_type", "url"])
        writer.writeheader()
        writer.writerows(TEXT_SOURCES)

    rows = []
    for source in TEXT_SOURCES:
        source_id = source["source_id"]
        url = source["url"]
        raw_path = raw_dir / f"{source_id}.html"
        text_path = text_dir / f"{source_id}.txt"
        log = download_file(source_id, url, raw_path, overwrite=True)
        status = log.status
        text = ""
        note = log.note
        if raw_path.exists() and raw_path.stat().st_size > 0:
            text = clean_text_from_html(raw_path.read_bytes())
            text_path.write_text(text, encoding="utf-8")
            if len(text) < 500:
                status = "weak_text"
                note = "Downloaded page but extracted text is very short; likely app shell or blocked content."
        else:
            status = "failed"
        log.status = status
        log.note = note
        logs.append(log)
        counts = {
            term: len(re.findall(pattern, text, flags=re.IGNORECASE))
            for term, pattern in TERM_PATTERNS.items()
        }
        rows.append(
            {
                **source,
                "download_status": status,
                "note": note,
                "raw_path": str(raw_path.relative_to(ROOT)),
                "text_path": str(text_path.relative_to(ROOT)) if text else "",
                "text_characters": len(text),
                **counts,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "zoning_text_term_counts.csv", index=False)
    return df


def build_county_panel(bps: pd.DataFrame, acs: pd.DataFrame, nri: pd.DataFrame) -> pd.DataFrame:
    nri_keep = [
        "geoid",
        "RISK_SCORE",
        "RISK_RATNG",
        "EAL_SCORE",
        "EAL_RATNG",
        "SOVI_SCORE",
        "SOVI_RATNG",
        "RESL_SCORE",
        "RESL_RATNG",
        "CFLD_RISKS",
        "HRCN_RISKS",
        "SWND_RISKS",
        "TRND_RISKS",
        "WFIR_RISKS",
        "HWAV_RISKS",
    ]
    panel = bps.merge(
        acs[
            [
                "geoid",
                "NAME",
                "acs_total_housing_units",
                "acs_mobile_home_units",
                "acs_median_household_income",
                "acs_median_gross_rent",
                "acs_median_home_value",
                "acs_owner_occupied_units",
                "acs_renter_occupied_units",
                "mobile_home_share",
            ]
        ],
        on="geoid",
        how="left",
    )
    panel = panel.merge(nri[nri_keep], on="geoid", how="left")
    panel["permits_per_1000_housing_units"] = (
        panel["total_units"] / panel["acs_total_housing_units"] * 1000
    )
    panel["multifamily_share_of_permits"] = panel["multifamily_units"] / panel["total_units"].replace({0: pd.NA})
    panel["avg_permitted_value_per_unit"] = panel["total_value"] / panel["total_units"].replace({0: pd.NA})
    panel.to_csv(PROCESSED / "county_prototype_panel_2020_2025.csv", index=False)
    return panel


def write_source_manifest(logs: list[DownloadLog]) -> None:
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "project": "CECREH HUD Regulatory Barriers Prototype",
        "target_states": TARGET_STATES,
        "sources": [log.__dict__ for log in logs],
    }
    (RAW / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    logs: list[DownloadLog] = []
    bps_county, _bps_place = fetch_bps(logs)
    fetch_mhs(logs)
    acs = fetch_acs(logs)
    nri = fetch_nri(logs)
    fetch_text_sources(logs)
    panel = build_county_panel(bps_county, acs, nri)
    write_logs(logs)
    write_source_manifest(logs)

    summary = {
        "county_panel_rows": int(panel.shape[0]),
        "county_panel_counties": int(panel["geoid"].nunique()),
        "county_panel_years": sorted(int(y) for y in panel["year"].dropna().unique()),
        "downloaded_or_existing": sum(1 for log in logs if log.status in {"downloaded", "exists"}),
        "failed_or_weak": sum(1 for log in logs if log.status not in {"downloaded", "exists"}),
    }
    (REPORTS / "download_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
