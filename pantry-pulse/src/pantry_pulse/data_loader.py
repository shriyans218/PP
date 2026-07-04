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

    client = bigquery.Client(project=project)
    table = f"`{project}.{dataset}.{name}`"
    df = client.query(f"SELECT * FROM {table}").to_dataframe()
    if "date" in df.columns:
        # BigQuery DATE columns can come back as a `dbdate` extension dtype
        # (via db-dtypes) instead of datetime64[ns]. Normalize so downstream
        # code (df["date"].dt.dayofweek, date arithmetic in forecasting.py)
        # behaves identically whether data came from CSV or BigQuery.
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_tables(use_bigquery: bool = False) -> dict[str, pd.DataFrame]:
    reader = _read_bigquery_table if use_bigquery else _read_local_csv
    return {name: reader(name) for name in TABLES}
