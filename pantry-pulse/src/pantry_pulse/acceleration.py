from __future__ import annotations

import importlib.util
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class AccelerationStatus:
    enabled: bool
    engine: str
    note: str


def enable_rapids_if_available() -> AccelerationStatus:
    """Enable cudf.pandas acceleration if installed and not disabled."""
    if os.getenv("PANTRY_PULSE_DISABLE_RAPIDS", "false").lower() == "true":
        return AccelerationStatus(False, "pandas", "RAPIDS disabled by environment variable.")

    if importlib.util.find_spec("cudf") is None:
        return AccelerationStatus(False, "pandas", "cuDF is not installed; using pandas fallback.")

    if importlib.util.find_spec("cudf.pandas") is None:
        return AccelerationStatus(False, "pandas", "cuDF exists, but cudf.pandas is unavailable.")

    try:
        import cudf.pandas  # type: ignore

        cudf.pandas.install()
        return AccelerationStatus(True, "cudf.pandas", "RAPIDS dataframe acceleration is active.")
    except Exception as exc:  # pragma: no cover - depends on GPU runtime
        return AccelerationStatus(False, "pandas", f"RAPIDS import failed; using pandas fallback: {exc}")


@contextmanager
def timed_stage(name: str, collector: list[dict[str, float | str]]):
    start = time.perf_counter()
    yield
    collector.append({"stage": name, "seconds": round(time.perf_counter() - start, 4)})
