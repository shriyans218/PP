CREATE SCHEMA IF NOT EXISTS `pantry-pulse-501417.pantry_pulse`;

CREATE OR REPLACE TABLE `pantry-pulse-501417.pantry_pulse.visits` (
  date DATE,
  household_id INT64,
  has_senior INT64,
  children INT64
);

CREATE OR REPLACE TABLE `pantry-pulse-501417.pantry_pulse.inventory` (
  date DATE,
  category STRING,
  stock_kg FLOAT64,
  is_low_stock INT64
);

CREATE OR REPLACE TABLE `pantry-pulse-501417.pantry_pulse.donations` (
  date DATE,
  donation_id STRING,
  category STRING,
  quantity_kg FLOAT64,
  source STRING
);

CREATE OR REPLACE TABLE `pantry-pulse-501417.pantry_pulse.weather` (
  date DATE,
  temperature_c FLOAT64,
  rain_mm FLOAT64
);

CREATE OR REPLACE TABLE `pantry-pulse-501417.pantry_pulse.events` (
  date DATE,
  event_name STRING,
  demand_pressure FLOAT64
);
