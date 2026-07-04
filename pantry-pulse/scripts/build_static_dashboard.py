from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pantry_pulse.data_loader import load_tables
from pantry_pulse.features import build_daily_features, build_inventory_risk
from pantry_pulse.forecasting import make_forecast
from pantry_pulse.recommendations import action_list, recommend_staffing


def records(frame, columns=None):
    data = frame[columns].copy() if columns else frame.copy()
    for column in data.columns:
        if "date" in column:
            data[column] = data[column].astype(str)
    return data.to_dict(orient="records")


def main() -> None:
    public = ROOT / "public"
    public.mkdir(exist_ok=True)

    tables = load_tables(use_bigquery=False)
    features = build_daily_features(tables)
    forecast, mae = make_forecast(features, days=14)
    risk = build_inventory_risk(tables, forecast)
    staffing = recommend_staffing(forecast)
    actions = action_list(risk, staffing)

    latest = features.sort_values("date").iloc[-1]
    next_7 = forecast.head(7)
    high_risk_count = int((risk["risk_level"].astype(str) == "High").sum())

    payload = {
        "metrics": {
            "visitorsYesterday": int(latest["visitors"]),
            "forecast7Day": int(next_7["predicted_visitors"].sum()),
            "highRiskItems": high_risk_count,
            "modelMae": round(float(mae), 1),
        },
        "history": records(features.tail(45), ["date", "visitors"]),
        "forecast": records(forecast, ["date", "predicted_visitors"]),
        "risk": records(
            risk.assign(
                stockout_risk_pct=(risk["stockout_risk"] * 100).round(1),
                risk_level=risk["risk_level"].astype(str),
            ),
            [
                "category",
                "stock_kg",
                "expected_7d_need_kg",
                "coverage_ratio",
                "stockout_risk_pct",
                "risk_level",
            ],
        ),
        "staffing": records(
            staffing.assign(service_load=staffing["service_load"].astype(str)),
            ["date", "predicted_visitors", "recommended_volunteers", "service_load"],
        ),
        "actions": records(actions),
    }

    with (public / "data.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Wrote {public / 'data.json'}")


if __name__ == "__main__":
    main()
