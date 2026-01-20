-- Verification SQL queries to check all venue names are correct after migration
-- Run these queries after executing the migration scripts

-- ============================================
-- 1. Check for any remaining old format patterns
-- ============================================
SELECT DISTINCT venue_name 
FROM availability_slots 
WHERE venue_name LIKE '%(NYC - %' 
   OR venue_name LIKE '%(London - %'
ORDER BY venue_name;

-- ============================================
-- 2. Verify all venue names match new format
-- ============================================
SELECT DISTINCT venue_name 
FROM availability_slots 
ORDER BY venue_name;

-- ============================================
-- 3. Count records by venue name
-- ============================================
SELECT venue_name, COUNT(*) as count 
FROM availability_slots 
GROUP BY venue_name 
ORDER BY venue_name;

-- ============================================
-- 4. Check specific venue name updates
-- ============================================
-- NYC Venues
SELECT 'Swingers (Nomad)' as expected, COUNT(*) as actual_count
FROM availability_slots 
WHERE venue_name = 'Swingers (Nomad)'
UNION ALL
SELECT 'Electric Shuffle (Nomad)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Electric Shuffle (Nomad)'
UNION ALL
SELECT 'Puttery (Meatpacking)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Puttery (Meatpacking)'
UNION ALL
SELECT 'T-Squared Social (Midtown East)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'T-Squared Social (Midtown East)'
UNION ALL
SELECT 'Chelsea Piers (Chelsea)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Chelsea Piers (Chelsea)'
UNION ALL
SELECT 'Five Iron Golf (Financial District)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Five Iron Golf (Financial District)'
UNION ALL
SELECT 'Five Iron Golf (Flatiron)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Five Iron Golf (Flatiron)'
UNION ALL
SELECT 'Five Iron Golf (Midtown East)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Five Iron Golf (Midtown East)'
UNION ALL
SELECT 'SPIN (Flatiron)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'SPIN (Flatiron)'
UNION ALL
SELECT 'SPIN (Midtown East)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'SPIN (Midtown East)';

-- London Venues
SELECT 'Swingers (Oxford Circus)' as expected, COUNT(*) as actual_count
FROM availability_slots 
WHERE venue_name = 'Swingers (Oxford Circus)'
UNION ALL
SELECT 'Electric Shuffle (Canary Wharf)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Electric Shuffle (Canary Wharf)'
UNION ALL
SELECT 'Electric Shuffle (London Bridge)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Electric Shuffle (London Bridge)'
UNION ALL
SELECT 'Electric Shuffle (King''s Cross)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Electric Shuffle (King''s Cross)'
UNION ALL
SELECT 'Bounce (Farringdon)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Bounce (Farringdon)'
UNION ALL
SELECT 'Bounce (Shoreditch)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Bounce (Shoreditch)'
UNION ALL
SELECT 'F1 Arcade (St Paul''s)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'F1 Arcade (St Paul''s)'
UNION ALL
SELECT 'Hijingo (Shoreditch)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Hijingo (Shoreditch)'
UNION ALL
SELECT 'Topgolf (Chigwell)', COUNT(*)
FROM availability_slots 
WHERE venue_name = 'Topgolf (Chigwell)';

-- ============================================
-- 5. Check for any unexpected venue names
-- ============================================
-- This query will help identify any venue names that might have been missed
SELECT DISTINCT venue_name 
FROM availability_slots 
WHERE venue_name NOT IN (
    -- NYC Venues
    'Swingers (Nomad)',
    'Electric Shuffle (Nomad)',
    'Puttery (Meatpacking)',
    'T-Squared Social (Midtown East)',
    'Chelsea Piers (Chelsea)',
    'Five Iron Golf (Financial District)',
    'Five Iron Golf (Flatiron)',
    'Five Iron Golf (Midtown East)',
    'Five Iron Golf (Herald Square)',
    'Five Iron Golf (Long Island City)',
    'Five Iron Golf (Upper East Side)',
    'Five Iron Golf (Rockefeller Center)',
    'SPIN (Flatiron)',
    'SPIN (Midtown East)',
    'Lucky Strike (Chelsea Piers)',
    'Lucky Strike (Times Square)',
    'Easybowl (NYC)',
    'Kick Axe (Brooklyn)',
    'The Lawn Club (Financial District)',
    'Lawn Club (Indoor Gaming)',
    'Lawn Club (Curling Lawns)',
    'Lawn Club (Croquet Lawns)',
    -- London Venues
    'Swingers (Oxford Circus)',
    'Electric Shuffle (Canary Wharf)',
    'Electric Shuffle (London Bridge)',
    'Electric Shuffle (King''s Cross)',
    'Bounce (Farringdon)',
    'Bounce (Shoreditch)',
    'F1 Arcade (St Paul''s)',
    'Hijingo (Shoreditch)',
    'Topgolf (Chigwell)',
    'Puttshack (Bank)',
    'Puttshack (Lakeside)',
    'Puttshack (White City)',
    'Puttshack (Watford)',
    'Flight Club Darts (Shoreditch)',
    'Flight Club Darts (Bloomsbury)',
    'Flight Club Darts (Victoria)',
    'Flight Club Darts (Angel)',
    'Clays Bar (Canary Wharf)',
    'Clays Bar (The City)',
    'Clays Bar (Soho)',
    'Fair Game (Canary Wharf)',
    'Fair Game (City)',
    'All Star Lanes (Holborn)',
    'All Star Lanes (Shoreditch)',
    'All Star Lanes (White City)',
    'All Star Lanes (Stratford)'
)
ORDER BY venue_name;
