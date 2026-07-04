from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_pipeline(disable_rapids: bool) -> float:
    env = os.environ.copy()
    env["PANTRY_PULSE_DISABLE_RAPIDS"] = "true" if disable_rapids else "false"
    start = time.perf_counter()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "smoke_test.py")],
        env=env,
        check=True,
        cwd=ROOT,
    )
    return time.perf_counter() - start


def main() -> None:
    pandas_time = run_pipeline(disable_rapids=True)
    rapids_time = run_pipeline(disable_rapids=False)

    speedup = pandas_time / rapids_time if rapids_time > 0 else float("nan")
    report = (
        f"pandas (CPU):    {pandas_time:.3f}s\n"
        f"cudf.pandas (GPU): {rapids_time:.3f}s\n"
        f"speedup: {speedup:.2f}x\n"
    )
    print(report)
    (ROOT / "benchmark_result.txt").write_text(report)


if __name__ == "__main__":
    main()
