from __future__ import annotations

import pandas as pd


def recommend_staffing(forecast: pd.DataFrame) -> pd.DataFrame:
    df = forecast[["date", "predicted_visitors", "event_pressure", "rain_mm"]].copy()
    df["recommended_volunteers"] = (
        (df["predicted_visitors"] / 18).round().clip(lower=2)
        + (df["event_pressure"] > 0).astype(int)
        + (df["rain_mm"] > 8).astype(int)
    ).astype(int)
    df["service_load"] = pd.cut(
        df["predicted_visitors"],
        bins=[-1, 45, 75, 10_000],
        labels=["Normal", "Busy", "Surge"],
    )
    return df


def action_list(inventory_risk: pd.DataFrame, staffing: pd.DataFrame) -> pd.DataFrame:
    actions = []
    high_risk = inventory_risk[inventory_risk["risk_level"].astype(str) == "High"]
    for _, row in high_risk.iterrows():
        actions.append(
            {
                "priority": "High",
                "action": f"Request emergency donation for {row['category']}",
                "reason": f"{row['stock_kg']:.0f} kg on hand vs {row['expected_7d_need_kg']:.0f} kg expected 7-day need",
            }
        )

    peak_day = staffing.sort_values("recommended_volunteers", ascending=False).iloc[0]
    actions.append(
        {
            "priority": "Medium",
            "action": f"Schedule {int(peak_day['recommended_volunteers'])} volunteers on {peak_day['date'].date()}",
            "reason": f"Forecast demand is {int(peak_day['predicted_visitors'])} visitors",
        }
    )

    return pd.DataFrame(actions)
