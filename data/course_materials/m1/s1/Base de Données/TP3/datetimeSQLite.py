# Datetime in SQLite
import sqlite3
import datetime

# Create a connection to a new SQLite database
conn = sqlite3.connect('date_time_example.db')
c = conn.cursor()

# Create a table for our date and time examples
c.execute('''CREATE TABLE IF NOT EXISTS events
           (id INTEGER PRIMARY KEY,
            event_name TEXT,
            event_datetime TEXT,
            duration_minutes INTEGER)''')

# Insert some sample data
sample_data = [
  ('New Year Party', '2023-01-01 00:00:00', 240),
  ('Team Meeting', '2023-03-15 14:30:00', 60),
  ('Product Launch', '2023-06-30 10:00:00', 120),
  ('Annual Conference', '2023-09-22 09:00:00', 480),
  ('Holiday Party', '2023-12-24 18:00:00', 180)
]

c.executemany("INSERT INTO events (event_name, event_datetime, duration_minutes) VALUES (?, ?, ?)", sample_data)
conn.commit()
