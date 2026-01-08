"""
Simple test script for DaySmart Chelsea scraper (no database required)
"""
from datetime import datetime, timedelta
from scrapers.daysmart import scrape_daysmart_chelsea

# Set test parameters
target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

# Run the scraper
print("=" * 60)
print("Testing DaySmart Chelsea Scraper")
print("=" * 60)
print(f"Date: {target_date}")
print("-" * 60)
print("\nRunning scraper...\n")

try:
    results = scrape_daysmart_chelsea(target_date)
    
    print(f"[SUCCESS] Found {len(results)} slots\n")
    
    if results:
        print("Sample slots:")
        for i, slot in enumerate(results[:10], 1):  # Show first 10
            print(f"\n{i}. Time: {slot.get('time', 'N/A')}")
            print(f"   Title: {slot.get('title', 'N/A')}")
            print(f"   Price: {slot.get('price', 'N/A')}")
            print(f"   Duration: {slot.get('duration', 'N/A')}")
            print(f"   Status: {slot.get('status', 'N/A')}")
            print(f"   Guests: {slot.get('guests', 'N/A')}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more slots")
    else:
        print("[WARNING] No slots found (this might be normal if no availability)")
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

