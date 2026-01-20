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
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Financial District)' WHERE venue_name = 'Five Iron Golf (NYC - FiDi)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Flatiron)' WHERE venue_name = 'Five Iron Golf (NYC - Flatiron)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Midtown East)' WHERE venue_name = 'Five Iron Golf (NYC - Grand Central)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Midtown East)' WHERE venue_name = 'Five Iron Golf (NYC - Midtown East)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Herald Square)' WHERE venue_name = 'Five Iron Golf (NYC - Herald Square)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Long Island City)' WHERE venue_name = 'Five Iron Golf (NYC - Long Island City)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Upper East Side)' WHERE venue_name = 'Five Iron Golf (NYC - Upper East Side)';
UPDATE availability_slots SET venue_name = 'Five Iron Golf (Rockefeller Center)' WHERE venue_name = 'Five Iron Golf (NYC - Rockefeller Center)';

-- SPIN venues
UPDATE availability_slots SET venue_name = 'SPIN (Flatiron)' WHERE venue_name = 'SPIN (NYC - Flatiron)';
UPDATE availability_slots SET venue_name = 'SPIN (Midtown East)' WHERE venue_name = 'SPIN (NYC - Midtown)';

-- Swingers venues
UPDATE availability_slots SET venue_name = 'Swingers (Nomad)' WHERE venue_name = 'Swingers (NYC)';
UPDATE availability_slots SET venue_name = 'Swingers (Oxford Circus)' WHERE venue_name = 'Swingers (London)';

-- Electric Shuffle venues
UPDATE availability_slots SET venue_name = 'Electric Shuffle (Nomad)' WHERE venue_name = 'Electric Shuffle (NYC)';
UPDATE availability_slots SET venue_name = 'Electric Shuffle (Canary Wharf)' WHERE venue_name = 'Electric Shuffle (London)' AND city = 'London';

-- Puttery
UPDATE availability_slots SET venue_name = 'Puttery (Meatpacking)' WHERE venue_name = 'Puttery (NYC)';

-- T-Squared Social
UPDATE availability_slots SET venue_name = 'T-Squared Social (Midtown East)' WHERE venue_name = 'T-Squared Social';

-- Chelsea Piers
UPDATE availability_slots SET venue_name = 'Chelsea Piers (Chelsea)' WHERE venue_name = 'Chelsea Piers Golf';

-- Bounce
UPDATE availability_slots SET venue_name = 'Bounce (Farringdon)' WHERE venue_name = 'Bounce';

-- F1 Arcade
UPDATE availability_slots SET venue_name = 'F1 Arcade (St Paul''s)' WHERE venue_name = 'F1 Arcade';

-- Hijingo
UPDATE availability_slots SET venue_name = 'Hijingo (Shoreditch)' WHERE venue_name = 'Hijingo';

-- Topgolf
UPDATE availability_slots SET venue_name = 'Topgolf (Chigwell)' WHERE venue_name = 'Topgolf Chigwell';

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
