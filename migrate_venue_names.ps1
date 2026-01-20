# PowerShell script to migrate venue names in SQLite database
# This script runs the SQL migration commands

$dbPath = "availability.db"

if (-not (Test-Path $dbPath)) {
    Write-Host "Error: Database file '$dbPath' not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Starting venue name migration..." -ForegroundColor Green
Write-Host "Database: $dbPath" -ForegroundColor Cyan

# Backup database first
$backupPath = "availability_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
Write-Host "Creating backup: $backupPath" -ForegroundColor Yellow
Copy-Item $dbPath $backupPath
Write-Host "Backup created successfully!" -ForegroundColor Green

# Run migration SQL
Write-Host "`nRunning migration SQL commands..." -ForegroundColor Yellow

$sqlCommands = @"
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
"@

# Execute SQL commands
$sqlCommands -split "`n" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("--")) {
        try {
            sqlite3 $dbPath $line
            Write-Host "Executed: $line" -ForegroundColor Gray
        } catch {
            Write-Host "Error executing: $line" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
        }
    }
}

Write-Host "`nMigration completed!" -ForegroundColor Green
Write-Host "Backup saved as: $backupPath" -ForegroundColor Cyan
Write-Host "`nVerifying changes..." -ForegroundColor Yellow

# Verify - check for any remaining old patterns
$verifySql = "SELECT DISTINCT venue_name FROM availability_slots WHERE venue_name LIKE '%(NYC - %' OR venue_name LIKE '%(London - %' ORDER BY venue_name;"
$remaining = sqlite3 $dbPath $verifySql

if ($remaining) {
    Write-Host "Warning: Some old format patterns still exist:" -ForegroundColor Yellow
    Write-Host $remaining
} else {
    Write-Host "All venue names have been migrated successfully!" -ForegroundColor Green
}

# Show updated venue names
Write-Host "`nUpdated venue names:" -ForegroundColor Cyan
sqlite3 $dbPath "SELECT DISTINCT venue_name FROM availability_slots ORDER BY venue_name;"
