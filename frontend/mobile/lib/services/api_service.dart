import 'dart:convert';
import 'package:http/http.dart' as http;

/// API configuration
class ApiConfig {
  // Change this to your backend URL
  // For Android emulator use: 10.0.2.2:8000
  // For physical device use your computer's IP address
  // For web/desktop use: localhost:8000
  static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
}

/// Location model
class Location {
  final double latitude;
  final double longitude;

  Location({required this.latitude, required this.longitude});

  factory Location.fromJson(Map<String, dynamic> json) {
    return Location(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'latitude': latitude,
    'longitude': longitude,
  };
}

/// Connector model
class Connector {
  final String id;
  final String connectorType;
  final double powerKw;
  final String status;

  Connector({
    required this.id,
    required this.connectorType,
    required this.powerKw,
    required this.status,
  });

  factory Connector.fromJson(Map<String, dynamic> json) {
    return Connector(
      id: json['id'],
      connectorType: json['connector_type'],
      powerKw: (json['power_kw'] as num).toDouble(),
      status: json['status'],
    );
  }

  bool get isAvailable => status == 'available';
}

/// Pricing model
class Pricing {
  final double baseRate;
  final double dynamicMultiplier;
  final double effectiveRate;

  Pricing({
    required this.baseRate,
    required this.dynamicMultiplier,
    required this.effectiveRate,
  });

  factory Pricing.fromJson(Map<String, dynamic> json) {
    return Pricing(
      baseRate: (json['base_rate'] as num).toDouble(),
      dynamicMultiplier: (json['dynamic_multiplier'] as num).toDouble(),
      effectiveRate: (json['effective_rate'] as num).toDouble(),
    );
  }
}

/// Charging Station model
class ChargingStation {
  final String id;
  final String name;
  final Location location;
  final String operatorId;
  final Pricing pricing;
  final List<Connector> connectors;
  final bool isActive;
  final String? blockchainAddress;

  ChargingStation({
    required this.id,
    required this.name,
    required this.location,
    required this.operatorId,
    required this.pricing,
    required this.connectors,
    required this.isActive,
    this.blockchainAddress,
  });

  factory ChargingStation.fromJson(Map<String, dynamic> json) {
    return ChargingStation(
      id: json['id'],
      name: json['name'],
      location: Location.fromJson(json['location']),
      operatorId: json['operator_id'],
      pricing: Pricing.fromJson(json['pricing']),
      connectors: (json['connectors'] as List)
          .map((c) => Connector.fromJson(c))
          .toList(),
      isActive: json['is_active'],
      blockchainAddress: json['blockchain_address'],
    );
  }

  int get availableConnectors =>
      connectors.where((c) => c.isAvailable).length;

  double get maxPower =>
      connectors.map((c) => c.powerKw).reduce((a, b) => a > b ? a : b);

  List<String> get connectorTypes =>
      connectors.map((c) => c.connectorType).toSet().toList();
}

/// Ranked Station model (for recommendations)
class RankedStation {
  final ChargingStation station;
  final double score;
  final double distanceKm;
  final int estimatedWaitMinutes;

  RankedStation({
    required this.station,
    required this.score,
    required this.distanceKm,
    required this.estimatedWaitMinutes,
  });

  factory RankedStation.fromJson(Map<String, dynamic> json) {
    return RankedStation(
      station: ChargingStation.fromJson(json['station']),
      score: (json['score'] as num).toDouble(),
      distanceKm: (json['distance_km'] as num).toDouble(),
      estimatedWaitMinutes: json['estimated_wait_minutes'],
    );
  }
}

/// API Service for backend communication
class ApiService {
  final http.Client _client = http.Client();

  /// Get all charging stations
  Future<List<ChargingStation>> getStations({
    double? lat,
    double? lon,
    double? radiusKm,
    String? connectorType,
  }) async {
    var uri = Uri.parse('${ApiConfig.baseUrl}/stations/');
    
    final params = <String, String>{};
    if (lat != null) params['lat'] = lat.toString();
    if (lon != null) params['lon'] = lon.toString();
    if (radiusKm != null) params['radius_km'] = radiusKm.toString();
    if (connectorType != null) params['connector_type'] = connectorType;
    
    if (params.isNotEmpty) {
      uri = uri.replace(queryParameters: params);
    }

    final response = await _client.get(uri);
    
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((s) => ChargingStation.fromJson(s)).toList();
    } else {
      throw Exception('Failed to load stations: ${response.statusCode}');
    }
  }

  /// Get station by ID
  Future<ChargingStation> getStation(String id) async {
    final response = await _client.get(
      Uri.parse('${ApiConfig.baseUrl}/stations/$id'),
    );
    
    if (response.statusCode == 200) {
      return ChargingStation.fromJson(json.decode(response.body));
    } else {
      throw Exception('Station not found');
    }
  }

  /// Get personalized recommendations
  Future<List<RankedStation>> getRecommendations({
    required double lat,
    required double lon,
    double batterySoc = 50.0,
    double maxDistanceKm = 50.0,
    String? connectorType,
    double distanceWeight = 0.4,
    double priceWeight = 0.3,
    double speedWeight = 0.2,
    double availabilityWeight = 0.1,
  }) async {
    final body = {
      'user_location': {'latitude': lat, 'longitude': lon},
      'battery_soc': batterySoc,
      'max_distance_km': maxDistanceKm,
      'preferences': {
        'distance_weight': distanceWeight,
        'price_weight': priceWeight,
        'speed_weight': speedWeight,
        'availability_weight': availabilityWeight,
      },
    };

    if (connectorType != null) {
      body['connector_type'] = connectorType;
    }

    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}/stations/recommend'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['stations'] as List)
          .map((s) => RankedStation.fromJson(s))
          .toList();
    } else {
      throw Exception('Failed to get recommendations: ${response.statusCode}');
    }
  }

  /// Create a reservation
  Future<Reservation> createReservation({
    required String stationId,
    required String userEmail,
    String? userName,
    DateTime? scheduledStart,
  }) async {
    final body = {
      'station_id': stationId,
      'user_email': userEmail,
    };
    if (userName != null) body['user_name'] = userName;
    if (scheduledStart != null) body['scheduled_start'] = scheduledStart.toIso8601String();

    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}/reservations/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );

    if (response.statusCode == 200) {
      return Reservation.fromJson(json.decode(response.body));
    } else {
      final error = json.decode(response.body);
      throw Exception(error['detail'] ?? 'Failed to create reservation');
    }
  }

  /// Get reservation details
  Future<Reservation> getReservation(String id) async {
    final response = await _client.get(
      Uri.parse('${ApiConfig.baseUrl}/reservations/$id'),
    );

    if (response.statusCode == 200) {
      return Reservation.fromJson(json.decode(response.body));
    } else {
      throw Exception('Reservation not found');
    }
  }

  /// Cancel a reservation
  Future<void> cancelReservation(String id) async {
    final response = await _client.delete(
      Uri.parse('${ApiConfig.baseUrl}/reservations/$id'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to cancel reservation');
    }
  }

  /// Start a charging session
  Future<ChargingSession> startSession(String reservationId) async {
    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}/sessions/start'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'reservation_id': reservationId}),
    );

    if (response.statusCode == 200) {
      return ChargingSession.fromJson(json.decode(response.body));
    } else {
      final error = json.decode(response.body);
      throw Exception(error['detail'] ?? 'Failed to start session');
    }
  }

  /// End a charging session
  Future<ChargingSession> endSession(String sessionId, double energyDelivered) async {
    final response = await _client.post(
      Uri.parse('${ApiConfig.baseUrl}/sessions/$sessionId/end'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'energy_delivered_kwh': energyDelivered}),
    );

    if (response.statusCode == 200) {
      return ChargingSession.fromJson(json.decode(response.body));
    } else {
      final error = json.decode(response.body);
      throw Exception(error['detail'] ?? 'Failed to end session');
    }
  }

  /// Get session details
  Future<ChargingSession> getSession(String id) async {
    final response = await _client.get(
      Uri.parse('${ApiConfig.baseUrl}/sessions/$id'),
    );

    if (response.statusCode == 200) {
      return ChargingSession.fromJson(json.decode(response.body));
    } else {
      throw Exception('Session not found');
    }
  }

  void dispose() {
    _client.close();
  }
}

/// Reservation model
class Reservation {
  final String id;
  final String stationId;
  final String? connectorId;
  final String userId;
  final String status;
  final double escrowAmount;
  final DateTime? startTime;
  final DateTime? endTime;
  final DateTime createdAt;

  Reservation({
    required this.id,
    required this.stationId,
    this.connectorId,
    required this.userId,
    required this.status,
    required this.escrowAmount,
    this.startTime,
    this.endTime,
    required this.createdAt,
  });

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json['id'],
      stationId: json['station_id'],
      connectorId: json['connector_id'],
      userId: json['user_id'],
      status: json['status'],
      escrowAmount: (json['escrow_amount'] as num).toDouble(),
      startTime: json['start_time'] != null ? DateTime.parse(json['start_time']) : null,
      endTime: json['end_time'] != null ? DateTime.parse(json['end_time']) : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  bool get isActive => status == 'reserved' || status == 'active';
  bool get canStart => status == 'reserved';
  bool get isCharging => status == 'active';
}

/// Charging Session model
class ChargingSession {
  final String id;
  final String stationId;
  final String? connectorId;
  final String userId;
  final String status;
  final DateTime? startTime;
  final DateTime? endTime;
  final double? energyDeliveredKwh;
  final double? cost;

  ChargingSession({
    required this.id,
    required this.stationId,
    this.connectorId,
    required this.userId,
    required this.status,
    this.startTime,
    this.endTime,
    this.energyDeliveredKwh,
    this.cost,
  });

  factory ChargingSession.fromJson(Map<String, dynamic> json) {
    return ChargingSession(
      id: json['id'],
      stationId: json['station_id'],
      connectorId: json['connector_id'],
      userId: json['user_id'],
      status: json['status'],
      startTime: json['start_time'] != null ? DateTime.parse(json['start_time']) : null,
      endTime: json['end_time'] != null ? DateTime.parse(json['end_time']) : null,
      energyDeliveredKwh: json['energy_delivered_kwh'] != null 
          ? (json['energy_delivered_kwh'] as num).toDouble() 
          : null,
      cost: json['cost'] != null ? (json['cost'] as num).toDouble() : null,
    );
  }

  bool get isActive => status == 'active';
  bool get isCompleted => status == 'completed';

  Duration? get chargingDuration {
    if (startTime == null) return null;
    final end = endTime ?? DateTime.now();
    return end.difference(startTime!);
  }
}
