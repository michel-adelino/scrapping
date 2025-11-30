#!/bin/bash
# Debug script to test the database query

cd /opt/scrapping
source venv/bin/activate

python3 << 'PYTHON_SCRIPT'
import sys
from app import app, db, AvailabilitySlot

with app.app_context():
    print("=" * 60)
    print("Testing Database Queries")
    print("=" * 60)
    
    # Test 1: Count all
    total = AvailabilitySlot.query.count()
    print(f"\n1. Total slots in database: {total}")
    
    # Test 2: Count NYC
    nyc_total = AvailabilitySlot.query.filter(AvailabilitySlot.city == 'NYC').count()
    print(f"2. Total NYC slots: {nyc_total}")
    
    # Test 3: Count NYC with guests=6
    nyc_guests_6 = AvailabilitySlot.query.filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    ).count()
    print(f"3. NYC slots with guests=6: {nyc_guests_6}")
    
    # Test 4: Get actual query result
    query = AvailabilitySlot.query.filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    )
    slots = query.limit(3).all()
    print(f"\n4. Sample slots (first 3):")
    for slot in slots:
        print(f"   - ID: {slot.id}, Venue: {slot.venue_name}, City: {slot.city}, Date: {slot.date}, Guests: {slot.guests}")
    
    # Test 5: Check dates
    dates = db.session.query(AvailabilitySlot.date).filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    ).distinct().order_by(AvailabilitySlot.date).limit(5).all()
    print(f"\n5. Sample dates: {[str(d[0]) for d in dates]}")
    
    # Test 6: Try to_dict()
    if slots:
        try:
            slot_dict = slots[0].to_dict()
            print(f"\n6. First slot as dict: {slot_dict}")
        except Exception as e:
            print(f"\n6. Error converting to dict: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)

PYTHON_SCRIPT

