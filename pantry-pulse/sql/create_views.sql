CREATE OR REPLACE VIEW `YOUR_PROJECT.pantry_pulse.daily_operations_vw` AS
WITH daily_visits AS (
  SELECT
    date,
    COUNT(DISTINCT household_id) AS visitors,
    COUNT(*) AS household_visits,
    SUM(has_senior) AS senior_households,
    SUM(children) AS children_served
  FROM `YOUR_PROJECT.pantry_pulse.visits`
  GROUP BY date
),
daily_inventory AS (
  SELECT
    date,
    SUM(stock_kg) AS total_stock_kg,
    SUM(is_low_stock) AS low_stock_items
  FROM `YOUR_PROJECT.pantry_pulse.inventory`
  GROUP BY date
),
daily_donations AS (
  SELECT
    date,
    SUM(quantity_kg) AS donation_kg,
    COUNT(*) AS donation_events
  FROM `YOUR_PROJECT.pantry_pulse.donations`
  GROUP BY date
),
daily_events AS (
  SELECT
    date,
    COUNT(*) AS event_count,
    SUM(demand_pressure) AS event_pressure
  FROM `YOUR_PROJECT.pantry_pulse.events`
  GROUP BY date
)
SELECT
  v.date,
  v.visitors,
  v.household_visits,
  v.senior_households,
  v.children_served,
  w.temperature_c,
  w.rain_mm,
  COALESCE(i.total_stock_kg, 0) AS total_stock_kg,
  COALESCE(i.low_stock_items, 0) AS low_stock_items,
  COALESCE(d.donation_kg, 0) AS donation_kg,
  COALESCE(d.donation_events, 0) AS donation_events,
  COALESCE(e.event_count, 0) AS event_count,
  COALESCE(e.event_pressure, 0) AS event_pressure
FROM daily_visits v
LEFT JOIN `YOUR_PROJECT.pantry_pulse.weather` w USING (date)
LEFT JOIN daily_inventory i USING (date)
LEFT JOIN daily_donations d USING (date)
LEFT JOIN daily_events e USING (date);
