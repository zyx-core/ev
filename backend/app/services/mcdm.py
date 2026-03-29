import math
from typing import List, Tuple
from ..models import ChargingStation, ConnectorStatus


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in kilometers
    r = 6371
    
    return c * r


def normalize_value(value: float, min_val: float, max_val: float, inverse: bool = False) -> float:
    """
    Normalize a value to [0, 1] range
    
    Args:
        value: Value to normalize
        min_val: Minimum value in dataset
        max_val: Maximum value in dataset
        inverse: If True, lower values get higher scores (for distance, price)
    
    Returns:
        Normalized score between 0 and 1
    """
    if max_val == min_val:
        return 1.0
    
    normalized = (value - min_val) / (max_val - min_val)
    
    if inverse:
        normalized = 1.0 - normalized
    
    return max(0.0, min(1.0, normalized))


def calculate_availability_score(station: ChargingStation) -> float:
    """
    Calculate availability score based on connector status
    
    Args:
        station: ChargingStation model
    
    Returns:
        Availability score between 0 and 1
    """
    if not station.connectors:
        return 0.0
    
    available_count = sum(
        1 for c in station.connectors 
        if c.status == ConnectorStatus.AVAILABLE
    )
    
    return available_count / len(station.connectors)


def calculate_speed_score(station: ChargingStation) -> float:
    """
    Calculate charging speed score based on max power
    
    Args:
        station: ChargingStation model
    
    Returns:
        Speed score (max power in kW)
    """
    if not station.connectors:
        return 0.0
    
    return max(c.power_kw for c in station.connectors)


class MCDMRecommender:
    """Multi-Criteria Decision Making recommender for charging stations"""
    
    def __init__(
        self,
        distance_weight: float = 0.4,
        price_weight: float = 0.3,
        speed_weight: float = 0.2,
        availability_weight: float = 0.1
    ):
        """
        Initialize MCDM recommender with weights
        
        Args:
            distance_weight: Weight for distance criterion
            price_weight: Weight for price criterion
            speed_weight: Weight for charging speed criterion
            availability_weight: Weight for availability criterion
        """
        self.distance_weight = distance_weight
        self.price_weight = price_weight
        self.speed_weight = speed_weight
        self.availability_weight = availability_weight
    
    def rank_stations(
        self,
        stations: List[ChargingStation],
        user_lat: float,
        user_lon: float,
        connector_type: str = None
    ) -> List[Tuple[ChargingStation, float, float]]:
        """
        Rank stations using MCDM algorithm
        
        Args:
            stations: List of ChargingStation models
            user_lat: User latitude
            user_lon: User longitude
            connector_type: Optional filter for connector type
        
        Returns:
            List of tuples (station, score, distance_km) sorted by score descending
        """
        if not stations:
            return []
        
        # Filter by connector type if specified
        if connector_type:
            stations = [
                s for s in stations
                if any(c.connector_type.value == connector_type for c in s.connectors)
            ]
        
        if not stations:
            return []
        
        # Calculate criteria for all stations
        station_data = []
        for station in stations:
            distance = haversine_distance(user_lat, user_lon, station.latitude, station.longitude)
            price = station.base_rate * station.dynamic_multiplier
            speed = calculate_speed_score(station)
            availability = calculate_availability_score(station)
            
            station_data.append({
                'station': station,
                'distance': distance,
                'price': price,
                'speed': speed,
                'availability': availability
            })
        
        # Find min/max for normalization
        distances = [d['distance'] for d in station_data]
        prices = [d['price'] for d in station_data]
        speeds = [d['speed'] for d in station_data]
        
        min_distance, max_distance = min(distances), max(distances)
        min_price, max_price = min(prices), max(prices)
        min_speed, max_speed = min(speeds), max(speeds)
        
        # Calculate weighted scores
        results = []
        for data in station_data:
            # Normalize criteria (inverse for distance and price - lower is better)
            distance_score = normalize_value(data['distance'], min_distance, max_distance, inverse=True)
            price_score = normalize_value(data['price'], min_price, max_price, inverse=True)
            speed_score = normalize_value(data['speed'], min_speed, max_speed, inverse=False)
            availability_score = data['availability']  # Already 0-1
            
            # Calculate weighted sum
            total_score = (
                self.distance_weight * distance_score +
                self.price_weight * price_score +
                self.speed_weight * speed_score +
                self.availability_weight * availability_score
            )
            
            results.append((data['station'], total_score, data['distance']))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
