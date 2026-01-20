# Example PowerShell script to run specific scraping tasks
# All available venues with examples

$baseUrl = "http://localhost:8010/run_scraper"
$defaultDate = "2025-01-15"
$defaultGuests = 6

# ============================================
# NYC VENUES
# ============================================

# Swingers NYC
Write-Host "Example: Swingers NYC" -ForegroundColor Cyan
$body = @{
    website = "swingers_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Electric Shuffle NYC
Write-Host "Example: Electric Shuffle NYC" -ForegroundColor Cyan
$body = @{
    website = "electric_shuffle_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Lawn Club - Indoor Gaming
Write-Host "Example: Lawn Club (Indoor Gaming)" -ForegroundColor Cyan
$body = @{
    website = "lawn_club_nyc_indoor_gaming"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Lawn Club - Curling Lawns
Write-Host "Example: Lawn Club (Curling Lawns)" -ForegroundColor Cyan
$body = @{
    website = "lawn_club_nyc_curling_lawns"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Lawn Club - Croquet Lawns
Write-Host "Example: Lawn Club (Croquet Lawns)" -ForegroundColor Cyan
$body = @{
    website = "lawn_club_nyc_croquet_lawns"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# SPIN (Flatiron)
Write-Host "Example: SPIN (Flatiron)" -ForegroundColor Cyan
$body = @{
    website = "spin_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# SPIN (Midtown East)
Write-Host "Example: SPIN (Midtown East)" -ForegroundColor Cyan
$body = @{
    website = "spin_nyc_midtown"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - FiDi
Write-Host "Example: Five Iron Golf (Financial District)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_fidi"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Flatiron
Write-Host "Example: Five Iron Golf (Flatiron)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_flatiron"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Grand Central
Write-Host "Example: Five Iron Golf (Midtown East)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_grand_central"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Herald Square
Write-Host "Example: Five Iron Golf (Herald Square)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_herald_square"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Long Island City
Write-Host "Example: Five Iron Golf (Long Island City)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_long_island_city"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Upper East Side
Write-Host "Example: Five Iron Golf (Upper East Side)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_upper_east_side"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Five Iron Golf - Rockefeller Center
Write-Host "Example: Five Iron Golf (Rockefeller Center)" -ForegroundColor Cyan
$body = @{
    website = "five_iron_golf_nyc_rockefeller_center"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Lucky Strike - Chelsea Piers
Write-Host "Example: Lucky Strike (Chelsea Piers)" -ForegroundColor Cyan
$body = @{
    website = "lucky_strike_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Lucky Strike - Times Square
Write-Host "Example: Lucky Strike (Times Square)" -ForegroundColor Cyan
$body = @{
    website = "lucky_strike_nyc_times_square"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Easybowl NYC
Write-Host "Example: Easybowl NYC" -ForegroundColor Cyan
$body = @{
    website = "easybowl_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# T-Squared Social
Write-Host "Example: T-Squared Social (Midtown East)" -ForegroundColor Cyan
$body = @{
    website = "tsquaredsocial_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Chelsea Piers (Chelsea) (DaySmart) - Only supports 2 guests
Write-Host "Example: Chelsea Piers (Chelsea) (DaySmart) - Only supports 2 guests" -ForegroundColor Cyan
$body = @{
    website = "daysmart_chelsea"
    guests = 2
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Puttery NYC
Write-Host "Example: Puttery (Meatpacking)" -ForegroundColor Cyan
$body = @{
    website = "puttery_nyc"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Kick Axe Brooklyn
Write-Host "Example: Kick Axe (Brooklyn)" -ForegroundColor Cyan
$body = @{
    website = "kick_axe_brooklyn"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# ============================================
# LONDON VENUES
# ============================================

# Swingers London
Write-Host "Example: Swingers London" -ForegroundColor Green
$body = @{
    website = "swingers_london"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Electric Shuffle London
Write-Host "Example: Electric Shuffle London" -ForegroundColor Green
$body = @{
    website = "electric_shuffle_london"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Fair Game - Canary Wharf
Write-Host "Example: Fair Game (Canary Wharf)" -ForegroundColor Green
$body = @{
    website = "fair_game_canary_wharf"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Fair Game - City
Write-Host "Example: Fair Game (City)" -ForegroundColor Green
$body = @{
    website = "fair_game_city"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Clays Bar (with location option)
Write-Host "Example: Clays Bar (Canary Wharf)" -ForegroundColor Green
$body = @{
    website = "clays_bar"
    guests = $defaultGuests
    target_date = $defaultDate
    clays_location = "Canary Wharf"  # Options: "Canary Wharf", "The City", "Birmingham", "Soho"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Clays Bar - The City
Write-Host "Example: Clays Bar (The City)" -ForegroundColor Green
$body = @{
    website = "clays_bar"
    guests = $defaultGuests
    target_date = $defaultDate
    clays_location = "The City"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Clays Bar - Birmingham
Write-Host "Example: Clays Bar (Birmingham)" -ForegroundColor Green
$body = @{
    website = "clays_bar"
    guests = $defaultGuests
    target_date = $defaultDate
    clays_location = "Birmingham"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Clays Bar - Soho
Write-Host "Example: Clays Bar (Soho)" -ForegroundColor Green
$body = @{
    website = "clays_bar"
    guests = $defaultGuests
    target_date = $defaultDate
    clays_location = "Soho"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Puttshack (with location option)
Write-Host "Example: Puttshack (Bank)" -ForegroundColor Green
$body = @{
    website = "puttshack"
    guests = $defaultGuests
    target_date = $defaultDate
    puttshack_location = "Bank"  # Options: "Bank", "Lakeside", "White City", "Watford"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Puttshack - Lakeside
Write-Host "Example: Puttshack (Lakeside)" -ForegroundColor Green
$body = @{
    website = "puttshack"
    guests = $defaultGuests
    target_date = $defaultDate
    puttshack_location = "Lakeside"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Puttshack - White City
Write-Host "Example: Puttshack (White City)" -ForegroundColor Green
$body = @{
    website = "puttshack"
    guests = $defaultGuests
    target_date = $defaultDate
    puttshack_location = "White City"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Puttshack - Watford
Write-Host "Example: Puttshack (Watford)" -ForegroundColor Green
$body = @{
    website = "puttshack"
    guests = $defaultGuests
    target_date = $defaultDate
    puttshack_location = "Watford"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Flight Club Darts (scrapes all 4 locations: Angel, Bloomsbury, Shoreditch, Victoria)
Write-Host "Example: Flight Club Darts (all 4 locations)" -ForegroundColor Green
$body = @{
    website = "flight_club_darts"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# F1 Arcade (St Paul's) (with experience option)
Write-Host "Example: F1 Arcade (St Paul's) (Team Racing)" -ForegroundColor Green
$body = @{
    website = "f1_arcade"
    guests = $defaultGuests
    target_date = $defaultDate
    f1_experience = "Team Racing"  # Options: "Team Racing", "Grand Prix"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# F1 Arcade (St Paul's) - Grand Prix
Write-Host "Example: F1 Arcade (St Paul's) (Grand Prix)" -ForegroundColor Green
$body = @{
    website = "f1_arcade"
    guests = $defaultGuests
    target_date = $defaultDate
    f1_experience = "Grand Prix"
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Topgolf (Chigwell)
Write-Host "Example: Topgolf (Chigwell)" -ForegroundColor Green
$body = @{
    website = "topgolf_chigwell"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Hijingo
Write-Host "Example: Hijingo (Shoreditch)" -ForegroundColor Green
$body = @{
    website = "hijingo"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Bounce (pingpong)
Write-Host "Example: Bounce (pingpong)" -ForegroundColor Green
$body = @{
    website = "pingpong"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# All Star Lanes - Stratford
Write-Host "Example: All Star Lanes (Stratford)" -ForegroundColor Green
$body = @{
    website = "allstarlanes_stratford"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# All Star Lanes - Holborn
Write-Host "Example: All Star Lanes (Holborn)" -ForegroundColor Green
$body = @{
    website = "allstarlanes_holborn"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# All Star Lanes - White City
Write-Host "Example: All Star Lanes (White City)" -ForegroundColor Green
$body = @{
    website = "allstarlanes_white_city"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# All Star Lanes - Brick Lane
Write-Host "Example: All Star Lanes (Brick Lane)" -ForegroundColor Green
$body = @{
    website = "allstarlanes_brick_lane"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# ============================================
# BULK OPERATIONS
# ============================================

# Scrape all NYC venues
Write-Host "Example: All NYC Venues" -ForegroundColor Yellow
$body = @{
    website = "all_new_york"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# Scrape all London venues
Write-Host "Example: All London Venues" -ForegroundColor Yellow
$body = @{
    website = "all_london"
    guests = $defaultGuests
    target_date = $defaultDate
} | ConvertTo-Json
# Invoke-RestMethod -Uri $baseUrl -Method POST -Body $body -ContentType "application/json"

# ============================================
# NOTES
# ============================================
# 
# 1. All venues require:
#    - website: The venue identifier (see examples above)
#    - guests: Number of guests (2-8, except daysmart_chelsea which only supports 2)
#    - target_date: Date in YYYY-MM-DD format
#
# 2. Optional parameters for specific venues:
#    - clays_location: For Clays Bar ("Canary Wharf", "The City", "Birmingham", "Soho")
#    - puttshack_location: For Puttshack ("Bank", "Lakeside", "White City", "Watford")
#    - f1_experience: For F1 Arcade (St Paul's) ("Team Racing", "Grand Prix")
#    - lawn_club_option: For Lawn Club (auto-detected from website name)
#    - lawn_club_time: Optional time filter for Lawn Club
#    - lawn_club_duration: Optional duration for Lawn Club
#    - spin_time: Optional time filter for SPIN
#
# 3. To actually run a task, uncomment the Invoke-RestMethod line for that example
#
# 4. Check task status using: GET http://localhost:8010/task_status/<task_id>
#
# 5. The response will include a task_id that you can use to track the task progress
