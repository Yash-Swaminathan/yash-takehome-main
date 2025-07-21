import json
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
    construction_year = db.Column(db.Integer)
    last_updated = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Building {self.address} ({self.building_type})>'
    
    @property
    def footprint(self):
        """Parse footprint coordinates JSON string to Python object"""
        if self.footprint_coords:
            try:
                return json.loads(self.footprint_coords)
            except json.JSONDecodeError:
                return []
        return []
    
    @footprint.setter
    def footprint(self, value):
        """Set footprint by converting coordinate list to JSON string"""
        if value is None:
            self.footprint_coords = None
        else:
            self.footprint_coords = json.dumps(value)
    
    def to_dict(self):
        """Convert building object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'building_id': self.building_id,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'footprint': self.footprint,
            'height': self.height,
            'floors': self.floors,
            'building_type': self.building_type,
            'zoning': self.zoning,
            'assessed_value': self.assessed_value,
            'land_use': self.land_use,
            'construction_year': self.construction_year,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def matches_filter(self, filter_criteria):
        """Check if building matches the given filter criteria"""
        attribute = filter_criteria.get('attribute')
        operator = filter_criteria.get('operator')
        value = filter_criteria.get('value')
        
        if not all([attribute, operator, value]):
            return False
        
        building_value = getattr(self, attribute, None)
        if building_value is None:
            return False
        
        try:
            # Handle different operators
            if operator == '>':
                return float(building_value) > float(value)
            elif operator == '<':
                return float(building_value) < float(value)
            elif operator == '=':
                return str(building_value).lower() == str(value).lower()
            elif operator == 'contains':
                return str(value).lower() in str(building_value).lower()
            elif operator == '>=':
                return float(building_value) >= float(value)
            elif operator == '<=':
                return float(building_value) <= float(value)
        except (ValueError, TypeError):
            # Fallback to string comparison for non-numeric values
            if operator == '=':
                return str(building_value).lower() == str(value).lower()
            elif operator == 'contains':
                return str(value).lower() in str(building_value).lower()
        
        return False 