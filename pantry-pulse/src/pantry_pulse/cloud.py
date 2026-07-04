from __future__ import annotations

from pathlib import Path


def upload_data_to_gcs(bucket_name: str, data_dir: Path) -> list[str]:
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    uploaded = []
    for path in data_dir.glob("*.csv"):
        blob = bucket.blob(f"raw/{path.name}")
        blob.upload_from_filename(path)
        uploaded.append(f"gs://{bucket_name}/raw/{path.name}")
    return uploaded
