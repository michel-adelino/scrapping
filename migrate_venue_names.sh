#!/bin/bash
# Bash script to migrate venue names in SQLite database
# This script runs the SQL migration commands

DB_PATH="availability.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file '$DB_PATH' not found!"
    exit 1
fi

echo "Starting venue name migration..."
echo "Database: $DB_PATH"

# Backup database first
BACKUP_PATH="availability_backup_$(date +%Y%m%d_%H%M%S).db"
echo "Creating backup: $BACKUP_PATH"
cp "$DB_PATH" "$BACKUP_PATH"
echo "Backup created successfully!"

# Run migration SQL
echo ""
echo "Running migration SQL commands..."

sqlite3 "$DB_PATH" <<EOF
-- Five Iron Golf venues
UPDATE availability_slots SET venue_name = 'Five Iron Golf (FiDi)' WHERE venue_name = 'Five Iron Golf (NYC - FiDi)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Flatiron)' WHERE venue_name = 'Five Iron Golf (NYC - Flatiron)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Grand Central)' WHERE venue_name = 'Five Iron Golf (NYC - Grand Central)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Midtown East)' WHERE venue_name = 'Five Iron Golf (NYC - Midtown East)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Herald Square)' WHERE venue_name = 'Five Iron Golf (NYC - Herald Square)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Long Island City)' WHERE venue_name = 'Five Iron Golf (NYC - Long Island City)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Upper East Side)' WHERE venue_name = 'Five Iron Golf (NYC - Upper East Side)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Rockefeller Center)' WHERE venue_name = 'Five Iron Golf (NYC - Rockefeller Center)';

-- SPIN venues
UPDATE availability_slots SET venue_name = 'SPIN (Flatiron)' WHERE venue_name = 'SPIN (NYC - Flatiron)';
UPDATE availability_slots SET venue_name = 'SPIN (Midtown)' WHERE venue_name = 'SPIN (NYC - Midtown)';

-- Lawn Club venues
UPDATE availability_slots SET venue_name = 'The Lawn Club (Financial District)' WHERE venue_name LIKE 'Lawn Club (%';

-- Generic updates for any remaining patterns
UPDATE availability_slots SET venue_name = REPLACE(venue_name, '(NYC - ', '(') WHERE venue_name LIKE '%(NYC - %';
UPDATE availability_slots SET venue_name = REPLACE(venue_name, '(London - ', '(') WHERE venue_name LIKE '%(London - %';
EOF

echo ""
echo "Migration completed!"
echo "Backup saved as: $BACKUP_PATH"
echo ""
echo "Verifying changes..."

# Verify - check for any remaining old patterns
REMAINING=$(sqlite3 "$DB_PATH" "SELECT DISTINCT venue_name FROM availability_slots WHERE venue_name LIKE '%(NYC - %' OR venue_name LIKE '%(London - %' ORDER BY venue_name;")

if [ -n "$REMAINING" ]; then
    echo "Warning: Some old format patterns still exist:"
    echo "$REMAINING"
else
    echo "All venue names have been migrated successfully!"
fi

# Show updated venue names
echo ""
echo "Updated venue names:"
sqlite3 "$DB_PATH" "SELECT DISTINCT venue_name FROM availability_slots ORDER BY venue_name;"
