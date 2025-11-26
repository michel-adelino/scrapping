from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index, UniqueConstraint
import json

db = SQLAlchemy()


class AvailabilitySlot(db.Model):
    """Model for storing availability slot data"""
    __tablename__ = 'availability_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_name = db.Column(db.String(200), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(200))
    status = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(50), nullable=False, index=True)
    venue_specific_data = db.Column(db.Text)  # JSON string for options like lawn_club_option, clays_location, etc.
    booking_url = db.Column(db.String(500))
    
    # Composite unique constraint to prevent duplicates
    __table_args__ = (
        UniqueConstraint('venue_name', 'date', 'time', 'guests', name='uq_venue_date_time_guests'),
        Index('idx_venue_city_date', 'venue_name', 'city', 'date'),
    )
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        venue_specific = None
        if self.venue_specific_data:
            try:
                venue_specific = json.loads(self.venue_specific_data)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, return as string or None
                venue_specific = None
        
        return {
            'id': self.id,
            'venue_name': self.venue_name,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time,
            'price': self.price,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'guests': self.guests,
            'city': self.city,
            'booking_url': self.booking_url,
            'venue_specific_data': venue_specific,
            'website': self.venue_name  # Add website field for compatibility
        }
    
    def set_venue_specific_data(self, data):
        """Set venue-specific data as JSON string"""
        if data:
            self.venue_specific_data = json.dumps(data)
        else:
            self.venue_specific_data = None
    
    def get_venue_specific_data(self):
        """Get venue-specific data as dictionary"""
        if self.venue_specific_data:
            return json.loads(self.venue_specific_data)
        return None


class ScrapingTask(db.Model):
    """Model for tracking scraping tasks"""
    __tablename__ = 'scraping_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    website = db.Column(db.String(100), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    target_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='PENDING', nullable=False)  # PENDING, STARTED, SUCCESS, FAILURE
    progress = db.Column(db.Text)
    total_slots_found = db.Column(db.Integer, default=0)
    current_venue = db.Column(db.String(200))
    error = db.Column(db.Text)
    duration_seconds = db.Column(db.Float)  # Duration in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'website': self.website,
            'guests': self.guests,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'status': self.status,
            'progress': self.progress,
            'total_slots_found': self.total_slots_found,
            'current_venue': self.current_venue,
            'error': self.error,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

