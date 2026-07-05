from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


TABLES = {
    "visits": "visits.csv",
    "inventory": "inventory.csv",
    "donations": "donations.csv",
    "weather": "weather.csv",
    "events": "events.csv",
}


class DataSourceError(RuntimeError):
    """Raised when the requested data source is not available."""


def _read_local_csv(name: str, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    path = data_dir / TABLES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python scripts/generate_sample_data.py` first."
        )
    return pd.read_csv(path, parse_dates=["date"])


def _make_bigquery_client(bigquery, project: str):
    """Build a BigQuery client.

    On Streamlit Cloud there are no ambient gcloud credentials, so we look
    for a service account block in st.secrets (set via the Streamlit Cloud
    Secrets UI, never committed to the repo). Locally, if st.secrets isn't
    available or doesn't have that block, fall back to whatever default
    application credentials are available.
    """
    try:
        import streamlit as st
        from google.oauth2 import service_account

        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"])
            )
            return bigquery.Client(project=project, credentials=credentials)
    except Exception:
        pass
    return bigquery.Client(project=project)


def _read_bigquery_table(name: str) -> pd.DataFrame:
    try:
        from google.cloud import bigquery
    except ModuleNotFoundError as exc:
        raise DataSourceError(
            "BigQuery mode needs the `google-cloud-bigquery` package. "
            "Install requirements.txt or turn off `Read from BigQuery` to use local sample data."
        ) from exc

    project = os.getenv("GCP_PROJECT")
    dataset = os.getenv("BQ_DATASET", "pantry_pulse")
    if not project:
        raise DataSourceError("GCP_PROJECT must be set when BigQuery mode is enabled.")

    try:
        client = _make_bigquery_client(bigquery, project)
        table = f"`{project}.{dataset}.{name}`"
        df = client.query(f"SELECT * FROM {table}").to_dataframe()
    except Exception as exc:
        raise DataSourceError(
            f"BigQuery query for `{name}` failed: {exc}"
        ) from exc

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_tables(use_bigquery: bool = False) -> dict[str, pd.DataFrame]:
    reader = _read_bigquery_table if use_bigquery else _read_local_csv
    return {name: reader(name) for name in TABLES}
