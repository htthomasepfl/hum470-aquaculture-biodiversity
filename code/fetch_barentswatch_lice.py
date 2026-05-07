"""
fetch_barentswatch_lice.py
==========================
Standalone script to retrieve weekly average adult female salmon lice counts
per fish from the BarentsWatch Fish Health API (2012–2019) and compute
annual national averages.

Output
------
output/data/lice_annual_avg.csv
    Columns: year, N_lice_per_fish_avg

Authentication
--------------
The BarentsWatch API requires OAuth2 client credentials.

Steps to obtain credentials:
  1. Register at https://www.barentswatch.no/minside/
  2. Go to "API-klient" and create a new client (scope: api)
  3. Copy your client_id and client_secret
  4. Set them as environment variables (recommended) or directly in this script:

        export BW_CLIENT_ID="your_client_id"
        export BW_CLIENT_SECRET="your_client_secret"

API Reference
-------------
- Auth:    POST https://id.barentswatch.no/connect/token
- Lice:    POST /v2/geodata/fishhealth/locality/{year}/{week}
           Response key: averageFemalelice (adult female lice per fish)
- Docs:    https://developer.barentswatch.no/docs/fishhealth/

Usage
-----
    python fetch_barentswatch_lice.py
    python fetch_barentswatch_lice.py --years 2012 2013 2014
    python fetch_barentswatch_lice.py --out path/to/output.csv
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
TOKEN_URL    = "https://id.barentswatch.no/connect/token"
API_BASE     = "https://www.barentswatch.no/bwapi"
LICE_ENDPOINT = API_BASE + "/v2/geodata/fishhealth/locality/{year}/{week}"

DEFAULT_YEARS   = list(range(2012, 2020))   # 2012–2019 inclusive
WEEKS_PER_YEAR  = 52
REQUEST_DELAY_S = 0.3   # polite rate-limit: 3 req/s max

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OUT = OUTPUT_DIR / "lice_annual_avg.csv"


# ── Authentication ─────────────────────────────────────────────────────────────
def get_access_token(client_id: str, client_secret: str) -> str:
    """Exchange client credentials for a Bearer token (expires in 3600 s)."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type":    "client_credentials",
            "client_id":     client_id,
            "client_secret": client_secret,
            "scope":         "api",
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    log.info("Access token obtained (expires in %s s)", resp.json().get("expires_in"))
    return token


# ── Data fetching ──────────────────────────────────────────────────────────────
def fetch_week(year: int, week: int, token: str) -> list[dict]:
    """
    Fetch locality-level lice reports for a single (year, week).
    Returns a list of records with keys: locality_no, avg_female_lice.
    Only includes active localities that have reported (hasReported=True,
    isFallow=False) and have a non-null adultFemaleLice.average value.
    """
    url = LICE_ENDPOINT.format(year=year, week=week)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={}, timeout=30)

    if resp.status_code == 404:
        log.debug("No data for %d-W%02d (404)", year, week)
        return []
    if resp.status_code == 401:
        raise RuntimeError("Unauthorized – check your client_id and client_secret.")
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        data = data.get("localities", data.get("features", []))

    records = []
    for item in data:
        lice_report = item.get("liceReport", {})
        # Skip non-reporting and fallow localities
        if not lice_report.get("hasReported", False):
            continue
        if lice_report.get("isFallow", True):
            continue
        avg = lice_report.get("adultFemaleLice", {}).get("average")
        if avg is None:
            continue
        locality_no = item.get("locality", {}).get("no") or item.get("localityNo")
        records.append({"locality_no": locality_no, "avg_female_lice": float(avg)})
    return records


def fetch_year(year: int, token: str) -> pd.DataFrame:
    """
    Iterate weeks 1–52 for `year` and collect averageFemalelice values.
    Returns a DataFrame with columns [year, week, locality_no, avg_female_lice].
    """
    records = []
    for week in range(1, WEEKS_PER_YEAR + 1):
        try:
            rows = fetch_week(year, week, token)
        except Exception as exc:
            log.warning("Error fetching %d-W%02d: %s – skipping", year, week, exc)
            time.sleep(REQUEST_DELAY_S * 3)
            continue

        for row in rows:
            records.append({
                "year":            year,
                "week":            week,
                "locality_no":     row["locality_no"],
                "avg_female_lice": row["avg_female_lice"],
            })
        time.sleep(REQUEST_DELAY_S)

    df = pd.DataFrame(records)
    log.info("Year %d: %d locality-week observations fetched.", year, len(df))
    return df


# ── Aggregation ────────────────────────────────────────────────────────────────
def annual_national_average(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    Compute annual national average of adult female lice per fish.
    Strategy: for each (year, week), take the mean across all active localities
    (simple mean of site-level means, as BarentsWatch reports do not include
    biomass weights per locality). Then average across weeks within the year.
    This matches the methodology described in Fish Health Report 2024 (p. 155).
    """
    weekly_nat = (
        df_all
        .groupby(["year", "week"])["avg_female_lice"]
        .mean()
        .reset_index()
        .rename(columns={"avg_female_lice": "weekly_nat_avg"})
    )
    annual = (
        weekly_nat
        .groupby("year")["weekly_nat_avg"]
        .mean()
        .reset_index()
        .rename(columns={"weekly_nat_avg": "N_lice_per_fish_avg"})
    )
    annual["N_lice_per_fish_avg"] = annual["N_lice_per_fish_avg"].round(4)
    return annual.sort_values("year").reset_index(drop=True)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch BarentsWatch salmon lice data.")
    parser.add_argument(
        "--years", nargs="+", type=int, default=DEFAULT_YEARS,
        help="Years to fetch (default: 2012–2019)",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help="Output CSV path",
    )
    args = parser.parse_args()

    # ── Credentials ──
    client_id     = os.environ.get("BW_CLIENT_ID", "")
    client_secret = os.environ.get("BW_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        log.error(
            "Missing credentials. Set environment variables:\n"
            "  export BW_CLIENT_ID='your_client_id'\n"
            "  export BW_CLIENT_SECRET='your_client_secret'\n"
            "\n"
            "Register at: https://www.barentswatch.no/minside/\n"
            "See: https://developer.barentswatch.no/docs/appreg/"
        )
        sys.exit(1)

    token = get_access_token(client_id, client_secret)

    all_frames = []
    for year in sorted(args.years):
        log.info("Fetching lice data for year %d …", year)
        df_year = fetch_year(year, token)
        if not df_year.empty:
            all_frames.append(df_year)

    if not all_frames:
        log.error("No data retrieved. Exiting.")
        sys.exit(1)

    df_all  = pd.concat(all_frames, ignore_index=True)
    df_out  = annual_national_average(df_all)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.out, index=False)
    log.info("Saved %d rows to %s", len(df_out), args.out)
    print(df_out.to_string(index=False))


if __name__ == "__main__":
    main()
