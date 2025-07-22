import json
from datetime import datetime
from app import db

class Building(db.Model):
    """Building model for Calgary city building data"""
    __tablename__ = 'buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic building information
    address = db.Column(db.String(200))
    building_id = db.Column(db.String(50), unique=True, index=True)  # External ID from Calgary data
    
    # Spatial data
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    footprint_coords = db.Column(db.Text)  # JSON string of polygon coordinates
    
    # Building characteristics
    height = db.Column(db.Float)  # Height in feet/meters
    floors = db.Column(db.Integer)
    building_type = db.Column(db.String(100))  # Residential, Commercial, Industrial, etc.
    
    # Zoning and assessment data
    zoning = db.Column(db.String(50))  # Zoning classification (e.g., RC-G)
    assessed_value = db.Column(db.Float)  # Property assessment value
    land_use = db.Column(db.String(100))
    
    # Additional metadata
    last_updated = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Building {self.building_id}: {self.address}>'
    
    @property
    def footprint(self):
        """Return footprint coordinates as Python object"""
        if self.footprint_coords:
            try:
                return json.loads(self.footprint_coords)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @footprint.setter
    def footprint(self, value):
        """Set footprint coordinates from Python object"""
        if value:
            try:
                self.footprint_coords = json.dumps(value)
            except (TypeError, ValueError):
                self.footprint_coords = None
        else:
            self.footprint_coords = None
    
    def to_dict(self):
        """Convert building to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'building_id': self.building_id,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'height': self.height,
            'floors': self.floors,
            'building_type': self.building_type,
            'zoning': self.zoning,
            'assessed_value': self.assessed_value,
            'land_use': self.land_use,
            'footprint': self.footprint,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def matches_filter(self, filter_criteria):
        """Check if building matches the given filter criteria"""
        try:
            # Height filter
            if filter_criteria.get('min_height') and (not self.height or self.height < filter_criteria['min_height']):
                return False
            if filter_criteria.get('max_height') and (not self.height or self.height > filter_criteria['max_height']):
                return False
            
            # Floors filter
            if filter_criteria.get('min_floors') and (not self.floors or self.floors < filter_criteria['min_floors']):
                return False
            if filter_criteria.get('max_floors') and (not self.floors or self.floors > filter_criteria['max_floors']):
                return False
            
            # Building type filter
            if filter_criteria.get('building_types') and self.building_type not in filter_criteria['building_types']:
                return False
            
            # Zoning filter
            if filter_criteria.get('zoning_types') and self.zoning not in filter_criteria['zoning_types']:
                return False
            
            # Assessment value filter
            if filter_criteria.get('min_value') and (not self.assessed_value or self.assessed_value < filter_criteria['min_value']):
                return False
            if filter_criteria.get('max_value') and (not self.assessed_value or self.assessed_value > filter_criteria['max_value']):
                return False
            
            return True
            
        except Exception as e:
            return False 