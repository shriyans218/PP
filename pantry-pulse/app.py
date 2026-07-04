from __future__ import annotations

import os
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from pantry_pulse.acceleration import enable_rapids_if_available, timed_stage

ACCELERATION = enable_rapids_if_available()

import pandas as pd  # noqa: E402

from pantry_pulse.data_loader import DataSourceError, load_tables  # noqa: E402
from pantry_pulse.features import build_daily_features, build_inventory_risk  # noqa: E402
from pantry_pulse.forecasting import make_forecast  # noqa: E402
from pantry_pulse.recommendations import action_list, recommend_staffing  # noqa: E402


st.set_page_config(page_title="Pantry Pulse", page_icon="PP", layout="wide")


@st.cache_data(show_spinner=False)
def run_pipeline(use_bigquery: bool, forecast_days: int):
    timings = []
    with timed_stage("Load data", timings):
        source = "BigQuery" if use_bigquery else "local CSV"
        try:
            tables = load_tables(use_bigquery=use_bigquery)
        except DataSourceError as exc:
            if not use_bigquery:
                raise
            tables = load_tables(use_bigquery=False)
            source = "local CSV fallback"
            timings.append({"stage": "BigQuery unavailable", "seconds": 0.0})
            warning = str(exc)
        else:
            warning = ""
    with timed_stage("Clean and join features", timings):
        features = build_daily_features(tables)
    with timed_stage("Train model and forecast", timings):
        forecast, mae = make_forecast(features, days=forecast_days)
    with timed_stage("Score inventory risk", timings):
        inventory_risk = build_inventory_risk(tables, forecast)
    with timed_stage("Recommend staffing", timings):
        staffing = recommend_staffing(forecast)
    with timed_stage("Build action list", timings):
        actions = action_list(inventory_risk, staffing)
    return tables, features, forecast, mae, inventory_risk, staffing, actions, pd.DataFrame(timings), source, warning


def metric_card(label: str, value: str, help_text: str | None = None):
    st.metric(label=label, value=value, help=help_text)


def main() -> None:
    st.title("Pantry Pulse")
    st.caption("Demand forecasting, inventory risk scoring, and volunteer scheduling for community pantries.")

    with st.sidebar:
        st.header("Settings")
        use_bigquery = st.toggle("Read from BigQuery", value=os.getenv("USE_BIGQUERY", "false").lower() == "true")
        forecast_days = st.slider("Forecast horizon", 7, 21, 14)
        st.divider()
        st.subheader("Acceleration")
        st.write(f"Engine: **{ACCELERATION.engine}**")
        st.caption(ACCELERATION.note)
        
        benchmark_path = ROOT / "benchmark_result.txt"
        if benchmark_path.exists():
            st.caption("Last acceleration benchmark:")
            st.code(benchmark_path.read_text())
        else:
            st.caption("Run `python scripts/benchmark_acceleration.py` to generate acceleration evidence.")

        data_path = Path("data")
        if not data_path.exists():
            st.warning("Sample data is missing. Run `python scripts/generate_sample_data.py`.")

    tables, features, forecast, mae, inventory_risk, staffing, actions, timings, source, warning = run_pipeline(
        use_bigquery=use_bigquery,
        forecast_days=forecast_days,
    )
    if warning:
        st.warning(f"{warning} Showing local sample data instead.")
    st.caption(f"Data source: {source}")

    latest = features.sort_values("date").iloc[-1]
    next_7 = forecast.head(7)
    high_risk_count = int((inventory_risk["risk_level"].astype(str) == "High").sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Visitors yesterday", f"{int(latest['visitors'])}")
    with col2:
        metric_card("7-day forecast", f"{int(next_7['predicted_visitors'].sum())}")
    with col3:
        metric_card("High-risk items", f"{high_risk_count}")
    with col4:
        metric_card("Model MAE", f"{mae:.1f}", "Mean absolute error on the holdout period.")

    st.subheader("Demand Forecast")
    history = features.tail(45)[["date", "visitors"]].rename(columns={"visitors": "people"})
    history["series"] = "Actual"
    future = forecast[["date", "predicted_visitors"]].rename(columns={"predicted_visitors": "people"})
    future["series"] = "Forecast"
    demand_chart = pd.concat([history, future], ignore_index=True)
    st.plotly_chart(
        px.line(
            demand_chart,
            x="date",
            y="people",
            color="series",
            markers=True,
            title="Actual vs Forecast Pantry Visitors",
        ),
        use_container_width=True,
    )

    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Inventory Stockout Risk")
        risk_chart = inventory_risk.copy()
        risk_chart["stockout_risk_pct"] = (risk_chart["stockout_risk"] * 100).round(1)
        st.plotly_chart(
            px.bar(
                risk_chart,
                x="category",
                y="stockout_risk_pct",
                color="risk_level",
                text="stockout_risk_pct",
                title="Risk by Item Category",
                color_discrete_map={"Low": "#16a34a", "Medium": "#f59e0b", "High": "#dc2626"},
            ),
            use_container_width=True,
        )
        st.dataframe(
            risk_chart[
                ["category", "stock_kg", "expected_7d_need_kg", "coverage_ratio", "risk_level"]
            ].round(2),
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.subheader("Volunteer Staffing")
        st.plotly_chart(
            px.bar(
                staffing,
                x="date",
                y="recommended_volunteers",
                color="service_load",
                text="recommended_volunteers",
                title="Recommended Volunteers by Day",
                color_discrete_map={"Normal": "#2563eb", "Busy": "#f59e0b", "Surge": "#dc2626"},
            ),
            use_container_width=True,
        )
        st.dataframe(staffing, use_container_width=True, hide_index=True)

    st.subheader("Recommended Actions")
    st.dataframe(actions, use_container_width=True, hide_index=True)
    st.download_button(
        "Download action list",
        actions.to_csv(index=False).encode("utf-8"),
        file_name="pantry_pulse_actions.csv",
        mime="text/csv",
    )

    st.subheader("Pipeline Acceleration Evidence")
    total_seconds = timings["seconds"].sum()
    baseline_note = "GPU speedup depends on dataset size and hardware. RAPIDS is most valuable when BigQuery exports millions of rows to GPU-backed processing."
    accel_label = "RAPIDS active" if ACCELERATION.enabled else "CPU fallback"
    st.write(f"Current run: **{accel_label}**, total pipeline time: **{total_seconds:.3f}s**.")
    st.caption(baseline_note)
    st.dataframe(timings, use_container_width=True, hide_index=True)

    st.subheader("Data Pipeline")
    st.markdown(
        """
        Cloud Storage lands raw CSVs, BigQuery stores cleaned analytical tables, and this app reads either BigQuery or local sample data. 
        RAPIDS/cuDF accelerates dataframe cleaning and feature generation in a CUDA environment, then the app produces a forecast, risk score, and action list.
        """
    )


if __name__ == "__main__":
    main()
