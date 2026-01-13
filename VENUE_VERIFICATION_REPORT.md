# Venue Verification Report

## Summary
✅ **All 36 venues are correctly configured to run in the Celery worker**

## Verification Results

### NYC Venues (21 venues)
All venues have proper handlers in `scrape_venue_task`:

1. ✅ `swingers_nyc` → `scrape_swingers_task()`
2. ✅ `electric_shuffle_nyc` → `scrape_electric_shuffle_task()`
3. ✅ `lawn_club_nyc_indoor_gaming` → `scrape_lawn_club_task()` (pattern: `lawn_club_nyc_*`)
4. ✅ `lawn_club_nyc_curling_lawns` → `scrape_lawn_club_task()` (pattern: `lawn_club_nyc_*`)
5. ✅ `lawn_club_nyc_croquet_lawns` → `scrape_lawn_club_task()` (pattern: `lawn_club_nyc_*`)
6. ✅ `spin_nyc` → `scrape_spin_task()` (location='flatiron')
7. ✅ `spin_nyc_midtown` → `scrape_spin_task()` (pattern: `spin_nyc_*`)
8. ✅ `five_iron_golf_nyc_fidi` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
9. ✅ `five_iron_golf_nyc_flatiron` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
10. ✅ `five_iron_golf_nyc_grand_central` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
11. ✅ `five_iron_golf_nyc_herald_square` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
12. ✅ `five_iron_golf_nyc_long_island_city` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
13. ✅ `five_iron_golf_nyc_upper_east_side` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
14. ✅ `five_iron_golf_nyc_rockefeller_center` → `scrape_five_iron_golf_task()` (pattern: `five_iron_golf_nyc_*`)
15. ✅ `lucky_strike_nyc` → `scrape_lucky_strike_task()` (pattern: `lucky_strike_nyc*`)
16. ✅ `lucky_strike_nyc_times_square` → `scrape_lucky_strike_task()` (pattern: `lucky_strike_nyc*`)
17. ✅ `easybowl_nyc` → `scrape_easybowl_task()`
18. ✅ `tsquaredsocial_nyc` → `scrape_tsquaredsocial_task()`
19. ✅ `daysmart_chelsea` → `scrape_daysmart_chelsea_task()` (only supports 2 guests)
20. ✅ `puttery_nyc` → `scrape_puttery_task()`
21. ✅ `kick_axe_brooklyn` → `scrape_kick_axe_task()`

### London Venues (15 venues)
All venues have proper handlers in `scrape_venue_task`:

1. ✅ `swingers_london` → `scrape_swingers_uk_task()`
2. ✅ `electric_shuffle_london` → `scrape_electric_shuffle_london_task()`
3. ✅ `fair_game_canary_wharf` → `scrape_fair_game_canary_wharf_task()`
4. ✅ `fair_game_city` → `scrape_fair_game_city_task()`
5. ✅ `clays_bar` → `scrape_clays_bar_task()` (with `clays_location` parameter)
6. ✅ `puttshack` → `scrape_puttshack_task()` (with `puttshack_location` parameter)
7. ✅ `flight_club_darts` → `scrape_flight_club_darts_task()` (scrapes all 4 locations)
8. ✅ `f1_arcade` → `scrape_f1_arcade_task()` (with `f1_experience` parameter)
9. ✅ `topgolf_chigwell` → `scrape_topgolf_chigwell_task()`
10. ✅ `hijingo` → `scrape_hijingo_task()`
11. ✅ `pingpong` → `scrape_pingpong_task()` (Bounce venue)
12. ✅ `allstarlanes_stratford` → `scrape_allstarlanes_task()` (pattern: `allstarlanes_*`)
13. ✅ `allstarlanes_holborn` → `scrape_allstarlanes_task()` (pattern: `allstarlanes_*`)
14. ✅ `allstarlanes_white_city` → `scrape_allstarlanes_task()` (pattern: `allstarlanes_*`)
15. ✅ `allstarlanes_brick_lane` → `scrape_allstarlanes_task()` (pattern: `allstarlanes_*`)

## Celery Task Functions Verified

All required Celery task functions exist and are properly decorated:

- ✅ `scrape_swingers_task`
- ✅ `scrape_swingers_uk_task`
- ✅ `scrape_electric_shuffle_task`
- ✅ `scrape_electric_shuffle_london_task`
- ✅ `scrape_lawn_club_task`
- ✅ `scrape_spin_task`
- ✅ `scrape_five_iron_golf_task`
- ✅ `scrape_allstarlanes_task`
- ✅ `scrape_lucky_strike_task`
- ✅ `scrape_easybowl_task`
- ✅ `scrape_tsquaredsocial_task`
- ✅ `scrape_hijingo_task`
- ✅ `scrape_pingpong_task`
- ✅ `scrape_daysmart_chelsea_task`
- ✅ `scrape_fair_game_canary_wharf_task`
- ✅ `scrape_fair_game_city_task`
- ✅ `scrape_clays_bar_task`
- ✅ `scrape_puttshack_task`
- ✅ `scrape_flight_club_darts_task`
- ✅ `scrape_f1_arcade_task`
- ✅ `scrape_topgolf_chigwell_task`
- ✅ `scrape_puttery_task`
- ✅ `scrape_kick_axe_task`
- ✅ `scrape_venue_task` (main wrapper)
- ✅ `scrape_all_venues_task` (bulk operation)
- ✅ `refresh_all_venues_task` (refresh cycle)

## Scraper Modules Verified

All scraper modules are properly imported in `app.py`:

```python
from scrapers import swingers, electric_shuffle, lawn_club, spin, five_iron_golf, lucky_strike, easybowl
from scrapers import fair_game, clays_bar, puttshack, flight_club_darts, f1_arcade, topgolfchigwell, tsquaredsocial, daysmart, hijingo, pingpong, puttery, kick_axe, allstarlanes_bowling
```

## Handler Patterns

The `scrape_venue_task` function uses the following patterns to route venues:

1. **Exact matches**: Direct `if website == 'venue_name'` checks
2. **Pattern matches**: `website.startswith('pattern_')` for venues with multiple locations:
   - `lawn_club_nyc_*` → handles all 3 Lawn Club options
   - `spin_nyc_*` → handles SPIN midtown (spin_nyc is exact match)
   - `five_iron_golf_nyc_*` → handles all 7 Five Iron Golf locations
   - `lucky_strike_nyc*` → handles both Lucky Strike locations
   - `allstarlanes_*` → handles all 4 All Star Lanes locations

## Error Handling

All venues that require a `target_date` have proper validation:
- If `target_date` is missing, a `ValueError` is raised with a descriptive message
- Unknown venues trigger: `ValueError(f"Unknown website: {website}")`
- All errors are logged and task status is updated to 'FAILURE'

## Conclusion

✅ **All 36 venues are correctly configured and will run properly in the Celery worker.**

No missing handlers or configuration issues found.
