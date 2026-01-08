"""
Simple test script for PingPong scraper (no database required)
"""
from datetime import datetime, timedelta
from scrapers.pingpong import fetch_available_dates, fetch_available_times

# Set test parameters
test_guests = 4
# Test date 7 days from now, format: YYYY-MM-DD
test_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

# Run the scraper
print("=" * 60)
print("Testing PingPong Scraper")
print("=" * 60)
print(f"Guests: {test_guests}")
print(f"Date: {test_date}")
print("-" * 60)
print("\nRunning scraper...\n")

try:
    # Fetch available dates
    print("Fetching available dates...")
    dates = fetch_available_dates(test_guests, test_date)
    
    if not dates:
        print("[WARNING] No valid dates returned (this might be normal if no availability)")
    else:
        print(f"[SUCCESS] Found {len(dates)} available date(s)\n")
        
        # Test fetching times for each date (limit to first 3 dates to avoid too much output)
        for i, date in enumerate(dates[:3], 1):
            print(f"\nDate {i}: {date}")
            print("-" * 40)
            
            # Check times in 2-hour windows starting from 12:00
            start_time = 12
            all_times = []
            
            for window in range(4):  # Check 4 time windows (12-14, 15-17, 18-20, 21-23)
                try:
                    times = fetch_available_times(date, test_guests, start_time)
                    if times:
                        all_times.extend(times)
                        print(f"  Window {start_time}:00-{start_time+2}:59: {len(times)} slot(s)")
                except Exception as e:
                    print(f"  Window {start_time}:00-{start_time+2}:59: Error - {str(e)}")
                
                start_time += 3
            
            if all_times:
                print(f"\n  Available times for {date}:")
                for time in sorted(all_times):
                    # Calculate end time (55 minutes duration)
                    time_obj = datetime.strptime(time, "%H:%M")
                    end_time = (time_obj + timedelta(minutes=55)).strftime("%H:%M")
                    print(f"    {time} ~ {end_time}")
            else:
                print(f"  No available times found for {date}")
        
        if len(dates) > 3:
            print(f"\n... and {len(dates) - 3} more date(s) (not shown)")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

