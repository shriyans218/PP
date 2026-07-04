from __future__ import annotations

from pantry_pulse.data_loader import load_tables
from pantry_pulse.features import build_daily_features, build_inventory_risk
from pantry_pulse.forecasting import make_forecast
from pantry_pulse.recommendations import action_list, recommend_staffing


def main() -> None:
    tables = load_tables(use_bigquery=False)
    features = build_daily_features(tables)
    forecast, mae = make_forecast(features, days=7)
    risk = build_inventory_risk(tables, forecast)
    staffing = recommend_staffing(forecast)
    actions = action_list(risk, staffing)

    assert len(features) > 100
    assert len(forecast) == 7
    assert mae >= 0
    assert not risk.empty
    assert not staffing.empty
    assert not actions.empty
    print("Smoke test passed")


if __name__ == "__main__":
    main()
