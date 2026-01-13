"""
Script to verify all venues are correctly configured in the Celery worker
"""

# Venue lists from app.py
NYC_VENUES = [
    'swingers_nyc',
    'electric_shuffle_nyc',
    'lawn_club_nyc_indoor_gaming',
    'lawn_club_nyc_curling_lawns',
    'lawn_club_nyc_croquet_lawns',
    'spin_nyc',
    'spin_nyc_midtown',
    'five_iron_golf_nyc_fidi',
    'five_iron_golf_nyc_flatiron',
    'five_iron_golf_nyc_grand_central',
    'five_iron_golf_nyc_herald_square',
    'five_iron_golf_nyc_long_island_city',
    'five_iron_golf_nyc_upper_east_side',
    'five_iron_golf_nyc_rockefeller_center',
    'lucky_strike_nyc',
    'lucky_strike_nyc_times_square',
    'easybowl_nyc',
    'tsquaredsocial_nyc',
    'daysmart_chelsea',
    'puttery_nyc',
    'kick_axe_brooklyn'
]

LONDON_VENUES = [
    'swingers_london',
    'electric_shuffle_london',
    'fair_game_canary_wharf',
    'fair_game_city',
    'clays_bar',
    'puttshack',
    'flight_club_darts',
    'f1_arcade',
    'topgolf_chigwell',
    'hijingo',
    'pingpong',
    'allstarlanes_stratford',
    'allstarlanes_holborn',
    'allstarlanes_white_city',
    'allstarlanes_brick_lane'
]

ALL_VENUES = NYC_VENUES + LONDON_VENUES

# Handlers from scrape_venue_task (based on code analysis)
# Exact matches
EXACT_HANDLERS = {
    'swingers_nyc',
    'swingers_london',
    'electric_shuffle_nyc',
    'electric_shuffle_london',
    'spin_nyc',
    'easybowl_nyc',
    'tsquaredsocial_nyc',
    'daysmart_chelsea',
    'fair_game_canary_wharf',
    'fair_game_city',
    'clays_bar',
    'puttshack',
    'flight_club_darts',
    'f1_arcade',
    'topgolf_chigwell',
    'hijingo',
    'pingpong',
    'puttery_nyc',
    'kick_axe_brooklyn'
}

# Pattern-based handlers (using startswith)
PATTERN_HANDLERS = {
    'lawn_club_nyc_': ['lawn_club_nyc_indoor_gaming', 'lawn_club_nyc_curling_lawns', 'lawn_club_nyc_croquet_lawns'],
    'spin_nyc_': ['spin_nyc_midtown'],  # Note: spin_nyc is exact match, spin_nyc_* is pattern
    'five_iron_golf_nyc_': [
        'five_iron_golf_nyc_fidi',
        'five_iron_golf_nyc_flatiron',
        'five_iron_golf_nyc_grand_central',
        'five_iron_golf_nyc_herald_square',
        'five_iron_golf_nyc_long_island_city',
        'five_iron_golf_nyc_upper_east_side',
        'five_iron_golf_nyc_rockefeller_center'
    ],
    'lucky_strike_nyc': ['lucky_strike_nyc', 'lucky_strike_nyc_times_square'],  # Uses startswith
    'allstarlanes_': [
        'allstarlanes_stratford',
        'allstarlanes_holborn',
        'allstarlanes_white_city',
        'allstarlanes_brick_lane'
    ]
}

def check_venue_handler(venue):
    """Check if a venue has a handler"""
    # Check exact match
    if venue in EXACT_HANDLERS:
        return True, "exact"
    
    # Check pattern matches
    for pattern, venues in PATTERN_HANDLERS.items():
        if venue.startswith(pattern):
            if venue in venues:
                return True, f"pattern ({pattern})"
            else:
                # Pattern matches but venue not in expected list
                return True, f"pattern ({pattern}) - WARNING: venue not in expected list"
    
    return False, "no handler found"

def main():
    print("=" * 80)
    print("VENUE HANDLER VERIFICATION")
    print("=" * 80)
    print()
    
    missing_handlers = []
    all_good = []
    warnings = []
    
    print("NYC VENUES:")
    print("-" * 80)
    for venue in NYC_VENUES:
        has_handler, handler_type = check_venue_handler(venue)
        if has_handler:
            if "WARNING" in handler_type:
                warnings.append((venue, handler_type))
                print(f"  [W] {venue:45} - {handler_type}")
            else:
                all_good.append((venue, handler_type))
                print(f"  [OK] {venue:45} - {handler_type}")
        else:
            missing_handlers.append(venue)
            print(f"  [X] {venue:45} - {handler_type}")
    
    print()
    print("LONDON VENUES:")
    print("-" * 80)
    for venue in LONDON_VENUES:
        has_handler, handler_type = check_venue_handler(venue)
        if has_handler:
            if "WARNING" in handler_type:
                warnings.append((venue, handler_type))
                print(f"  [W] {venue:45} - {handler_type}")
            else:
                all_good.append((venue, handler_type))
                print(f"  [OK] {venue:45} - {handler_type}")
        else:
            missing_handlers.append(venue)
            print(f"  [X] {venue:45} - {handler_type}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total venues: {len(ALL_VENUES)}")
    print(f"  [OK] Correctly handled: {len(all_good)}")
    print(f"  [W]  Warnings: {len(warnings)}")
    print(f"  [X]  Missing handlers: {len(missing_handlers)}")
    print()
    
    if missing_handlers:
        print("[ERROR] MISSING HANDLERS:")
        for venue in missing_handlers:
            print(f"   - {venue}")
        print()
        return False
    
    if warnings:
        print("[WARNING] WARNINGS:")
        for venue, warning in warnings:
            print(f"   - {venue}: {warning}")
        print()
    
    if not missing_handlers:
        print("[SUCCESS] All venues have handlers configured!")
        return True
    
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
