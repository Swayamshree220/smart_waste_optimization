from models.database import db
from datetime import datetime

class VehicleHealth(db.Model):
    __tablename__ = "vehicle_health"

    id = db.Column(db.Integer, primary_key=True)
    truck_id = db.Column(db.String(50), nullable=False)
    mileage = db.Column(db.Integer)
    days_since_service = db.Column(db.Integer)
    engine_health = db.Column(db.Float)
    brake_health = db.Column(db.Float)
    tire_health = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
