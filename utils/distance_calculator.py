import math

class DistanceCalculator:
    def __init__(self):
        self.EARTH_RADIUS_KM = 6371.0
        
    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_KM * c
    
    def manhattan_distance(self, lat1, lon1, lat2, lon2):
        """Calculate Manhattan distance (approximation)"""
        return abs(lat2 - lat1) + abs(lon2 - lon1)