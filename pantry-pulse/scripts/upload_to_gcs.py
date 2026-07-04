from __future__ import annotations

import os
from pathlib import Path

from pantry_pulse.cloud import upload_data_to_gcs


def main() -> None:
    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        raise SystemExit("Set GCS_BUCKET before running this script.")
    data_dir = Path(__file__).resolve().parents[1] / "data"
    for uri in upload_data_to_gcs(bucket, data_dir):
        print(uri)


if __name__ == "__main__":
    main()
