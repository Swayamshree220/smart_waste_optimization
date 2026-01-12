from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Bin(db.Model):
    """Smart Waste Bin Model with IoT capabilities"""
    __tablename__ = 'bins'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.String(50), unique=True, nullable=False)
    
    # Location information
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    area = db.Column(db.String(200), nullable=True)  # ✅ FIXED: Added area field
    location = db.Column(db.String(200), nullable=True)
    
    # Capacity and status
    capacity = db.Column(db.Float, default=100.0)
    current_fill_level = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    bin_type = db.Column(db.String(50), default='general')
    is_active = db.Column(db.Boolean, default=True)
    
    # IoT sensor data
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    battery_level = db.Column(db.Float, default=100.0)
    
    # Timestamps - ✅ FIXED: Proper datetime handling
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                           onupdate=lambda: datetime.now(timezone.utc))
    last_collection = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    readings = db.relationship('BinReading', backref='bin', lazy=True, 
                              cascade='all, delete-orphan')
    collections = db.relationship('Collection', backref='bin', lazy=True)
    
    def get_status(self):
        """Get bin status based on fill level"""
        if self.current_fill_level >= 90:
            return 'CRITICAL'
        elif self.current_fill_level >= 70:
            return 'ALERT'
        elif self.current_fill_level >= 50:
            return 'MODERATE'
        else:
            return 'OK'
    
    def needs_collection(self):
        """Check if bin needs collection"""
        return self.current_fill_level >= 70
    
    def to_dict(self):
        """Convert bin to dictionary"""
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'area': self.area,
            'location': self.location,
            'capacity': self.capacity,
            'current_fill_level': self.current_fill_level,
            'status': self.get_status(),
            'bin_type': self.bin_type,
            'is_active': self.is_active,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'battery_level': self.battery_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None,
            'needs_collection': self.needs_collection()
        }
    
    def __repr__(self):
        return f'<Bin {self.bin_id} - {self.get_status()}>'


class BinReading(db.Model):
    """IoT Sensor Readings from Smart Bins"""
    __tablename__ = 'bin_readings'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.String(50), db.ForeignKey('bins.bin_id'), nullable=False)
    
    # Sensor data
    fill_level = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    battery_level = db.Column(db.Float, nullable=True)
    
    # GPS data
    gps_lat = db.Column(db.Float, nullable=True)
    gps_lon = db.Column(db.Float, nullable=True)
    
    # Timestamp - ✅ FIXED: Proper datetime
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                         nullable=False)
    
    def to_dict(self):
        """Convert reading to dictionary"""
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'fill_level': self.fill_level,
            'weight_kg': self.weight_kg,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'battery_level': self.battery_level,
            'gps_lat': self.gps_lat,
            'gps_lon': self.gps_lon,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<BinReading {self.bin_id} - {self.fill_level}% at {self.timestamp}>'


class Collection(db.Model):
    """Waste Collection Records"""
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.String(50), db.ForeignKey('bins.bin_id'), nullable=False)
    
    # Collection details
    collection_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    waste_collected = db.Column(db.Float, nullable=True)  # in kg
    truck_id = db.Column(db.String(50), nullable=True)
    driver_id = db.Column(db.String(50), nullable=True)
    
    # Route information
    route_id = db.Column(db.String(50), nullable=True)
    route_order = db.Column(db.Integer, nullable=True)
    
    # Before and after fill levels
    fill_before = db.Column(db.Float, nullable=True)
    fill_after = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='completed')  # completed, pending, failed
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert collection to dictionary"""
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'collection_time': self.collection_time.isoformat() if self.collection_time else None,
            'waste_collected': self.waste_collected,
            'truck_id': self.truck_id,
            'driver_id': self.driver_id,
            'route_id': self.route_id,
            'route_order': self.route_order,
            'fill_before': self.fill_before,
            'fill_after': self.fill_after,
            'status': self.status,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<Collection {self.bin_id} at {self.collection_time}>'


class Alert(db.Model):
    """System Alerts and Notifications"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.String(50), db.ForeignKey('bins.bin_id'), nullable=True)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # CRITICAL_FILL, FIRE_RISK, LOW_BATTERY
    severity = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    message = db.Column(db.Text, nullable=False)
    
    # Status
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'bin_id': self.bin_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<Alert {self.alert_type} - {self.severity}>'


def init_db(app):
    """Initialize database with Bhubaneswar bins"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if bins already exist
        if Bin.query.count() == 0:
            print("🔄 Initializing Bhubaneswar bins...")
            
            # Bhubaneswar ward data
            bhubaneswar_areas = [
                {"name": "Unit-1 (Master Canteen)", "lat": 20.2961, "lon": 85.8245, "type": "commercial"},
                {"name": "Unit-2 (Rajmahal)", "lat": 20.2975, "lon": 85.8220, "type": "commercial"},
                {"name": "Unit-3 (AG Colony)", "lat": 20.2990, "lon": 85.8200, "type": "residential"},
                {"name": "Unit-4 (Bhubaneswar Club)", "lat": 20.2945, "lon": 85.8180, "type": "residential"},
                {"name": "Unit-5 (Market Building)", "lat": 20.2920, "lon": 85.8165, "type": "commercial"},
                {"name": "Saheed Nagar", "lat": 20.2970, "lon": 85.8400, "type": "residential"},
                {"name": "Satya Nagar", "lat": 20.2920, "lon": 85.8380, "type": "residential"},
                {"name": "Nayapalli", "lat": 20.2850, "lon": 85.7980, "type": "residential"},
                {"name": "Patia (KIIT)", "lat": 20.3550, "lon": 85.8180, "type": "commercial"},
                {"name": "Chandrasekharpur", "lat": 20.3160, "lon": 85.8220, "type": "residential"},
            ]
            
            # Create bins
            for i, area in enumerate(bhubaneswar_areas):
                bin_obj = Bin(
                    bin_id=f"BIN_{i+1:03d}",
                    latitude=area['lat'],
                    longitude=area['lon'],
                    area=area['name'],  # ✅ Now this works!
                    location=f"{area['name']}, Bhubaneswar, Odisha",
                    capacity=100.0,
                    current_fill_level=0.0,
                    bin_type=area['type'],
                    is_active=True,
                    battery_level=100.0
                )
                db.session.add(bin_obj)
            
            db.session.commit()
            print(f"✅ Created {len(bhubaneswar_areas)} bins for Bhubaneswar wards")
        else:
            print(f"✅ Database already initialized ({Bin.query.count()} bins found)")

    from models.vehicle_health import VehicleHealth
