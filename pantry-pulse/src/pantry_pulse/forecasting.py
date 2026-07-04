from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


FEATURE_COLUMNS = [
    "day_of_week",
    "is_weekend",
    "temperature_c",
    "rain_mm",
    "event_count",
    "event_pressure",
    "rolling_7d_visitors",
    "low_stock_items",
]


def train_forecaster(features: pd.DataFrame) -> tuple[Pipeline, float]:
    df = features.dropna(subset=FEATURE_COLUMNS + ["visitors"]).copy()
    split_idx = max(int(len(df) * 0.8), 14)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:] if split_idx < len(df) else df.tail(14)

    preprocessor = ColumnTransformer(
        transformers=[
            ("dow", OneHotEncoder(handle_unknown="ignore"), ["day_of_week"]),
            ("num", "passthrough", [col for col in FEATURE_COLUMNS if col != "day_of_week"]),
        ]
    )
    model = Pipeline(
        steps=[
            ("features", preprocessor),
            ("model", RandomForestRegressor(n_estimators=120, random_state=42, min_samples_leaf=3)),
        ]
    )
    model.fit(train[FEATURE_COLUMNS], train["visitors"])
    mae = mean_absolute_error(test["visitors"], model.predict(test[FEATURE_COLUMNS]))
    return model, float(mae)


def make_forecast(features: pd.DataFrame, days: int = 14) -> tuple[pd.DataFrame, float]:
    model, mae = train_forecaster(features)
    last = features.sort_values("date").tail(1).iloc[0]
    future_rows = []
    rolling = float(features["visitors"].tail(7).mean())

    for offset in range(1, days + 1):
        date = last["date"] + pd.Timedelta(days=offset)
        dow = date.dayofweek
        expected_event_pressure = 1 if dow in [0, 4] else 0
        row = {
            "date": date,
            "day_of_week": dow,
            "is_weekend": int(dow in [5, 6]),
            "temperature_c": float(np.clip(last["temperature_c"] + np.sin(offset / 3) * 2, 20, 38)),
            "rain_mm": float(max(0, last["rain_mm"] * 0.6 + (3 if dow == 1 else 0))),
            "event_count": int(expected_event_pressure > 0),
            "event_pressure": expected_event_pressure,
            "rolling_7d_visitors": rolling,
            "low_stock_items": float(last["low_stock_items"]),
        }
        pred = max(float(model.predict(pd.DataFrame([row])[FEATURE_COLUMNS])[0]), 0)
        row["predicted_visitors"] = round(pred)
        rolling = (rolling * 6 + pred) / 7
        future_rows.append(row)

    return pd.DataFrame(future_rows), mae
