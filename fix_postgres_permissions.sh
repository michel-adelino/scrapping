#!/bin/bash
# Fix PostgreSQL permissions for the database user

echo "Fixing PostgreSQL permissions..."

# Read database credentials from .env file if it exists
if [ -f /opt/scrapping/.env ]; then
    source /opt/scrapping/.env
    DB_USER=$(echo $DATABASE_URL | grep -oP 'postgresql://\K[^:]+')
    DB_NAME=$(echo $DATABASE_URL | grep -oP 'postgresql://[^:]+:[^@]+@[^:]+:[^/]+/\K[^?]+')
else
    echo "Please enter database user name (default: scrapping_user):"
    read -r DB_USER
    DB_USER=${DB_USER:-scrapping_user}
    
    echo "Please enter database name (default: scrapping_db):"
    read -r DB_NAME
    DB_NAME=${DB_NAME:-scrapping_db}
fi

echo "Granting permissions to user: $DB_USER on database: $DB_NAME"

# Grant permissions on the database
sudo -u postgres psql -d $DB_NAME << EOF
-- Grant usage on schema public
GRANT USAGE ON SCHEMA public TO $DB_USER;

-- Grant create privilege on schema public
GRANT CREATE ON SCHEMA public TO $DB_USER;

-- Grant all privileges on all tables in schema public
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;

-- Grant all privileges on all sequences in schema public
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- Make the user the owner of the database (alternative approach)
-- ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF

echo "Permissions granted successfully!"
echo "Restarting Flask service..."
sudo systemctl restart scrapping-flask

echo "Check status with: sudo systemctl status scrapping-flask"

