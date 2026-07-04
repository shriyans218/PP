from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def main() -> None:
    rng = np.random.default_rng(42)
    DATA_DIR.mkdir(exist_ok=True)
    dates = pd.date_range("2025-01-01", periods=210, freq="D")

    weather = pd.DataFrame(
        {
            "date": dates,
            "temperature_c": np.round(26 + np.sin(np.arange(len(dates)) / 18) * 5 + rng.normal(0, 1.8, len(dates)), 1),
            "rain_mm": np.round(rng.gamma(1.2, 3.5, len(dates)) * rng.choice([0, 1], len(dates), p=[0.55, 0.45]), 1),
        }
    )

    event_rows = []
    for d in dates:
        if d.dayofweek == 0:
            event_rows.append((d, "Benefit renewal support", 1.2))
        if d.day in [1, 15]:
            event_rows.append((d, "Community clinic day", 1.0))
        if d.month in [4, 5] and d.dayofweek == 4:
            event_rows.append((d, "Exam week pantry pickup", 1.6))
    events = pd.DataFrame(event_rows, columns=["date", "event_name", "demand_pressure"])

    visit_rows = []
    household_id = 1000
    for d in dates:
        dow_effect = 14 if d.dayofweek in [0, 4] else 0
        weather_row = weather[weather["date"] == d].iloc[0]
        rain_effect = 6 if weather_row["rain_mm"] > 8 else 0
        temp_effect = 5 if weather_row["temperature_c"] > 32 else 0
        event_effect = events[events["date"] == d]["demand_pressure"].sum() * 10
        base = 42 + dow_effect + rain_effect + temp_effect + event_effect
        visits = max(12, int(rng.normal(base, 8)))
        for _ in range(visits):
            household_id += int(rng.integers(1, 4))
            visit_rows.append(
                {
                    "date": d,
                    "household_id": household_id,
                    "has_senior": int(rng.random() < 0.28),
                    "children": int(rng.choice([0, 1, 2, 3], p=[0.46, 0.26, 0.2, 0.08])),
                }
            )
    visits = pd.DataFrame(visit_rows)

    categories = ["rice", "lentils", "oil", "vegetables", "milk", "hygiene"]
    stock = dict(zip(categories, [620.0, 240.0, 75.0, 210.0, 105.0, 55.0]))
    use_per_visit = dict(zip(categories, [0.85, 0.34, 0.09, 0.42, 0.2, 0.06]))
    inventory_rows = []
    donation_rows = []
    donation_id = 0

    for d in dates:
        visitors = visits[visits["date"] == d]["household_id"].nunique()
        for cat in categories:
            stock[cat] = max(0, stock[cat] - visitors * use_per_visit[cat] * rng.uniform(0.85, 1.12))
            if rng.random() < (0.16 if cat in ["vegetables", "milk"] else 0.08):
                qty = float(rng.uniform(20, 140))
                stock[cat] += qty
                donation_id += 1
                donation_rows.append(
                    {
                        "date": d,
                        "donation_id": f"D{donation_id:05d}",
                        "category": cat,
                        "quantity_kg": round(qty, 1),
                        "source": rng.choice(["Retail rescue", "Community drive", "Local farm", "Corporate sponsor"]),
                    }
                )
            inventory_rows.append(
                {
                    "date": d,
                    "category": cat,
                    "stock_kg": round(stock[cat], 1),
                    "is_low_stock": int(stock[cat] < 90 if cat != "hygiene" else stock[cat] < 35),
                }
            )

    inventory = pd.DataFrame(inventory_rows)
    donations = pd.DataFrame(donation_rows)

    visits.to_csv(DATA_DIR / "visits.csv", index=False)
    inventory.to_csv(DATA_DIR / "inventory.csv", index=False)
    donations.to_csv(DATA_DIR / "donations.csv", index=False)
    weather.to_csv(DATA_DIR / "weather.csv", index=False)
    events.to_csv(DATA_DIR / "events.csv", index=False)
    print(f"Generated sample data in {DATA_DIR}")


if __name__ == "__main__":
    main()
