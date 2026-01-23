#!/bin/bash
# Bash script to migrate Lawn Club venue names in SQLite database
# This script updates venue names from "Lawn Club (Activity)" to "The Lawn Club (Activity)"

DB_PATH="availability.db"

if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file '$DB_PATH' not found!"
    exit 1
fi

echo "Starting Lawn Club venue name migration..."
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
-- Update from "Lawn Club (Activity)" to "The Lawn Club (Activity)"

-- Update Indoor Gaming
UPDATE availability_slots 
SET venue_name = 'The Lawn Club (Indoor Gaming)' 
WHERE venue_name = 'Lawn Club (Indoor Gaming)';

-- Update Curling Lawns
UPDATE availability_slots 
SET venue_name = 'The Lawn Club (Curling Lawns)' 
WHERE venue_name = 'Lawn Club (Curling Lawns)';

-- Update Croquet Lawns
UPDATE availability_slots 
SET venue_name = 'The Lawn Club (Croquet Lawns)' 
WHERE venue_name = 'Lawn Club (Croquet Lawns)';
EOF

echo ""
echo "Migration completed!"
echo "Backup saved as: $BACKUP_PATH"
echo ""
echo "Verifying changes..."

# Verify - check updated venue names
sqlite3 "$DB_PATH" <<EOF
SELECT DISTINCT venue_name, COUNT(*) as count 
FROM availability_slots 
WHERE venue_name LIKE '%Lawn Club%' 
GROUP BY venue_name 
ORDER BY venue_name;
EOF

echo ""
echo "Migration script completed successfully!"
