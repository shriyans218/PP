# Pantry Pulse

Pantry Pulse is a practical data analytics and decision-support app for a community food pantry, campus pantry, or small NGO that needs to answer one daily question:

> How many visitors should we expect, which items are at risk of running out, and how many volunteers should we schedule?

The app ingests pantry visit, inventory, donation, weather, and event data; cleans and joins it; forecasts near-term demand; creates item-level stockout risk scores; and recommends volunteer staffing levels.

## Why This Matters

Food pantries often work with limited staff, irregular donations, and demand spikes caused by exams, bad weather, holidays, or benefit-payment cycles. Decisions are usually made from spreadsheets and memory. Pantry Pulse turns those records into a dashboard that helps coordinators make faster, better daily decisions.

## Real User

Primary user: a pantry coordinator or student volunteer lead.

Their workflow:

1. Check expected visitors for the next 7 days.
2. Identify high-risk inventory categories.
3. Decide whether to request emergency donations.
4. Schedule enough volunteers for peak days.
5. Export a daily action list for the team.

## Required Technology Coverage

This project uses two or more requested layers:

- Google Cloud data and application layer:
  - BigQuery for analytics tables and production query source.
  - Cloud Storage for raw CSV landing files.
  - Optional Looker Studio dashboard export using the BigQuery views.
- NVIDIA acceleration layer:
  - NVIDIA RAPIDS with `cudf.pandas` / cuDF for accelerated dataframe processing when running on a GPU.
  - CPU pandas fallback for local development.

## Features

- Generates realistic sample data for pantry visits, inventory, donations, events, and weather.
- Loads data from local CSVs or BigQuery.
- Cleans and joins raw records into daily features.
- Forecasts visitors using a lightweight regression model.
- Scores inventory risk by category.
- Recommends volunteer staffing based on expected visitors and event/weather pressure.
- Shows acceleration evidence: measured pipeline runtime and estimated speedup from RAPIDS when available.
- Exports recommended actions as CSV.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/generate_sample_data.py
streamlit run app.py
```

## Vercel Deployment

Vercel does not run Streamlit as a long-lived web server. This repo therefore includes a Vercel-ready static dashboard in `public/` generated from the same analytics pipeline.

```bash
python scripts/build_static_dashboard.py
npx vercel --prod
```

If the Vercel CLI asks you to log in, run:

```bash
npx vercel login
```

For GitHub-based deployment, import this repository in Vercel and keep the default static output. The generated files in `public/` are already included.

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_sample_data.py
streamlit run app.py
```

## Optional GPU / RAPIDS Setup

Install RAPIDS in a CUDA-enabled environment, then run normally:

```bash
pip install -r requirements.txt
pip install -r requirements-cuda.txt
streamlit run app.py
```

When `cudf.pandas` is available, the pipeline imports it before pandas work begins. The dashboard will show whether the accelerated path is active.

## Google Cloud Setup

export GCP_PROJECT="your-project-id"
export BQ_DATASET="pantry_pulse"

# 1. Create dataset + empty tables
bq query --use_legacy_sql=false < sql/create_tables.sql

# 2. Load the CSVs into BigQuery (real data, not just schema)
python scripts/load_bigquery.py

# 3. Create the analytics view
bq query --use_legacy_sql=false < sql/create_views.sql

# 4. Point the app at BigQuery
export USE_BIGQUERY=true
streamlit run app.py

## Project Structure

```text
pantry-pulse/
  app.py
  data/
  scripts/
  sql/
  src/pantry_pulse/
  .github/workflows/
  requirements.txt
  requirements-cuda.txt
  Dockerfile
```

## Submission Notes

This project is intentionally complete but lightweight:

- It runs locally without paid cloud resources.
- It documents a production path using BigQuery and Cloud Storage.
- It demonstrates acceleration with RAPIDS when a GPU environment is available.
- It solves a real operational decision: daily pantry staffing and stockout prevention.
