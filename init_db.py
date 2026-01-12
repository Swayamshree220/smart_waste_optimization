"""
Quick Database Initialization for Bhubaneswar Smart Waste System
Run this once to create fresh database with 'area' column
"""

from app import app
from models.database import db, Bin

print("\n" + "="*70)
print("🔧 FIXING DATABASE - Adding 'area' column")
print("="*70 + "\n")

with app.app_context():
    print("📋 Step 1: Dropping old tables...")
    db.drop_all()
    print("✅ Old tables dropped")
    
    print("\n📋 Step 2: Creating new tables with 'area' column...")
    db.create_all()
    print("✅ New tables created")
    
    print("\n📍 Step 3: Adding Bhubaneswar ward bins...")
    
    # Bhubaneswar areas
    areas = [
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
    
    # Create bins with area field
    for i, area in enumerate(areas):
        bin_obj = Bin(
            bin_id=f"BIN_{i+1:03d}",
            latitude=area['lat'],
            longitude=area['lon'],
            area=area['name'],  # ✅ This now works!
            location=f"{area['name']}, Bhubaneswar, Odisha",
            capacity=100.0,
            current_fill_level=0.0,
            bin_type=area['type'],
            is_active=True,
            battery_level=100.0
        )
        db.session.add(bin_obj)
        print(f"   ✅ Created: {area['name']}")
    
    db.session.commit()
    
    print("\n" + "="*70)
    print("🎉 DATABASE FIXED!")
    print("="*70)
    print(f"\n✅ Created {len(areas)} bins with Bhubaneswar ward names")
    print("✅ All bins have 'area' column now")
    print("✅ IoT endpoints will work without errors")
    print("\n🚀 Now run: python app.py")
    print("="*70 + "\n")