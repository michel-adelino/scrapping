"""
Simple test script for Hijingo scraper (no database required)
"""
from datetime import datetime, timedelta
from scrapers.hijingo import HijingoBookingBot

# Set test parameters
test_guests = 4
# Test date 7 days from now, format: YYYY-MM-DD
test_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

# Run the scraper
print("=" * 60)
print("Testing Hijingo Booking Bot")
print("=" * 60)
print(f"Guests: {test_guests}")
print(f"Date: {test_date}")
print("-" * 60)
print("\nRunning scraper...\n")

bot = None
try:
    # Initialize bot (set headless=False to see the browser in action)
    bot = HijingoBookingBot(headless=True)
    
    # Run the booking/scraping process
    bot.start_booking(test_guests, test_date)
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    
finally:
    # Clean up - close the browser
    if bot:
        print("\nCleaning up...")
        bot.close()

