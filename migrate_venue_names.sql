-- Migration script to update venue names from old format to new format
-- Old format: "Venue Name (City - Location)"
-- New format: "Venue Name (Location)"

-- IMPORTANT: Backup your database before running these commands!
-- sqlite3 availability.db ".backup backup_before_migration.db"

-- ============================================
-- Step 1: Check current venue names (run this first to see what needs updating)
-- ============================================
-- SELECT DISTINCT venue_name FROM availability_slots ORDER BY venue_name;

-- ============================================
-- Step 2: Update venue names with "NYC - " pattern
-- ============================================

-- Five Iron Golf venues
UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Financial District)' 
WHERE venue_name = 'Five Iron Golf (NYC - FiDi)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Flatiron)' 
WHERE venue_name = 'Five Iron Golf (NYC - Flatiron)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Midtown East)' 
WHERE venue_name = 'Five Iron Golf (NYC - Grand Central)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Midtown East)' 
WHERE venue_name = 'Five Iron Golf (NYC - Midtown East)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Herald Square)' 
WHERE venue_name = 'Five Iron Golf (NYC - Herald Square)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Long Island City)' 
WHERE venue_name = 'Five Iron Golf (NYC - Long Island City)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Upper East Side)' 
WHERE venue_name = 'Five Iron Golf (NYC - Upper East Side)';

UPDATE availability_slots 
SET venue_name = 'Five Iron Golf (Rockefeller Center)' 
WHERE venue_name = 'Five Iron Golf (NYC - Rockefeller Center)';

-- SPIN venues
UPDATE availability_slots 
SET venue_name = 'SPIN (Flatiron)' 
WHERE venue_name = 'SPIN (NYC - Flatiron)';

UPDATE availability_slots 
SET venue_name = 'SPIN (Midtown East)' 
WHERE venue_name = 'SPIN (NYC - Midtown)';

-- ============================================
-- Step 3: Update venue names with "London - " pattern (if any exist)
-- ============================================

-- Note: Most London venues don't have the "London - " pattern, but check first:
-- SELECT DISTINCT venue_name FROM availability_slots WHERE venue_name LIKE '%(London - %';

-- If any exist, update them similarly:
-- UPDATE availability_slots 
-- SET venue_name = REPLACE(venue_name, '(London - ', '(')
-- WHERE venue_name LIKE '%(London - %';

-- ============================================
-- Step 4: Update specific venue names from CSV format
-- ============================================

-- Swingers venues
UPDATE availability_slots 
SET venue_name = 'Swingers (Nomad)' 
WHERE venue_name = 'Swingers (NYC)';

UPDATE availability_slots 
SET venue_name = 'Swingers (Oxford Circus)' 
WHERE venue_name = 'Swingers (London)';

-- Electric Shuffle venues
UPDATE availability_slots 
SET venue_name = 'Electric Shuffle (Nomad)' 
WHERE venue_name = 'Electric Shuffle (NYC)';

-- Note: Electric Shuffle (London) has multiple locations - update based on which location is scraped
-- If only one location exists in DB, update to that location, otherwise may need separate handling
UPDATE availability_slots 
SET venue_name = 'Electric Shuffle (Canary Wharf)' 
WHERE venue_name = 'Electric Shuffle (London)' AND city = 'London';

-- Puttery
UPDATE availability_slots 
SET venue_name = 'Puttery (Meatpacking)' 
WHERE venue_name = 'Puttery (NYC)';

-- T-Squared Social
UPDATE availability_slots 
SET venue_name = 'T-Squared Social (Midtown East)' 
WHERE venue_name = 'T-Squared Social';

-- Chelsea Piers
UPDATE availability_slots 
SET venue_name = 'Chelsea Piers (Chelsea)' 
WHERE venue_name = 'Chelsea Piers Golf';

-- Bounce
UPDATE availability_slots 
SET venue_name = 'Bounce (Farringdon)' 
WHERE venue_name = 'Bounce';

-- F1 Arcade
UPDATE availability_slots 
SET venue_name = 'F1 Arcade (St Paul''s)' 
WHERE venue_name = 'F1 Arcade';

-- Hijingo
UPDATE availability_slots 
SET venue_name = 'Hijingo (Shoreditch)' 
WHERE venue_name = 'Hijingo';

-- Topgolf
UPDATE availability_slots 
SET venue_name = 'Topgolf (Chigwell)' 
WHERE venue_name = 'Topgolf Chigwell';

-- Lawn Club venues should be updated to "The Lawn Club (Financial District)"
-- Based on the requirements, all Lawn Club venues should show as "The Lawn Club (Financial District)"
-- with activities shown separately
UPDATE availability_slots 
SET venue_name = 'The Lawn Club (Financial District)' 
WHERE venue_name LIKE 'Lawn Club (%';

-- ============================================
-- Step 5: Generic update for any remaining "NYC - " patterns
-- ============================================

-- This catches any venue names we might have missed
UPDATE availability_slots 
SET venue_name = REPLACE(venue_name, '(NYC - ', '(')
WHERE venue_name LIKE '%(NYC - %';

-- ============================================
-- Step 6: Generic update for any remaining "London - " patterns
-- ============================================

UPDATE availability_slots 
SET venue_name = REPLACE(venue_name, '(London - ', '(')
WHERE venue_name LIKE '%(London - %';

-- ============================================
-- Step 7: Verify the changes
-- ============================================

-- Check for any remaining old format patterns
-- SELECT DISTINCT venue_name FROM availability_slots 
-- WHERE venue_name LIKE '%(NYC - %' OR venue_name LIKE '%(London - %'
-- ORDER BY venue_name;

-- View updated venue names
-- SELECT DISTINCT venue_name FROM availability_slots ORDER BY venue_name;

-- Count records by venue name
-- SELECT venue_name, COUNT(*) as count FROM availability_slots 
-- GROUP BY venue_name ORDER BY venue_name;
