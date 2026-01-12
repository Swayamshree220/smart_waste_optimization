from flask import Flask, render_template, request, jsonify
import numpy as np
from datetime import datetime
import logging

from models.waste_predictor import WastePredictor
from models.route_optimizer import RouteOptimizer
from algorithms.genetic_algorithm import GeneticAlgorithm
from algorithms.simulated_annealing import SimulatedAnnealing
from algorithms.nearest_neighbor import NearestNeighbor
from config import Config
from models.database import db, Bin, BinReading, Collection
from geopy.distance import geodesic
import requests

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# ✅ THEN CONFIGURE DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smart_waste.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ INIT DB
db.init_app(app)

# --------------------------------------------------
# Initialize ML Predictor
# --------------------------------------------------
predictor = WastePredictor()
print("Training waste prediction model...")
training_results = predictor.train()
print(f"Model trained - R² Score: {training_results['test_r2']:.4f}")

# --------------------------------------------------
# Bhubaneswar Areas (with TYPE ✅)
# --------------------------------------------------
BHUBANESWAR_AREAS = [
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

# --------------------------------------------------
# Generate bins (FIXED: includes 'type')
# --------------------------------------------------
def generate_bins():
    np.random.seed(42)
    bins = []

    for i, area in enumerate(BHUBANESWAR_AREAS):
        bins.append({
            "id": i,
            "location": (
                area["lat"] + np.random.uniform(-0.0005, 0.0005),
                area["lon"] + np.random.uniform(-0.0005, 0.0005)
            ),
            "ward_name": area["name"],
            "type": area["type"],          # ✅ REQUIRED BY PREDICTOR
            "capacity": 1000,
            "historical_avg": np.random.uniform(50, 200)
        })

    return bins


BINS = generate_bins()
DEPOT = {"lat": 20.2961, "lon": 85.8245, "name": "BMC Central Depot"}

# --------------------------------------------------
# Pages
# --------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        data = request.get_json()
        date_str = data.get("date") or datetime.now().isoformat()
        target_date = datetime.fromisoformat(date_str)

        bins_info = {b["id"]: b for b in BINS}
        predictions = predictor.predict_for_bins(bins_info, target_date)

        high_priority = 0
        for b in BINS:
            b["predicted_waste"] = predictions[b["id"]]
            if b["predicted_waste"] > b["capacity"] * 0.7:
                high_priority += 1

        total = sum(predictions.values())

        return jsonify({
            "success": True,
            "date": target_date.strftime("%Y-%m-%d"),
            "total_waste": round(total, 2),
            "avg_waste": round(total / len(BINS), 2),
            "bin_count": len(BINS),  # ✅ FIXED
            "bins_needing_collection": high_priority,
            "predictions": {
                str(k): round(v, 2) for k, v in predictions.items()
            },
            "bins": BINS
        })

    return render_template("prediction.html", bins=BINS)

@app.route("/optimize", methods=["GET", "POST"])
def optimize():
    if request.method == "GET":
        return render_template("optimization.html", bins=BINS, depot=DEPOT)

    # POST logic (already fixed earlier)
    try:
        data = request.get_json()
        algorithm = data.get("algorithm", "genetic")

        if "predicted_waste" not in BINS[0]:
            bins_info = {b["id"]: b for b in BINS}
            preds = predictor.predict_for_bins(bins_info, datetime.now())
            for b in BINS:
                b["predicted_waste"] = preds.get(b["id"], 0)

        optimizer = RouteOptimizer(
            BINS,
            (DEPOT["lat"], DEPOT["lon"]),
            Config.TRUCK_CAPACITY
        )

        bins_to_collect = sorted(
            range(len(BINS)),
            key=lambda i: BINS[i]["predicted_waste"],
            reverse=True
        )[:5]

        algo = GeneticAlgorithm(
            optimizer.calculate_route_distance,
            len(bins_to_collect),
            **Config.GENETIC_ALGORITHM
        )

        subset, _, _ = algo.optimize()
        best_route = [bins_to_collect[i] for i in subset]

        routes = optimizer.create_routes(best_route)
        optimized = optimizer._aggregate_route_metrics(routes)
        optimized["num_routes"] = len(routes)

        fixed_routes = optimizer.create_routes(bins_to_collect)
        fixed = optimizer._aggregate_route_metrics(fixed_routes)
        fixed["num_routes"] = len(fixed_routes)

        return jsonify({
            "success": True,
            "optimized": optimized,
            "fixed": fixed,
            "routes": [[BINS[i] for i in r] for r in routes],
            "depot": DEPOT
        })

    except Exception as e:
        print("❌ Optimize error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# --------------------------------------------------
# Comparison Page
# --------------------------------------------------
@app.route("/comparison")
def comparison():
    return render_template("comparison.html")

@app.route('/api/compare_algorithms', methods=['POST'])
def compare_algorithms():
    try:
        # Ensure predictions exist
        if 'predicted_waste' not in BINS[0]:
            bins_info = {b['id']: b for b in BINS}
            predictions = predictor.predict_for_bins(bins_info, datetime.now())
            for b in BINS:
                b['predicted_waste'] = predictions.get(b['id'], 0)

        # Demo-safe bin selection
        bins_to_collect = [
            i for i, b in enumerate(BINS)
            if b['predicted_waste'] > b['capacity'] * 0.4
        ]
        if not bins_to_collect:
            bins_to_collect = sorted(
                range(len(BINS)),
                key=lambda i: BINS[i]['predicted_waste'],
                reverse=True
            )[:5]

        optimizer = RouteOptimizer(
            BINS,
            (DEPOT['lat'], DEPOT['lon']),
            truck_capacity=Config.TRUCK_CAPACITY
        )

        results = {}

        # ---------------- FIXED ROUTE (BASELINE) ----------------
        fixed_routes = optimizer.create_routes(bins_to_collect)
        fixed_metrics = optimizer._aggregate_route_metrics(fixed_routes)
        fixed_metrics['num_routes'] = len(fixed_routes)
        results['Fixed Route'] = fixed_metrics

        # ---------------- NEAREST NEIGHBOR ----------------
        nn = NearestNeighbor(
            optimizer.calculate_route_distance,
            len(bins_to_collect),
            optimizer.distance_matrix
        )
        nn_idx, _, _ = nn.optimize()
        nn_route = [bins_to_collect[i] for i in nn_idx]
        nn_routes = optimizer.create_routes(nn_route)
        nn_metrics = optimizer._aggregate_route_metrics(nn_routes)
        nn_metrics['num_routes'] = len(nn_routes)
        results['Nearest Neighbor'] = nn_metrics

        # ---------------- GENETIC ALGORITHM ----------------
        ga = GeneticAlgorithm(
            optimizer.calculate_route_distance,
            len(bins_to_collect),
            **Config.GENETIC_ALGORITHM
        )
        ga_idx, _, _ = ga.optimize()
        ga_route = [bins_to_collect[i] for i in ga_idx]
        ga_routes = optimizer.create_routes(ga_route)
        ga_metrics = optimizer._aggregate_route_metrics(ga_routes)
        ga_metrics['num_routes'] = len(ga_routes)
        results['Genetic Algorithm'] = ga_metrics

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        print("Comparison error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_sample_bins():
    """Generate sample waste bin locations in Bhubaneswar areas (demo-optimized)"""
    np.random.seed(42)
    bins = []

    for i, area in enumerate(BHUBANESWAR_AREAS):
        # Create realistic waste variance by area type
        if area['type'] == 'commercial':
            base = np.random.uniform(700, 950)      # High waste
        elif area['type'] == 'industrial':
            base = np.random.uniform(500, 800)      # Medium-high waste
        else:
            base = np.random.uniform(150, 450)      # Residential

        bins.append({
            'id': i,
            'location': (
                area['lat'] + np.random.uniform(-0.0005, 0.0005),
                area['lon'] + np.random.uniform(-0.0005, 0.0005)
            ),
            'ward_name': area['name'],
            'type': area['type'],                   # REQUIRED by predictor
            'capacity': 1000,
            'historical_avg': base,
            'address': f"{area['name']}, Bhubaneswar"
        })

    return bins



# ============================================
# SMART DUSTBIN IoT ENDPOINTS
# ============================================

@app.route('/api/iot/bin/update', methods=['POST'])
def receive_iot_data():
    """
    Receive data from Smart Dustbin IoT device
    
    Expected payload from ESP32:
    {
        "bin_id": "BIN_001",
        "fill_level": 78.5,
        "weight_kg": 42.3,
        "temperature": 28.5,
        "humidity": 65.2,
        "battery_level": 87,
        "gps_lat": 40.7128,
        "gps_lon": -74.0060
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bin_id', 'fill_level', 'weight_kg']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        bin_id = data['bin_id']
        
        # Find or create bin
        bin_obj = Bin.query.filter_by(bin_id=bin_id).first()
        
        if not bin_obj:
            bin_obj = Bin(
                bin_id=bin_id,
                latitude=data.get('gps_lat', 0),
                longitude=data.get('gps_lon', 0),
                capacity=100.0,
                area='IoT-Auto',
                is_active=True
            )
            db.session.add(bin_obj)
        
        # Update bin data
        bin_obj.current_fill_level = float(data['fill_level'])
        bin_obj.updated_at = datetime.utcnow()
        
        # Update GPS if provided
        if 'gps_lat' in data and 'gps_lon' in data:
            bin_obj.latitude = data['gps_lat']
            bin_obj.longitude = data['gps_lon']
        
        # Create reading record
        reading = BinReading(
            bin_id=bin_id,
            fill_level=data['fill_level'],
            temperature=data.get('temperature'),
            timestamp=datetime.utcnow()
        )
        db.session.add(reading)
        
        # Check for alerts
        alerts = []
        
        # Critical fill level (>90%)
        if data['fill_level'] >= 90:
            alerts.append({
                'type': 'CRITICAL_FILL',
                'message': f'{bin_id} is {data["fill_level"]:.1f}% full - Urgent!',
                'priority': 'critical'
            })
        # High fill level (>70%)
        elif data['fill_level'] >= 70:
            alerts.append({
                'type': 'HIGH_FILL',
                'message': f'{bin_id} is {data["fill_level"]:.1f}% full',
                'priority': 'high'
            })
        
        # Fire risk (>60°C)
        if data.get('temperature', 0) > 60:
            alerts.append({
                'type': 'FIRE_RISK',
                'message': f'{bin_id} temperature: {data["temperature"]}°C',
                'priority': 'critical'
            })
        
        # Low battery (<20%)
        if data.get('battery_level', 100) < 20:
            alerts.append({
                'type': 'LOW_BATTERY',
                'message': f'{bin_id} battery: {data["battery_level"]}%',
                'priority': 'medium'
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data received successfully',
            'bin_status': bin_obj.get_status(),
            'alerts': alerts,
            'should_collect': bin_obj.current_fill_level >= 70
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"IoT data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/iot/bins/all-status', methods=['GET'])
def get_all_bins_status():
    """Get real-time status of all bins"""
    try:
        bins = Bin.query.filter_by(is_active=True).all()
        
        bins_status = []
        for bin_obj in bins:
            bins_status.append({
                'bin_id': bin_obj.bin_id,
                'latitude': bin_obj.latitude,
                'longitude': bin_obj.longitude,
                'fill_level': bin_obj.current_fill_level,
                'status': bin_obj.get_status(),
                'area': bin_obj.area,
                'last_update': bin_obj.updated_at.isoformat() if bin_obj.updated_at else None
            })
        
        # Summary stats
        status_summary = {
            'critical': len([b for b in bins if b.current_fill_level >= 90]),
            'needs_collection': len([b for b in bins if 70 <= b.current_fill_level < 90]),
            'moderate': len([b for b in bins if 50 <= b.current_fill_level < 70]),
            'good': len([b for b in bins if b.current_fill_level < 50])
        }
        
        return jsonify({
            'success': True,
            'bins': bins_status,
            'summary': status_summary,
            'total_bins': len(bins),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/iot/bin/simulate-fill', methods=['POST'])
def simulate_bin_fill():
    """Simulate bins filling up"""
    try:
        data = request.get_json()
        increase = data.get('increase', 10)
        
        bins = Bin.query.filter_by(is_active=True).all()
        
        for bin_obj in bins:
            new_level = min(100, bin_obj.current_fill_level + increase)
            bin_obj.current_fill_level = new_level
            
            reading = BinReading(
                bin_id=bin_obj.bin_id,
                fill_level=new_level,
                temperature=25.0,
                timestamp=datetime.utcnow()
            )
            db.session.add(reading)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'bins_updated': len(bins)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/live-stats', methods=['GET'])
def get_live_stats():
    """Enhanced real-time stats for dashboard"""
    try:
        total_bins = Bin.query.filter_by(is_active=True).count()
        bins_critical = Bin.query.filter(
            Bin.is_active == True,
            Bin.current_fill_level >= 90
        ).count()
        bins_need_collection = Bin.query.filter(
            Bin.is_active == True,
            Bin.current_fill_level >= 70
        ).count()
        
        # Recent collections
        today = datetime.utcnow().replace(hour=0, minute=0, second=0)
        recent_collections = Collection.query.filter(
            Collection.collection_time >= today
        ).order_by(Collection.collection_time.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_bins': total_bins,
                'bins_critical': bins_critical,
                'bins_need_collection': bins_need_collection,
                'bins_ok': total_bins - bins_need_collection
            },
            'recent_collections': [
                {
                    'bin_id': c.bin_id,
                    'time': c.collection_time.isoformat(),
                    'amount': c.waste_collected
                } for c in recent_collections
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route("/smart-bin")
def smart_bin():
    return render_template("smart_bin.html")

# --------------------------------------------------
# Smart Dustbin IoT API
# --------------------------------------------------
@app.route("/api/smart-bin/update", methods=["POST"])
def smart_bin_update():
    data = request.get_json()

    bin_id = data.get("bin_id", 1)
    fill_level = float(data.get("fill_level", 0))
    weight = float(data.get("weight", 0))
    temperature = float(data.get("temperature", 0))

    # Save reading to database
    reading = BinReading(
        bin_id=bin_id,
        fill_level=fill_level,
        weight_kg=weight,
        temperature=temperature
    )

    db.session.add(reading)
    db.session.commit()

    # Alerts (for demo & jury)
    alert = "OK"
    if temperature > 45:
        alert = "🔥 Fire Risk"
    elif fill_level > 80:
        alert = "⚠️ Bin Almost Full"

    return jsonify({
        "success": True,
        "message": "Smart bin data received",
        "alert": alert
    })

@app.route("/api/smart-bin/live", methods=["GET"])
def smart_bin_live():
    bins = Bin.query.all()

    data = []
    for b in bins:
        # Decide status
        if b.current_fill_level >= 90:
            status = "FULL"
        elif b.current_fill_level >= 70:
            status = "ALERT"
        else:
            status = "OK"

        data.append({
            "bin_id": b.bin_id,
            "weight": round(b.current_fill_level * 0.5, 2),  # demo logic
            "fill_level": round(b.current_fill_level, 2),
            "temperature": round(getattr(b, "temperature", 25), 1),
            "updated_at": b.updated_at.strftime("%H:%M:%S") if b.updated_at else "-",
            "status": status
        })

    return jsonify({"bins": data})


@app.route("/roi-calculator")
def roi_calculator():
    """ROI Calculator with React component"""
    return render_template("roi_calculator.html")

@app.route("/live-tracking")
def live_tracking():
    """Real-time route tracking page"""
    return render_template("live_route_tracking.html")

@app.route("/predictive-maintenance")
def predictive_maintenance():
    """AI Predictive Maintenance Dashboard"""
    return render_template("predictive_maintenance.html")

@app.route("/citizen-portal")
def citizen_portal():
    """Citizen Complaint & Feedback System"""
    return render_template("citizen_portal.html")






from flask import jsonify

@app.route("/api/predictive/trucks")
def api_predictive_trucks():
    """
    Static truck list for hackathon demo
    (DB integration is modular & can be enabled later)
    """
    return jsonify([
        {"truck_id": "BMC-TRUCK-01"},
        {"truck_id": "BMC-TRUCK-02"},
        {"truck_id": "BMC-TRUCK-03"},
        {"truck_id": "BMC-TRUCK-04"},
        {"truck_id": "BMC-TRUCK-05"}
    ])

@app.route("/api/predictive/analyze/<truck_id>")
def api_predictive_analyze(truck_id):
    # Simulated ML output (jury-safe)
    data = {
        "overall_health": 82,
        "status": "Healthy",
        "mileage": 45280,
        "last_service_days": 30,
        "components": {
            "engine": {"health": 85},
            "brakes": {"health": 72},
            "tires": {"health": 68},
            "transmission": {"health": 90},
            "suspension": {"health": 78},
            "hydraulics": {"health": 82}
        },
        "recommendations": [
            {"component": "Brakes", "days": 18, "cost": 4200},
            {"component": "Tires", "days": 25, "cost": 6500}
        ],
        "savings": {
            "monthly": 18000,
            "yearly": 216000,
            "hours": 64
        }
    }
    return jsonify(data)


# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    print("\n🗑️ Smart Waste Optimization System – Bhubaneswar")
    print(f"Bins: {len(BINS)} | Depot: {DEPOT['name']}")
    app.run(debug=True, host="0.0.0.0", port=5000)
