from __future__ import annotations

import os
from pathlib import Path

from google.cloud import bigquery

TABLES = ["visits", "inventory", "donations", "weather", "events"]


def main() -> None:
    project = os.getenv("GCP_PROJECT")
    dataset = os.getenv("BQ_DATASET", "pantry_pulse")
    if not project:
        raise SystemExit("Set GCP_PROJECT before running this script.")

    client = bigquery.Client(project=project)
    data_dir = Path(__file__).resolve().parents[1] / "data"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    for name in TABLES:
        csv_path = data_dir / f"{name}.csv"
        table_id = f"{project}.{dataset}.{name}"
        with open(csv_path, "rb") as fh:
            job = client.load_table_from_file(fh, table_id, job_config=job_config)
        job.result()
        table = client.get_table(table_id)
        print(f"Loaded {table.num_rows} rows into {table_id}")


if __name__ == "__main__":
    main()
