import numpy as np
from typing import List, Dict
import sys
import os

# Ensure root directory is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.distance_calculator import DistanceCalculator


class RouteOptimizer:
    def __init__(self, bins: List[Dict], depot: Dict, truck_capacity: int = 4000):
        """
        bins: List of dicts with keys:
              - location: (lat, lon)
              - predicted_waste: float (kg)
        depot: dict or tuple -> {'lat': x, 'lon': y} OR (lat, lon)
        """
        self.bins = bins

        if isinstance(depot, dict):
            self.depot_coords = (depot["lat"], depot["lon"])
        else:
            self.depot_coords = depot

        self.truck_capacity = truck_capacity
        self.distance_calc = DistanceCalculator()
        self.distance_matrix = self._create_distance_matrix()

    # --------------------------------------------------
    # Distance Matrix
    # --------------------------------------------------
    def _create_distance_matrix(self):
        """Index 0 = Depot, Index 1+ = Bins"""
        locations = [self.depot_coords] + [b["location"] for b in self.bins]
        n = len(locations)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = self.distance_calc.haversine(
                    locations[i][0], locations[i][1],
                    locations[j][0], locations[j][1]
                )
                matrix[i][j] = matrix[j][i] = dist

        return matrix

    # --------------------------------------------------
    # Distance Calculation
    # --------------------------------------------------
    def calculate_route_distance(self, route_indices: List[int]) -> float:
        """Distance for one route (bin indices only)"""
        if not route_indices:
            return 0.0

        total_distance = 0.0
        current_idx = 0  # Depot

        for idx in route_indices:
            matrix_idx = idx + 1
            total_distance += self.distance_matrix[current_idx][matrix_idx]
            current_idx = matrix_idx

        # Return to depot
        total_distance += self.distance_matrix[current_idx][0]
        return total_distance

    # --------------------------------------------------
    # Route Metrics
    # --------------------------------------------------
    def calculate_route_metrics(self, route: List[int]) -> Dict:
        distance = self.calculate_route_distance(route)
        total_waste = sum(self.bins[i].get("predicted_waste", 0) for i in route)

        # Bhubaneswar assumptions
        travel_time = distance / 25              # km/h
        service_time = len(route) * (8 / 60)      # 8 minutes per bin
        total_time = travel_time + service_time

        fuel_liters = distance * 0.40
        fuel_cost = fuel_liters * 95              # INR
        driver_cost = total_time * 200
        total_cost = fuel_cost + driver_cost

        co2_kg = fuel_liters * 2.68

        return {
            "distance_km": round(distance, 2),
            "time_hours": round(total_time, 2),
            "waste_kg": round(total_waste, 2),
            "fuel_liters": round(fuel_liters, 2),
            "total_cost": round(total_cost, 2),
            "co2_kg": round(co2_kg, 2),
            "bins_visited": len(route)
        }

    # --------------------------------------------------
    # Capacity-Based Route Splitting
    # --------------------------------------------------
    def create_routes(self, sequence: List[int]) -> List[List[int]]:
        routes = []
        current_route = []
        current_load = 0

        for idx in sequence:
            waste = self.bins[idx].get("predicted_waste", 0)

            if current_load + waste > self.truck_capacity:
                if current_route:
                    routes.append(current_route)
                current_route = [idx]
                current_load = waste
            else:
                current_route.append(idx)
                current_load += waste

        if current_route:
            routes.append(current_route)

        return routes

    # --------------------------------------------------
    # Aggregate Metrics
    # --------------------------------------------------
    def _aggregate_route_metrics(self, routes: List[List[int]]) -> Dict:
        summary = {
            "distance_km": 0,
            "time_hours": 0,
            "waste_kg": 0,
            "fuel_liters": 0,
            "total_cost": 0,
            "co2_kg": 0,
            "bins_visited": 0,
            "num_routes": len(routes)
        }

        for r in routes:
            metrics = self.calculate_route_metrics(r)
            for key in metrics:
                summary[key] += metrics[key]

        return {k: round(v, 2) for k, v in summary.items()}

    # --------------------------------------------------
    # FIXED / TRADITIONAL ROUTE (Baseline)
    # --------------------------------------------------
    def optimize_fixed_route(self) -> Dict:
        """
        Traditional waste collection (no AI optimization)
        """
        fixed_sequence = list(range(len(self.bins)))
        routes = self.create_routes(fixed_sequence)
        summary = self._aggregate_route_metrics(routes)

        return {
            "strategy": "Fixed Route (Traditional)",
            "routes": routes,
            "metrics": summary
        }

    # --------------------------------------------------
    # SIMPLE AI / HEURISTIC OPTIMIZED ROUTE
    # --------------------------------------------------
    def optimize_ai_route(self) -> Dict:
        """
        AI-inspired heuristic:
        Visit bins in descending order of predicted waste
        """
        optimized_sequence = sorted(
            range(len(self.bins)),
            key=lambda i: self.bins[i].get("predicted_waste", 0),
            reverse=True
        )

        routes = self.create_routes(optimized_sequence)
        summary = self._aggregate_route_metrics(routes)

        return {
            "strategy": "AI Optimized Route",
            "routes": routes,
            "metrics": summary
        }
