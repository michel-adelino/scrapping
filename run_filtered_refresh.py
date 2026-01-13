"""
Script to run a filtered refresh cycle for specific venues
Usage: python run_filtered_refresh.py puttery_nyc kick_axe_brooklyn
"""

import sys
from app import refresh_all_venues_task

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_filtered_refresh.py <venue1> [venue2] [venue3] ...")
        print("\nExample:")
        print("  python run_filtered_refresh.py puttery_nyc kick_axe_brooklyn")
        print("\nAvailable venues:")
        from app import NYC_VENUES, LONDON_VENUES
        print("\nNYC Venues:")
        for venue in NYC_VENUES:
            print(f"  - {venue}")
        print("\nLondon Venues:")
        for venue in LONDON_VENUES:
            print(f"  - {venue}")
        sys.exit(1)
    
    venues = sys.argv[1:]
    
    print(f"Starting filtered refresh cycle for {len(venues)} venues:")
    for venue in venues:
        print(f"  - {venue}")
    
    try:
        result = refresh_all_venues_task.delay(venues_filter=venues)
        print(f"\n✓ Task submitted successfully!")
        print(f"  Task ID: {result.id}")
        print(f"  Status: {result.status}")
        print(f"\nMonitor progress in Celery worker logs")
    except Exception as e:
        print(f"\n✗ Error submitting task: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
