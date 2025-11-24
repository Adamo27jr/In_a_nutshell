import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Create a connection to a new SQLite database
conn = sqlite3.connect('weather_data.db')
c = conn.cursor()

# Create a table for our time series data
c.execute('''CREATE TABLE IF NOT EXISTS daily_temperatures
           (date TEXT PRIMARY KEY,
            temperature REAL,
            precipitation REAL)''')

# Generate some sample data
start_date = datetime(2022, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(365)]
temperatures = np.random.normal(15, 5, 365)  # Mean of 15°C, std dev of 5°C
precipitation = np.random.exponential(1, 365)  # Exponential distribution for precipitation

# Insert the sample data
for date, temp, precip in zip(dates, temperatures, precipitation):
  c.execute("INSERT INTO daily_temperatures VALUES (?, ?, ?)",
            (date.strftime('%Y-%m-%d'), temp, precip))

conn.commit()
