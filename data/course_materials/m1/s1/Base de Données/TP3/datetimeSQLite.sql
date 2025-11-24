-- Manipulation des données de type datetime en SQLite

-- 1. Formatting dates
-- Extract date in YYYY-MM-DD format
SELECT event_name, date(event_datetime) as event_date
FROM events;

-- Extract time in HH:MM:SS format
SELECT event_name, time(event_datetime) as event_time
FROM events;

-- Custom date format (e.g., DD/MM/YYYY)
SELECT event_name, strftime('%d/%m/%Y', event_datetime) as formatted_date
FROM events;

-- 2. Date arithmetic
-- Add days to a date
SELECT event_name, event_datetime, 
       date(event_datetime, '+7 days') as week_later
FROM events;

-- Subtract days from a date
SELECT event_name, event_datetime, 
       date(event_datetime, '-1 month') as month_before
FROM events;

-- Calculate end time of events
SELECT event_name, event_datetime, 
       datetime(event_datetime, '+' || duration_minutes || ' minutes') as end_time
FROM events;

-- 3. Extracting parts of dates
-- Extract year, month, day
SELECT event_name, 
       strftime('%Y', event_datetime) as year,
       strftime('%m', event_datetime) as month,
       strftime('%d', event_datetime) as day
FROM events;

-- Extract hour, minute, second
SELECT event_name, 
       strftime('%H', event_datetime) as hour,
       strftime('%M', event_datetime) as minute,
       strftime('%S', event_datetime) as second
FROM events;

-- Get day of week (0 = Sunday, 6 = Saturday)
SELECT event_name, event_datetime,
       strftime('%w', event_datetime) as day_of_week
FROM events;

-- 4. Date comparisons
-- Events in the future (assuming current date is 2023-07-01)
SELECT event_name, event_datetime
FROM events
WHERE date(event_datetime) > date('2023-07-01');

-- Events in a specific month
SELECT event_name, event_datetime
FROM events
WHERE strftime('%m', event_datetime) = '12';

-- 5. Date differences
-- Calculate days between events and a reference date
SELECT event_name, event_datetime,
       julianday(event_datetime) - julianday('2023-01-01') as days_since_new_year
FROM events;

-- 6. Working with current date and time
-- Current date and time
SELECT datetime('now') as current_datetime;

-- Current date and time in UTC
SELECT datetime('now', 'utc') as current_utc_datetime;

-- 7. Date ranges
-- Events within a date range
SELECT event_name, event_datetime
FROM events
WHERE date(event_datetime) BETWEEN date('2023-06-01') AND date('2023-12-31');

-- 8. Grouping by date parts
-- Count of events by month
SELECT strftime('%m', event_datetime) as month,
       COUNT(*) as event_count
FROM events
GROUP BY strftime('%m', event_datetime)
ORDER BY month;

-- 9. Complex date calculations
-- Calculate the next occurrence of an event (assuming it's annual)
SELECT event_name, event_datetime,
       CASE 
           WHEN date(event_datetime, '+1 year') <= date('now')
           THEN date(event_datetime, '+2 year')
           ELSE date(event_datetime, '+1 year')
       END as next_occurrence
FROM events;

-- 10. Working with time zones (SQLite doesn't have built-in timezone support, but we can simulate it)
-- Convert local time to UTC (assuming events are in EST, which is UTC-5)
SELECT event_name, event_datetime as local_time,
       datetime(event_datetime, '+5 hours') as utc_time
FROM events;