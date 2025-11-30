# Database Check Guide - SQLite

This guide shows you how to manually check if data has been saved to the SQLite database.

## Database Location

The SQLite database file is located at:
```
/opt/scrapping/availability.db
```

Or in your project directory:
```
availability.db
```

## Connect to SQLite Database

### Option 1: Using sqlite3 command line tool

```bash
# Navigate to project directory
cd /opt/scrapping

# Connect to database
sqlite3 availability.db
```

### Option 2: Using sqlite3 with full path

```bash
sqlite3 /opt/scrapping/availability.db
```

---

## Basic Database Queries

### 1. Check Total Number of Records

```sql
-- Count all slots
SELECT COUNT(*) FROM availability_slots;

-- Count by status
SELECT status, COUNT(*) as count 
FROM availability_slots 
GROUP BY status 
ORDER BY count DESC;
```

### 2. Check Data by City

```sql
-- Count slots by city
SELECT city, COUNT(*) as total_slots 
FROM availability_slots 
GROUP BY city;

-- View all NYC slots
SELECT * FROM availability_slots 
WHERE UPPER(city) = 'NYC' 
ORDER BY venue_name, date DESC, time 
LIMIT 50;

-- View all London slots
SELECT * FROM availability_slots 
WHERE UPPER(city) = 'LONDON' 
ORDER BY venue_name, date DESC, time 
LIMIT 50;
```

### 3. Check Data by Venue

```sql
-- List all venues and their slot counts
SELECT venue_name, city, COUNT(*) as slot_count 
FROM availability_slots 
GROUP BY venue_name, city 
ORDER BY slot_count DESC;

-- View slots for a specific venue
SELECT * FROM availability_slots 
WHERE venue_name = 'Swingers (NYC)' 
ORDER BY date DESC, time 
LIMIT 20;
```

### 4. Check Recent Data

```sql
-- View most recently added/updated slots
SELECT venue_name, city, date, time, status, guests, last_updated 
FROM availability_slots 
ORDER BY last_updated DESC 
LIMIT 20;

-- View slots added today
SELECT venue_name, city, date, time, status, guests 
FROM availability_slots 
WHERE DATE(last_updated) = DATE('now') 
ORDER BY last_updated DESC;
```

### 5. Check Data by Date

```sql
-- View slots for a specific date
SELECT venue_name, city, time, status, price, guests 
FROM availability_slots 
WHERE date = '2025-12-01' 
ORDER BY venue_name, time;

-- View slots for date range
SELECT venue_name, city, date, time, status, guests 
FROM availability_slots 
WHERE date BETWEEN '2025-12-01' AND '2025-12-31' 
ORDER BY date, venue_name, time 
LIMIT 100;
```

### 6. Check Available Slots Only

```sql
-- Count available slots by city
SELECT city, COUNT(*) as available_slots 
FROM availability_slots 
WHERE UPPER(status) LIKE '%AVAILABLE%' 
GROUP BY city;

-- View available slots for NYC
SELECT venue_name, date, time, price, guests 
FROM availability_slots 
WHERE UPPER(city) = 'NYC' 
  AND UPPER(status) LIKE '%AVAILABLE%' 
ORDER BY venue_name, date, time 
LIMIT 50;
```

### 7. Check Data by Guest Count

```sql
-- Count slots by guest count
SELECT guests, COUNT(*) as count 
FROM availability_slots 
GROUP BY guests 
ORDER BY guests;

-- View slots for 6 guests
SELECT venue_name, city, date, time, status, price 
FROM availability_slots 
WHERE guests = 6 
ORDER BY city, venue_name, date, time 
LIMIT 50;
```

### 8. Check Scraping Tasks

```sql
-- View recent scraping tasks
SELECT task_id, website, status, total_slots_found, created_at, completed_at 
FROM scraping_tasks 
ORDER BY created_at DESC 
LIMIT 20;

-- View successful tasks
SELECT website, status, total_slots_found, created_at 
FROM scraping_tasks 
WHERE status = 'SUCCESS' 
ORDER BY created_at DESC 
LIMIT 10;

-- View failed tasks
SELECT website, status, error, created_at 
FROM scraping_tasks 
WHERE status = 'FAILURE' 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## Quick Verification Queries

### Check if data exists at all:

```sql
SELECT COUNT(*) as total_slots FROM availability_slots;
```

### Check latest data timestamp:

```sql
SELECT MAX(last_updated) as latest_update FROM availability_slots;
```

### Check data distribution:

```sql
SELECT 
    city,
    COUNT(DISTINCT venue_name) as venue_count,
    COUNT(*) as total_slots,
    SUM(CASE WHEN UPPER(status) LIKE '%AVAILABLE%' THEN 1 ELSE 0 END) as available_slots
FROM availability_slots 
GROUP BY city;
```

### Check specific venue data:

```sql
-- Replace 'Venue Name' with actual venue name
SELECT 
    date,
    COUNT(*) as slots,
    SUM(CASE WHEN UPPER(status) LIKE '%AVAILABLE%' THEN 1 ELSE 0 END) as available
FROM availability_slots 
WHERE venue_name = 'Swingers (NYC)' 
GROUP BY date 
ORDER BY date DESC 
LIMIT 10;
```

---

## Useful SQLite Commands

### List all tables:

```sql
.tables
```

### Describe table structure:

```sql
.schema availability_slots
.schema scraping_tasks
```

### Show table info:

```sql
PRAGMA table_info(availability_slots);
```

### Exit SQLite:

```sql
.quit
-- or
.exit
```

### Show database file info:

```sql
.dbinfo
```

### Enable column headers:

```sql
.headers on
```

### Enable column mode (better formatting):

```sql
.mode column
.width 20 15 12 10 15
```

---

## Example: Complete Data Check

```sql
.headers on
.mode column

-- Comprehensive data overview
SELECT 
    'Total Slots' as metric,
    COUNT(*) as value
FROM availability_slots

UNION ALL

SELECT 
    'Total Venues',
    COUNT(DISTINCT venue_name)
FROM availability_slots

UNION ALL

SELECT 
    'NYC Slots',
    COUNT(*)
FROM availability_slots
WHERE UPPER(city) = 'NYC'

UNION ALL

SELECT 
    'London Slots',
    COUNT(*)
FROM availability_slots
WHERE UPPER(city) = 'LONDON'

UNION ALL

SELECT 
    'Available Slots',
    COUNT(*)
FROM availability_slots
WHERE UPPER(status) LIKE '%AVAILABLE%'

UNION ALL

SELECT 
    'Latest Update',
    MAX(last_updated)
FROM availability_slots;
```

---

## Quick One-Liners (from terminal)

```bash
# Count total slots
sqlite3 /opt/scrapping/availability.db "SELECT COUNT(*) FROM availability_slots;"

# Count by city
sqlite3 /opt/scrapping/availability.db "SELECT city, COUNT(*) FROM availability_slots GROUP BY city;"

# View latest 10 slots
sqlite3 /opt/scrapping/availability.db "SELECT venue_name, city, date, time, status FROM availability_slots ORDER BY last_updated DESC LIMIT 10;"

# Check if database file exists and its size
ls -lh /opt/scrapping/availability.db
```

---

## Export Data

### Export to CSV:

```sql
.headers on
.mode csv
.output /tmp/slots_export.csv
SELECT * FROM availability_slots;
.output stdout
```

### Export from command line:

```bash
# Export all slots to CSV
sqlite3 -header -csv /opt/scrapping/availability.db "SELECT * FROM availability_slots;" > /tmp/slots_export.csv

# Export available slots only
sqlite3 -header -csv /opt/scrapping/availability.db "SELECT * FROM availability_slots WHERE UPPER(status) LIKE '%AVAILABLE%';" > /tmp/available_slots.csv
```

---

## Troubleshooting

### If database file doesn't exist:

The database is created automatically when Flask starts. Make sure:
1. Flask service is running: `sudo systemctl status scrapping-flask`
2. Check Flask logs for errors: `sudo journalctl -u scrapping-flask -n 50`

### If you get "database is locked":

This usually means another process is using the database. Check:
```bash
# Check if Flask/Celery processes are running
ps aux | grep python

# Check database file permissions
ls -l /opt/scrapping/availability.db
```

### Backup database:

```bash
# Simple copy
cp /opt/scrapping/availability.db /opt/scrapping/availability_backup_$(date +%Y%m%d).db

# Or use sqlite3 backup command
sqlite3 /opt/scrapping/availability.db ".backup /opt/scrapping/availability_backup_$(date +%Y%m%d).db"
```

### Restore database:

```bash
cp /opt/scrapping/availability_backup_YYYYMMDD.db /opt/scrapping/availability.db
```

---

## Database File Location

The SQLite database file is stored at:
- **Production**: `/opt/scrapping/availability.db`
- **Development**: `./availability.db` (in project root)

Make sure to backup this file regularly!
