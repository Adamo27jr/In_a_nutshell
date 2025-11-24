-- Time series DB 
-- View 1: Monthly average temperature and total precipitation
CREATE VIEW monthly_summary AS
SELECT 
    strftime('%Y-%m', date) as month,
    AVG(temperature) as avg_temperature,
    SUM(precipitation) as total_precipitation
FROM daily_temperatures
GROUP BY strftime('%Y-%m', date);

-- View 2: 7-day moving average for temperature
CREATE VIEW temperature_moving_avg AS
SELECT 
    date,
    temperature,
    AVG(temperature) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_temp
FROM daily_temperatures;

-- View 3: Temperature anomalies (difference from monthly mean)
CREATE VIEW temperature_anomalies AS
SELECT 
    dt.date,
    dt.temperature,
    dt.temperature - ms.avg_temperature as temperature_anomaly
FROM daily_temperatures dt
JOIN monthly_summary ms ON strftime('%Y-%m', dt.date) = ms.month;

-- View 4: Seasonal decomposition (very simplified)
CREATE VIEW seasonal_decomposition AS
SELECT 
    date,
    temperature,
    AVG(temperature) OVER (
        ORDER BY strftime('%j', date)
        ROWS BETWEEN 15 PRECEDING AND 15 FOLLOWING
    ) as trend,
    temperature - AVG(temperature) OVER (
        ORDER BY strftime('%j', date)
        ROWS BETWEEN 15 PRECEDING AND 15 FOLLOWING
    ) as seasonal_residual
FROM daily_temperatures;


