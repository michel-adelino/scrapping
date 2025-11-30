#!/usr/bin/env python3
"""Test script to debug the API query issue"""

import sys
import os
sys.path.insert(0, '/opt/scrapping')

from app import app, db, AvailabilitySlot
from datetime import datetime

with app.app_context():
    # Test 1: Count all NYC slots
    total_nyc = AvailabilitySlot.query.filter(AvailabilitySlot.city == 'NYC').count()
    print(f"Total NYC slots: {total_nyc}")
    
    # Test 2: Count NYC with guests=6
    nyc_guests_6 = AvailabilitySlot.query.filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    ).count()
    print(f"NYC slots with guests=6: {nyc_guests_6}")
    
    # Test 3: Get sample dates
    sample_dates = db.session.query(AvailabilitySlot.date).filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    ).distinct().order_by(AvailabilitySlot.date).limit(10).all()
    print(f"Sample dates for NYC, guests=6: {[str(d[0]) for d in sample_dates]}")
    
    # Test 4: Check what the actual query returns
    query = AvailabilitySlot.query.filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6
    )
    slots = query.limit(5).all()
    print(f"\nSample slots (first 5):")
    for slot in slots:
        print(f"  - {slot.venue_name}, {slot.date}, {slot.time}, {slot.status}, guests={slot.guests}, city={slot.city}")
    
    # Test 5: Check if there are any date filters being applied
    today = datetime.now().date()
    print(f"\nToday's date: {today}")
    future_slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.city == 'NYC',
        AvailabilitySlot.guests == 6,
        AvailabilitySlot.date >= today
    ).count()
    print(f"NYC slots with guests=6 from today onwards: {future_slots}")

