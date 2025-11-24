# Python TS Analysis
import matplotlib as plt
import pandas as pd
import sqlite3
import numpy as np
conn = sqlite3.connect('weather_data.db')

# 1. Analyze monthly trends
monthly_data = pd.read_sql_query("SELECT * FROM monthly_summary", conn)
monthly_data['month'] = pd.to_datetime(monthly_data['month'])

plt.figure(figsize=(12, 6))
plt.plot(monthly_data['month'], monthly_data['avg_temperature'])
plt.title('Monthly Average Temperature')
plt.xlabel('Month')
plt.ylabel('Temperature (°C)')
plt.show()

# 2. Visualize the 7-day moving average
moving_avg_data = pd.read_sql_query("SELECT * FROM temperature_moving_avg", conn)
moving_avg_data['date'] = pd.to_datetime(moving_avg_data['date'])

plt.figure(figsize=(12, 6))
plt.plot(moving_avg_data['date'], moving_avg_data['temperature'], label='Daily Temperature')
plt.plot(moving_avg_data['date'], moving_avg_data['moving_avg_temp'], label='7-day Moving Average')
plt.title('Daily Temperature with 7-day Moving Average')
plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.show()

# 3. Analyze temperature anomalies
anomaly_data = pd.read_sql_query("SELECT * FROM temperature_anomalies", conn)
anomaly_data['date'] = pd.to_datetime(anomaly_data['date'])

plt.figure(figsize=(12, 6))
plt.scatter(anomaly_data['date'], anomaly_data['temperature_anomaly'], alpha=0.5)
plt.title('Temperature Anomalies')
plt.xlabel('Date')
plt.ylabel('Temperature Anomaly (°C)')
plt.axhline(y=0, color='r', linestyle='-')
plt.show()

# 4. Perform basic seasonal decomposition
seasonal_data = pd.read_sql_query("SELECT * FROM seasonal_decomposition", conn)
seasonal_data['date'] = pd.to_datetime(seasonal_data['date'])

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

ax1.plot(seasonal_data['date'], seasonal_data['temperature'])
ax1.set_title('Original Time Series')
ax1.set_ylabel('Temperature (°C)')

ax2.plot(seasonal_data['date'], seasonal_data['trend'])
ax2.set_title('Trend')
ax2.set_ylabel('Temperature (°C)')

ax3.plot(seasonal_data['date'], seasonal_data['seasonal_residual'])
ax3.set_title('Seasonal + Residual')
ax3.set_ylabel('Temperature (°C)')

plt.tight_layout()
plt.show()

# 5. Identify extreme weather events
extreme_events = pd.read_sql_query("""
  SELECT date, temperature, precipitation
  FROM daily_temperatures
  WHERE temperature > (SELECT AVG(temperature) + 2 * STDEV(temperature) FROM daily_temperatures)
     OR precipitation > (SELECT AVG(precipitation) + 2 * STDEV(precipitation) FROM daily_temperatures)
""", conn)

print("Extreme Weather Events:")
print(extreme_events)

# Close the database connection
conn.close()
