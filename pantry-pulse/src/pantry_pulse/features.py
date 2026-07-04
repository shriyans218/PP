from __future__ import annotations

import pandas as pd


def build_daily_features(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    visits = tables["visits"].copy()
    inventory = tables["inventory"].copy()
    donations = tables["donations"].copy()
    weather = tables["weather"].copy()
    events = tables["events"].copy()

    daily_visits = (
        visits.groupby("date", as_index=False)
        .agg(
            visitors=("household_id", "nunique"),
            households=("household_id", "count"),
            seniors=("has_senior", "sum"),
            children=("children", "sum"),
        )
        .sort_values("date")
    )

    donation_daily = (
        donations.groupby("date", as_index=False)
        .agg(donation_kg=("quantity_kg", "sum"), donation_events=("donation_id", "count"))
    )

    inventory_daily = (
        inventory.groupby("date", as_index=False)
        .agg(total_stock_kg=("stock_kg", "sum"), low_stock_items=("is_low_stock", "sum"))
    )

    event_daily = (
        events.groupby("date", as_index=False)
        .agg(event_count=("event_name", "count"), event_pressure=("demand_pressure", "sum"))
    )

    df = daily_visits.merge(weather, on="date", how="left")
    df = df.merge(donation_daily, on="date", how="left")
    df = df.merge(inventory_daily, on="date", how="left")
    df = df.merge(event_daily, on="date", how="left")
    df = df.sort_values("date")

    fill_zero = ["donation_kg", "donation_events", "event_count", "event_pressure", "low_stock_items"]
    df[fill_zero] = df[fill_zero].fillna(0)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["rolling_7d_visitors"] = df["visitors"].rolling(7, min_periods=1).mean()
    df["rain_or_heat_flag"] = ((df["rain_mm"] > 8) | (df["temperature_c"] > 32)).astype(int)
    return df


def build_inventory_risk(tables: dict[str, pd.DataFrame], forecast: pd.DataFrame) -> pd.DataFrame:
    inventory = tables["inventory"].copy()
    latest_date = inventory["date"].max()
    latest = inventory[inventory["date"] == latest_date].copy()

    expected_visitors_7d = max(float(forecast["predicted_visitors"].head(7).sum()), 1.0)
    category_multiplier = {
        "rice": 0.85,
        "lentils": 0.34,
        "oil": 0.09,
        "vegetables": 0.42,
        "milk": 0.2,
        "hygiene": 0.06,
    }
    latest["expected_7d_need_kg"] = latest["category"].map(category_multiplier).fillna(0.2) * expected_visitors_7d
    latest["coverage_ratio"] = latest["stock_kg"] / latest["expected_7d_need_kg"].clip(lower=1)
    latest["stockout_risk"] = (1 - latest["coverage_ratio"]).clip(lower=0, upper=1)
    latest["risk_level"] = pd.cut(
        latest["stockout_risk"],
        bins=[-0.01, 0.25, 0.55, 1.0],
        labels=["Low", "Medium", "High"],
    )
    return latest.sort_values(["stockout_risk", "expected_7d_need_kg"], ascending=False)
